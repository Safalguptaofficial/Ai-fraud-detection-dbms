from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from oracledb import Connection
from deps import get_oracle, verify_api_key
from models.transaction import Transaction, TransactionCreate

router = APIRouter()


@router.post("/transactions", response_model=Transaction)
async def create_transaction(
    data: TransactionCreate,
    oracle: Connection = Depends(get_oracle),
    _auth: bool = Depends(verify_api_key)
):
    cursor = oracle.cursor()
    try:
        cursor.execute("""
            INSERT INTO transactions (
                id, account_id, amount, currency, merchant, mcc, channel,
                device_id, lat, lon, city, country, txn_time, auth_code
            )
            VALUES (
                seq_txns.NEXTVAL, :account_id, :amount, :currency, :merchant, :mcc, :channel,
                :device_id, :lat, :lon, :city, :country, :txn_time, :auth_code
            )
            RETURNING id INTO :id
        """, [
            data.account_id, data.amount, data.currency, data.merchant, data.mcc, data.channel,
            data.device_id, data.lat, data.lon, data.city, data.country, data.txn_time, data.auth_code,
            None
        ])
        
        txn_id = cursor.fetchone()[0]
        oracle.commit()
        
        # Fetch the inserted transaction
        cursor.execute("""
            SELECT id, account_id, amount, currency, merchant, mcc, channel, device_id,
                   lat, lon, city, country, txn_time, auth_code, status, created_at
            FROM transactions
            WHERE id = :id
        """, [txn_id])
        
        row = cursor.fetchone()
        return Transaction(
            id=row[0],
            account_id=row[1],
            amount=float(row[2]),
            currency=row[3],
            merchant=row[4],
            mcc=row[5],
            channel=row[6],
            device_id=row[7],
            lat=float(row[8]) if row[8] else None,
            lon=float(row[9]) if row[9] else None,
            city=row[10],
            country=row[11],
            txn_time=row[12],
            auth_code=row[13],
            status=row[14],
            created_at=row[15]
        )
    except Exception as e:
        oracle.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()


@router.get("/transactions", response_model=List[Transaction])
async def list_transactions(
    account_id: int = None,
    limit: int = 100,
    offset: int = 0,
    oracle: Connection = Depends(get_oracle)
):
    cursor = oracle.cursor()
    try:
        query = """
            SELECT id, account_id, amount, currency, merchant, mcc, channel, device_id,
                   lat, lon, city, country, txn_time, auth_code, status, created_at
            FROM transactions
        """
        params = []
        
        if account_id:
            query += " WHERE account_id = :account_id"
            params = [account_id]
        
        query += " ORDER BY txn_time DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params.extend([offset, limit])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            Transaction(
                id=row[0],
                account_id=row[1],
                amount=float(row[2]),
                currency=row[3],
                merchant=row[4],
                mcc=row[5],
                channel=row[6],
                device_id=row[7],
                lat=float(row[8]) if row[8] else None,
                lon=float(row[9]) if row[9] else None,
                city=row[10],
                country=row[11],
                txn_time=row[12],
                auth_code=row[13],
                status=row[14],
                created_at=row[15]
            )
            for row in rows
        ]
    finally:
        cursor.close()

