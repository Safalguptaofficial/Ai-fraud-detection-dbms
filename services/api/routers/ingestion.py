"""
Data Ingestion Router
Handles CSV uploads, real-time transaction API, and database connectors
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import io
import logging

from ingestion.csv_ingestor import CSVIngestor
from ingestion.realtime_api import RealtimeTransactionAPI, TransactionCreate
from ingestion.db_connectors import PostgreSQLConnector, MySQLConnector, DataSyncScheduler
from middleware import get_current_tenant, get_current_user_id
from deps import get_postgres, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["data-ingestion"])


# ============================================================================
# CSV/Excel Upload Endpoints
# ============================================================================

@router.post("/files")
async def upload_file(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant),
    request: Request,
    db=Depends(get_postgres),
    redis_client=Depends(get_redis)
):
    """
    📤 Upload CSV or Excel file
    
    Bulk upload historical transaction data
    Note: user_id is optional when using API key authentication
    """
    try:
        logger.info(f"File upload request received: filename={file.filename}, tenant_id={tenant_id}")
        
        # Try to get user_id from request scope, otherwise use None (API key auth)
        # When using API key authentication, user_id can be None
        user_id = None
        if request:
            try:
                user_id = request.scope.get('user_id', None)
            except (AttributeError, KeyError, TypeError):
                pass  # user_id remains None if not available
        
        logger.debug(f"Upload context: tenant_id={tenant_id}, user_id={user_id}, filename={file.filename}")
        
        # Read file
        file_content = await file.read()
        file_type = file.filename.split('.')[-1].lower()
        
        logger.info(f"File read: size={len(file_content)} bytes, type={file_type}")
        
        if file_type not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_type}. Supported: csv, xlsx, xls"
            )
        
        # Store file upload record
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO file_uploads (
                tenant_id, uploaded_by, filename, file_type,
                file_size, status
            ) VALUES (%s, %s, %s, %s, %s, 'PROCESSING')
            RETURNING id
        """, (tenant_id, user_id, file.filename, file_type, len(file_content)))
        
        upload_id = cursor.fetchone()[0]
        db.commit()
        
        # Validate and ingest file
        ingestor = CSVIngestor(db)
        result = await ingestor.ingest_file(
            tenant_id=tenant_id,
            file_content=file_content,
            file_type=file_type
        )
        
        # If ingestion failed, return error immediately with proper status code
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown error during file ingestion')
            # Check if it's a validation error (should return 400)
            if 'Missing required columns' in error_msg or 'must be' in error_msg or 'Unsupported file type' in error_msg:
                # Rollback the file_uploads record
                cursor.execute("""
                    UPDATE file_uploads
                    SET status = 'FAILED',
                        error_summary = %s,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (error_msg, upload_id))
                db.commit()
                cursor.close()
                logger.error(f"File upload {upload_id} validation failed: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            else:
                # Other errors (500)
                cursor.execute("""
                    UPDATE file_uploads
                    SET status = 'FAILED',
                        error_summary = %s,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (error_msg, upload_id))
                db.commit()
                cursor.close()
                logger.error(f"File upload {upload_id} ingestion failed: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"File ingestion failed: {error_msg}"
                )
        
        # Clear transactions cache after upload so new data shows immediately
        try:
            if redis_client:
                # Generate cache keys manually (same logic as transactions router)
                def get_cache_key(endpoint: str, **kwargs) -> str:
                    params = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()) if v)
                    return f"api:{endpoint}:{params}" if params else f"api:{endpoint}"
                
                keys_deleted = 0
                
                # Method 1: Clear all transaction cache keys using pattern matching
                try:
                    # Try multiple patterns to catch all variations
                    patterns = [
                        "api:/transactions:*",  # Standard format
                        "*:/transactions:*",     # Any prefix
                        "api:transactions:*",   # Without leading slash
                    ]
                    
                    for pattern in patterns:
                        try:
                            if hasattr(redis_client, 'keys'):
                                keys = redis_client.keys(pattern)
                                if keys:
                                    # Handle both bytes and string keys
                                    keys_list = []
                                    if isinstance(keys, (list, tuple)):
                                        keys_list = [k.decode() if isinstance(k, bytes) else k for k in keys]
                                    else:
                                        keys_list = [k.decode() if isinstance(k, bytes) else k for k in list(keys)]
                                    
                                    if keys_list:
                                        # Delete all keys at once
                                        redis_client.delete(*keys_list)
                                        keys_deleted += len(keys_list)
                                        logger.debug(f"Deleted {len(keys_list)} keys matching pattern {pattern}")
                        except Exception as pattern_err:
                            logger.debug(f"Pattern {pattern} failed: {pattern_err}")
                            continue
                    
                    # Method 2: Clear specific common cache key combinations
                    common_combinations = [
                        # Different limit/offset combinations
                        get_cache_key("/transactions", tenant_id=tenant_id),
                        get_cache_key("/transactions", tenant_id=tenant_id, limit=10),
                        get_cache_key("/transactions", tenant_id=tenant_id, limit=50),
                        get_cache_key("/transactions", tenant_id=tenant_id, limit=100),
                        get_cache_key("/transactions", tenant_id=tenant_id, limit=1000),
                        get_cache_key("/transactions", tenant_id=tenant_id, limit=100, offset=0),
                        get_cache_key("/transactions", tenant_id=tenant_id, limit=100, offset=100),
                        # Without tenant_id (for demo mode)
                        get_cache_key("/transactions"),
                        get_cache_key("/transactions", limit=100),
                        get_cache_key("/transactions", limit=100, offset=0),
                    ]
                    
                    for cache_key in common_combinations:
                        try:
                            result = redis_client.delete(cache_key)
                            if result:
                                keys_deleted += result
                            logger.debug(f"Deleted cache key: {cache_key}")
                        except Exception as key_err:
                            logger.debug(f"Failed to delete key {cache_key}: {key_err}")
                    
                    # Method 3: If tenant_id filtering is used, clear all keys and let them rebuild
                    # This is a more aggressive approach but ensures fresh data
                    try:
                        # Clear all API cache keys if pattern matching didn't work well
                        all_api_keys = redis_client.keys("api:*")
                        if all_api_keys and isinstance(all_api_keys, (list, tuple)):
                            transaction_keys = [k.decode() if isinstance(k, bytes) else k 
                                              for k in all_api_keys 
                                              if '/transactions' in (k.decode() if isinstance(k, bytes) else k)]
                            if transaction_keys:
                                redis_client.delete(*transaction_keys)
                                keys_deleted += len(transaction_keys)
                                logger.info(f"Cleared {len(transaction_keys)} transaction cache keys via bulk delete")
                    except Exception as bulk_err:
                        logger.debug(f"Bulk cache clear failed: {bulk_err}")
                    
                    logger.info(f"Cleared transactions cache after upload for tenant {tenant_id} (deleted {keys_deleted} keys total)")
                except Exception as cache_err:
                    logger.warning(f"Cache clearing encountered errors but continuing: {cache_err}")
        except Exception as e:
            logger.warning(f"Cache clearing skipped: {e}")
        
        # Update file upload status
        if result.get('success'):
            cursor.execute("""
                UPDATE file_uploads
                SET status = 'COMPLETED',
                    rows_total = %s,
                    rows_inserted = %s,
                    rows_failed = %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                result['rows_processed'],
                result['rows_inserted'],
                result['rows_failed'],
                upload_id
            ))
        else:
            cursor.execute("""
                UPDATE file_uploads
                SET status = 'FAILED',
                    error_summary = %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (result.get('error', 'Unknown error'), upload_id))
        
        db.commit()
        cursor.close()
        
        logger.info(f"File upload {upload_id} completed: {result['rows_inserted']} rows")
        
        return {
            "upload_id": upload_id,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/files")
async def list_uploads(
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📋 List file uploads
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                id, filename, file_type, file_size, status,
                rows_total, rows_inserted, rows_failed,
                created_at, completed_at
            FROM file_uploads
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (tenant_id, limit))
        
        columns = [desc[0] for desc in cursor.description]
        uploads = []
        
        for row in cursor.fetchall():
            upload = dict(zip(columns, row))
            uploads.append(upload)
        
        cursor.close()
        
        return {"uploads": uploads}
        
    except Exception as e:
        logger.error(f"Failed to list uploads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list uploads"
        )


@router.get("/files/{upload_id}")
async def get_upload_status(
    upload_id: int,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📊 Get file upload status
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT *
            FROM file_uploads
            WHERE id = %s AND tenant_id = %s
        """, (upload_id, tenant_id))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        columns = [desc[0] for desc in cursor.description]
        upload = dict(zip(columns, result))
        
        return {"upload": upload}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload status"
        )


@router.get("/template")
async def download_template():
    """
    📥 Download CSV template
    
    Returns a CSV template with example data
    """
    try:
        ingestor = CSVIngestor(None)
        template_csv = ingestor.get_template()
        
        # Return as downloadable file
        return StreamingResponse(
            io.StringIO(template_csv),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transaction_template.csv"}
        )
        
    except Exception as e:
        logger.error(f"Failed to generate template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate template"
        )


# ============================================================================
# Real-time Transaction API
# ============================================================================

@router.post("/transactions")
async def ingest_transaction(
    transaction: TransactionCreate,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres),
    redis_client = Depends(get_redis)
):
    """
    ⚡ Ingest single transaction in real-time
    
    Features:
    - ML-based fraud detection
    - Rate limiting per tenant
    - Comprehensive error handling
    - Retry logic for transient failures
    
    Returns fraud score and status
    """
    try:
        api = RealtimeTransactionAPI(db, redis_client)
        
        result = await api.ingest_transaction(tenant_id, transaction)
        
        # Record transaction for usage metering
        try:
            from billing.usage_metering import UsageMetering
            usage = UsageMetering(db, redis_client)
            await usage.record_transaction(tenant_id, result['transaction_id'])
        except Exception as e:
            logger.warning(f"Failed to record transaction for usage metering: {e}")
        
        logger.info(f"Ingested transaction {result['transaction_id']} for tenant {tenant_id}")
        
        return result
        
    except ValueError as e:
        # Rate limit or validation errors
        logger.warning(f"Transaction ingestion rejected: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS if "rate limit" in str(e).lower() 
            else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Transaction ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction ingestion failed: {str(e)}"
        )


@router.post("/transactions/batch")
async def ingest_batch(
    transactions: List[TransactionCreate],
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres),
    redis_client = Depends(get_redis)
):
    """
    ⚡ Ingest multiple transactions at once
    
    Max 100 transactions per batch
    """
    try:
        api = RealtimeTransactionAPI(db, redis_client)
        
        result = await api.ingest_batch(tenant_id, transactions)
        
        logger.info(f"Batch ingested: {result['success']} success, {result['failed']} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ingestion failed: {str(e)}"
        )


# ============================================================================
# Database Connector Endpoints
# ============================================================================

class ConnectorTestRequest(BaseModel):
    connector_type: str  # 'postgresql', 'mysql', 'oracle'
    host: str
    port: int
    database: str
    user: str
    password: str


class ConnectorCreateRequest(BaseModel):
    name: str
    connector_type: str
    connection_params: dict
    source_table: str
    column_mapping: dict
    schedule: str = "0 * * * *"  # Cron expression


@router.post("/connectors/test")
async def test_connector(
    request: ConnectorTestRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    🔍 Test database connection
    
    Verifies connection parameters before creating connector
    """
    try:
        connection_params = {
            'host': request.host,
            'port': request.port,
            'database': request.database,
            'user': request.user,
            'password': request.password
        }
        
        # Create connector
        if request.connector_type == 'postgresql':
            connector = PostgreSQLConnector(connection_params)
        elif request.connector_type == 'mysql':
            connector = MySQLConnector(connection_params)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported connector type: {request.connector_type}"
            )
        
        # Test connection
        result = connector.test_connection()
        
        return result
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/connectors")
async def create_connector(
    request: ConnectorCreateRequest,
    tenant_id: str = Depends(get_current_tenant),
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    🔗 Create database connector
    
    Sets up automated data sync from external database
    """
    try:
        scheduler = DataSyncScheduler(db)
        
        job_id = await scheduler.create_sync_job(
            tenant_id=tenant_id,
            connector_type=request.connector_type,
            connection_params=request.connection_params,
            table_name=request.source_table,
            column_mapping=request.column_mapping,
            schedule=request.schedule
        )
        
        logger.info(f"Created sync job {job_id} for tenant {tenant_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Connector '{request.name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Connector creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connector creation failed: {str(e)}"
        )


@router.get("/connectors")
async def list_connectors(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📋 List database connectors
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                id, name, connector_type, source_table,
                schedule, status, last_sync_at, last_sync_status,
                last_sync_count, total_synced, created_at
            FROM data_sync_jobs
            WHERE tenant_id = %s
            ORDER BY created_at DESC
        """, (tenant_id,))
        
        columns = [desc[0] for desc in cursor.description]
        connectors = []
        
        for row in cursor.fetchall():
            connector = dict(zip(columns, row))
            connectors.append(connector)
        
        cursor.close()
        
        return {"connectors": connectors}
        
    except Exception as e:
        logger.error(f"Failed to list connectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list connectors"
        )


@router.post("/connectors/{job_id}/sync")
async def trigger_sync(
    job_id: int,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    🔄 Manually trigger data sync
    """
    try:
        scheduler = DataSyncScheduler(db)
        
        result = await scheduler.run_sync_job(job_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Sync trigger failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync trigger failed: {str(e)}"
        )


@router.delete("/connectors/{job_id}")
async def delete_connector(
    job_id: int,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    🗑️ Delete database connector
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE data_sync_jobs
            SET status = 'DISABLED'
            WHERE id = %s AND tenant_id = %s
        """, (job_id, tenant_id))
        
        db.commit()
        cursor.close()
        
        logger.info(f"Disabled sync job {job_id} for tenant {tenant_id}")
        
        return {
            "success": True,
            "message": "Connector disabled successfully"
        }
        
    except Exception as e:
        logger.error(f"Connector deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connector deletion failed"
        )

