"""
Database Connectors
Direct connection to customer databases for automatic data sync
"""
import psycopg2
import mysql.connector
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Base database connector"""
    
    def __init__(self, connection_params: Dict):
        self.connection_params = connection_params
        self.connection = None
    
    def connect(self):
        """Establish connection"""
        raise NotImplementedError
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def test_connection(self) -> Dict:
        """Test database connection"""
        try:
            self.connect()
            self.disconnect()
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def fetch_transactions(
        self,
        table_name: str,
        column_mapping: Dict,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch transactions from customer database"""
        raise NotImplementedError


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector"""
    
    def connect(self):
        """Connect to PostgreSQL"""
        self.connection = psycopg2.connect(
            host=self.connection_params.get('host'),
            port=self.connection_params.get('port', 5432),
            database=self.connection_params.get('database'),
            user=self.connection_params.get('user'),
            password=self.connection_params.get('password')
        )
    
    async def fetch_transactions(
        self,
        table_name: str,
        column_mapping: Dict,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch transactions from PostgreSQL
        
        Args:
            table_name: Name of transactions table
            column_mapping: Map of our columns to customer columns
                Example: {'account_id': 'user_id', 'amount': 'total_amount'}
            since: Only fetch transactions after this time
            limit: Maximum number of rows to fetch
        """
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            # Build SELECT query
            select_columns = []
            for our_col, their_col in column_mapping.items():
                select_columns.append(f"{their_col} as {our_col}")
            
            query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
            
            # Add WHERE clause for incremental sync
            params = []
            if since and 'transaction_date' in column_mapping:
                date_col = column_mapping['transaction_date']
                query += f" WHERE {date_col} > %s"
                params.append(since)
            
            query += f" ORDER BY {column_mapping.get('transaction_date', 'id')} DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            transactions = []
            
            for row in cursor.fetchall():
                transactions.append(dict(zip(columns, row)))
            
            logger.info(f"Fetched {len(transactions)} transactions from PostgreSQL")
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to fetch from PostgreSQL: {e}")
            raise
        finally:
            self.disconnect()


class MySQLConnector(DatabaseConnector):
    """MySQL/MariaDB database connector"""
    
    def connect(self):
        """Connect to MySQL"""
        self.connection = mysql.connector.connect(
            host=self.connection_params.get('host'),
            port=self.connection_params.get('port', 3306),
            database=self.connection_params.get('database'),
            user=self.connection_params.get('user'),
            password=self.connection_params.get('password')
        )
    
    async def fetch_transactions(
        self,
        table_name: str,
        column_mapping: Dict,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch transactions from MySQL"""
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            
            # Build SELECT query
            select_columns = []
            for our_col, their_col in column_mapping.items():
                select_columns.append(f"`{their_col}` as `{our_col}`")
            
            query = f"SELECT {', '.join(select_columns)} FROM `{table_name}`"
            
            # Add WHERE clause for incremental sync
            params = []
            if since and 'transaction_date' in column_mapping:
                date_col = column_mapping['transaction_date']
                query += f" WHERE `{date_col}` > %s"
                params.append(since)
            
            query += f" ORDER BY `{column_mapping.get('transaction_date', 'id')}` DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            
            transactions = cursor.fetchall()
            
            logger.info(f"Fetched {len(transactions)} transactions from MySQL")
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to fetch from MySQL: {e}")
            raise
        finally:
            self.disconnect()


class OracleConnector(DatabaseConnector):
    """Oracle database connector"""
    
    def connect(self):
        """Connect to Oracle"""
        import oracledb
        
        self.connection = oracledb.connect(
            user=self.connection_params.get('user'),
            password=self.connection_params.get('password'),
            dsn=f"{self.connection_params.get('host')}:{self.connection_params.get('port', 1521)}/{self.connection_params.get('service_name')}"
        )
    
    async def fetch_transactions(
        self,
        table_name: str,
        column_mapping: Dict,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch transactions from Oracle"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            # Build SELECT query
            select_columns = []
            for our_col, their_col in column_mapping.items():
                select_columns.append(f"{their_col} as {our_col}")
            
            query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
            
            # Add WHERE clause
            params = {}
            if since and 'transaction_date' in column_mapping:
                date_col = column_mapping['transaction_date']
                query += f" WHERE {date_col} > :since"
                params['since'] = since
            
            # Oracle uses ROWNUM for limiting
            query += f" AND ROWNUM <= :limit"
            params['limit'] = limit
            
            cursor.execute(query, params)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            transactions = []
            
            for row in cursor.fetchall():
                transactions.append(dict(zip(columns, row)))
            
            logger.info(f"Fetched {len(transactions)} transactions from Oracle")
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to fetch from Oracle: {e}")
            raise
        finally:
            self.disconnect()


class DataSyncScheduler:
    """Manages scheduled data syncs from customer databases"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def create_sync_job(
        self,
        tenant_id: str,
        connector_type: str,
        connection_params: Dict,
        table_name: str,
        column_mapping: Dict,
        schedule: str = "0 * * * *"  # Every hour
    ) -> int:
        """
        Create a new data sync job
        
        Returns: Job ID
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO data_sync_jobs (
                    tenant_id, connector_type, connection_params,
                    table_name, column_mapping, schedule, status
                ) VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
                RETURNING id
            """, (
                tenant_id,
                connector_type,
                connection_params,
                table_name,
                column_mapping,
                schedule
            ))
            
            job_id = cursor.fetchone()[0]
            self.db.commit()
            
            logger.info(f"Created sync job {job_id} for tenant {tenant_id}")
            
            return job_id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create sync job: {e}")
            raise
        finally:
            cursor.close()
    
    async def run_sync_job(self, job_id: int) -> Dict:
        """Execute a data sync job"""
        cursor = self.db.cursor()
        
        try:
            # Get job details
            cursor.execute("""
                SELECT tenant_id, connector_type, connection_params,
                       table_name, column_mapping, last_sync_at
                FROM data_sync_jobs
                WHERE id = %s AND status = 'ACTIVE'
            """, (job_id,))
            
            result = cursor.fetchone()
            if not result:
                return {"success": False, "error": "Job not found or inactive"}
            
            tenant_id, connector_type, conn_params, table_name, col_mapping, last_sync = result
            
            # Create appropriate connector
            if connector_type == 'postgresql':
                connector = PostgreSQLConnector(conn_params)
            elif connector_type == 'mysql':
                connector = MySQLConnector(conn_params)
            elif connector_type == 'oracle':
                connector = OracleConnector(conn_params)
            else:
                return {"success": False, "error": f"Unknown connector type: {connector_type}"}
            
            # Fetch transactions
            transactions = await connector.fetch_transactions(
                table_name,
                col_mapping,
                since=last_sync
            )
            
            # Insert into our database
            inserted = 0
            for txn in transactions:
                try:
                    cursor.execute("""
                        INSERT INTO transactions (
                            tenant_id, account_id, amount, merchant, txn_time, status
                        ) VALUES (%s, %s, %s, %s, %s, 'COMPLETED')
                    """, (
                        tenant_id,
                        txn.get('account_id'),
                        txn.get('amount'),
                        txn.get('merchant'),
                        txn.get('transaction_date', datetime.utcnow())
                    ))
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert transaction: {e}")
            
            # Update last sync time
            cursor.execute("""
                UPDATE data_sync_jobs
                SET last_sync_at = CURRENT_TIMESTAMP,
                    last_sync_count = %s
                WHERE id = %s
            """, (inserted, job_id))
            
            self.db.commit()
            
            logger.info(f"Sync job {job_id} completed: {inserted} transactions")
            
            return {
                "success": True,
                "transactions_fetched": len(transactions),
                "transactions_inserted": inserted
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Sync job {job_id} failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()

