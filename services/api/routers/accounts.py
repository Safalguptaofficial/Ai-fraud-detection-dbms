from typing import List
from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection as PgConnection
from oracledb import Connection as OracleConnection
from deps import get_postgres, get_oracle
from models.account import Account, AccountCreate, AccountUpdate

router = APIRouter()


@router.get("/accounts", response_model=List[Account])
async def list_accounts(oracle: OracleConnection = Depends(get_oracle), postgres: PgConnection = Depends(get_postgres)):
    # Try Oracle first, fall back to PostgreSQL
    try:
        cursor = oracle.cursor()
        cursor.execute("""
            SELECT id, customer_id, status, created_at, updated_at
            FROM accounts
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [
            Account(
                id=row[0],
                customer_id=row[1],
                status=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
            for row in rows
        ]
    except:
        # Fallback to PostgreSQL
        cursor = postgres.cursor()
        cursor.execute("""
            SELECT id, customer_id, status, created_at, updated_at
            FROM accounts
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [
            Account(
                id=row[0],
                customer_id=row[1],
                status=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
            for row in rows
        ]


@router.post("/accounts", response_model=Account)
async def create_account(data: AccountCreate, postgres: PgConnection = Depends(get_postgres)):
    cursor = postgres.cursor()
    try:
        cursor.execute("""
            INSERT INTO accounts (customer_id, status)
            VALUES (%s, 'ACTIVE')
            RETURNING id, customer_id, status, created_at, updated_at
        """, [data.customer_id])
        
        account = cursor.fetchone()
        postgres.commit()
        return Account(
            id=account[0],
            customer_id=account[1],
            status=account[2],
            created_at=account[3],
            updated_at=account[4]
        )
    except Exception as e:
        postgres.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()


@router.get("/accounts/{account_id}", response_model=Account)
async def get_account(account_id: int, postgres: PgConnection = Depends(get_postgres)):
    cursor = postgres.cursor()
    try:
        cursor.execute("""
            SELECT id, customer_id, status, created_at, updated_at
            FROM accounts
            WHERE id = %s
        """, [account_id])
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return Account(
            id=row[0],
            customer_id=row[1],
            status=row[2],
            created_at=row[3],
            updated_at=row[4]
        )
    finally:
        cursor.close()


@router.patch("/accounts/{account_id}", response_model=Account)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    postgres: PgConnection = Depends(get_postgres)
):
    cursor = postgres.cursor()
    try:
        if data.status:
            cursor.execute("""
                UPDATE accounts
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [data.status, account_id])
        
        postgres.commit()
        
        return await get_account(account_id, postgres)
    except Exception as e:
        postgres.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

