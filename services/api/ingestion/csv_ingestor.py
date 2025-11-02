"""
CSV File Ingestion
Handles bulk upload of transaction data via CSV/Excel files
"""
import pandas as pd
import io
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVIngestor:
    """Handles CSV/Excel file ingestion"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.required_columns = [
            'account_id', 'amount', 'merchant', 'transaction_date'
        ]
        self.optional_columns = [
            'currency', 'mcc', 'channel', 'city', 'country', 'device_id'
        ]
    
    async def validate_file(self, file_content: bytes, file_type: str = 'csv') -> Dict:
        """
        Validate CSV/Excel file format
        
        Returns validation result
        """
        try:
            # Read file based on type
            if file_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            elif file_type in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                return {"valid": False, "error": f"Unsupported file type: {file_type}"}
            
            # Check required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    "valid": False,
                    "error": f"Missing required columns: {', '.join(missing_columns)}",
                    "required_columns": self.required_columns,
                    "found_columns": list(df.columns)
                }
            
            # Validate data types
            validation_errors = []
            
            # Check amount is numeric
            if not pd.api.types.is_numeric_dtype(df['amount']):
                validation_errors.append("'amount' column must be numeric")
            
            # Check date format
            try:
                pd.to_datetime(df['transaction_date'])
            except:
                validation_errors.append("'transaction_date' must be valid date format")
            
            if validation_errors:
                return {
                    "valid": False,
                    "errors": validation_errors
                }
            
            return {
                "valid": True,
                "row_count": len(df),
                "columns": list(df.columns),
                "sample_rows": df.head(5).to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            return {"valid": False, "error": str(e)}
    
    async def ingest_file(
        self,
        tenant_id: str,
        file_content: bytes,
        file_type: str = 'csv',
        batch_size: int = 1000
    ) -> Dict:
        """
        Ingest CSV/Excel file into database
        
        Returns: Ingestion statistics
        """
        try:
            # Validate first
            validation = await self.validate_file(file_content, file_type)
            if not validation['valid']:
                return validation
            
            # Read file
            if file_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            # Add tenant_id to all rows
            df['tenant_id'] = tenant_id
            logger.info(f"CSV ingestion: Using tenant_id={tenant_id}, rows to process={len(df)}")
            
            # Parse dates
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            # Set defaults for optional columns
            for col in self.optional_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Insert in batches
            cursor = self.db.cursor()
            success_count = 0
            error_count = 0
            errors = []
            
            try:
                cursor.execute("BEGIN")
                
                for start_idx in range(0, len(df), batch_size):
                    end_idx = min(start_idx + batch_size, len(df))
                    batch = df.iloc[start_idx:end_idx]
                    
                    for idx, row in batch.iterrows():
                        # Create savepoint for each row to allow rollback on error
                        cursor.execute("SAVEPOINT before_row")
                        try:
                            # Handle account_id: CSV may have customer_id strings like "ACC123"
                            # We need to find or create the account and use its integer ID
                            account_id_value = str(row['account_id']).strip()
                            
                            # Try to find existing account by customer_id or by ID if it's numeric
                            cursor.execute("""
                                SELECT id FROM accounts 
                                WHERE (customer_id = %s OR (id::text = %s AND %s ~ '^[0-9]+$'))
                                AND tenant_id = %s
                                LIMIT 1
                            """, (account_id_value, account_id_value, account_id_value, row['tenant_id']))
                            
                            account_result = cursor.fetchone()
                            
                            if account_result:
                                # Account exists, use its ID
                                account_id_int = account_result[0]
                            else:
                                # Account doesn't exist, create it
                                cursor.execute("""
                                    INSERT INTO accounts (customer_id, tenant_id, status)
                                    VALUES (%s, %s, 'ACTIVE')
                                    RETURNING id
                                """, (account_id_value, row['tenant_id']))
                                account_id_int = cursor.fetchone()[0]
                                logger.debug(f"Created new account {account_id_int} for customer_id {account_id_value}")
                            
                            # Map CSV columns to database columns
                            # Note: transactions table does NOT have 'status' or 'device_id' columns
                            
                            # Handle country: database column is VARCHAR(2) for ISO country codes
                            # Truncate to 2 characters if longer, or extract ISO code
                            country_value = row.get('country')
                            if country_value:
                                country_value = str(country_value).strip().upper()
                                # Common country name mappings to ISO codes
                                country_mapping = {
                                    'USA': 'US', 'UNITED STATES': 'US', 'U.S.A': 'US',
                                    'UK': 'GB', 'UNITED KINGDOM': 'GB', 'U.K.': 'GB',
                                    'INDIA': 'IN',
                                    'CANADA': 'CA',
                                    'AUSTRALIA': 'AU',
                                    'GERMANY': 'DE',
                                    'FRANCE': 'FR',
                                    'JAPAN': 'JP',
                                    'CHINA': 'CN',
                                    'BRAZIL': 'BR',
                                    'MEXICO': 'MX',
                                    'SPAIN': 'ES',
                                    'ITALY': 'IT'
                                }
                                
                                # Check mapping first
                                if country_value in country_mapping:
                                    country_value = country_mapping[country_value]
                                # If still longer than 2, truncate to first 2 chars
                                elif len(country_value) > 2:
                                    country_value = country_value[:2]
                                # If empty after strip, set to None
                                if not country_value:
                                    country_value = None
                            else:
                                country_value = None
                            
                            # Handle currency: database column is VARCHAR(3)
                            currency_value = row.get('currency', 'USD')
                            if currency_value:
                                currency_value = str(currency_value).strip().upper()[:3]  # Max 3 chars
                            else:
                                currency_value = 'USD'
                            
                            # Verify tenant_id is set
                            txn_tenant_id = row.get('tenant_id') or tenant_id
                            if not txn_tenant_id:
                                raise ValueError(f"Missing tenant_id for transaction row {success_count + error_count + 1}")
                            
                            cursor.execute("""
                                INSERT INTO transactions (
                                    tenant_id, account_id, amount, currency,
                                    merchant, mcc, channel, city, country,
                                    txn_time
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """, (
                                txn_tenant_id,
                                account_id_int,  # Use integer account ID
                                float(row['amount']),
                                currency_value,
                                row['merchant'],
                                row.get('mcc', '0000'),
                                row.get('channel', 'ONLINE'),
                                row.get('city'),
                                country_value,
                                row['transaction_date']
                            ))
                            success_count += 1
                            
                            # Log first few insertions for debugging
                            if success_count <= 3:
                                logger.debug(f"Inserted transaction: account={account_id_int}, amount={row['amount']}, tenant={txn_tenant_id}")
                        except Exception as e:
                            error_count += 1
                            # Calculate row number (1-based, including header)
                            try:
                                row_num = int(idx) + 2  # +2: idx is 0-based, +1 for header
                            except:
                                row_num = start_idx + len(errors) + 2
                            
                            error_msg = str(e)
                            errors.append({
                                "row": row_num,
                                "error": error_msg
                            })
                            if len(errors) <= 10:  # Only keep first 10 errors
                                logger.warning(f"Row {row_num} failed: {e}")
                            # Rollback to savepoint to allow continuing with next row
                            try:
                                cursor.execute("ROLLBACK TO SAVEPOINT before_row")
                            except Exception as savepoint_error:
                                logger.debug(f"Savepoint rollback failed: {savepoint_error}")
                                # If savepoint fails, we're in a bad state - break out
                                break
                
                cursor.execute("COMMIT")
                
                # Verify inserted data
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE tenant_id = %s", (tenant_id,))
                inserted_count = cursor.fetchone()[0]
                
                logger.info(f"Ingested {success_count} transactions for tenant {tenant_id}")
                logger.info(f"Verified: {inserted_count} total transactions now exist for tenant_id={tenant_id}")
                
                return {
                    "success": True,
                    "rows_processed": len(df),
                    "rows_inserted": success_count,
                    "rows_failed": error_count,
                    "errors": errors[:10],  # First 10 errors
                    "tenant_id": tenant_id  # Include tenant_id in response for debugging
                }
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                logger.error(f"Batch ingestion failed: {e}")
                raise
            finally:
                cursor.close()
                
        except Exception as e:
            logger.error(f"File ingestion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_template(self) -> str:
        """Generate CSV template for download"""
        template_df = pd.DataFrame(columns=self.required_columns + self.optional_columns)
        
        # Add example row
        template_df.loc[0] = {
            'account_id': 'ACC123456',
            'amount': 150.00,
            'merchant': 'Example Store Inc',
            'transaction_date': '2025-10-30 14:30:00',
            'currency': 'USD',
            'mcc': '5411',
            'channel': 'ONLINE',
            'city': 'San Francisco',
            'country': 'USA',
            'device_id': 'DEV789'
        }
        
        return template_df.to_csv(index=False)

