#!/usr/bin/env python3
import os
import random
import string
from datetime import datetime, timedelta
import oracledb
from dotenv import load_dotenv

load_dotenv()

ORACLE_URI = os.getenv("ORACLE_URI")
POSTGRES_URI = os.getenv("POSTGRES_URI")
MONGO_URI = os.getenv("MONGO_URI")

if not ORACLE_URI:
    raise ValueError("❌ ORACLE_URI not found. Please check your .env file or export command.")


def generate_customer_id():
    return f"C{random.randint(1000, 9999)}"


def generate_txn_data(account_id, anomaly_type=None):
    base_time = datetime.now(datetime.UTC).replace(tzinfo=None) - timedelta(days=random.randint(0, 7))
    
    if anomaly_type == "midnight_high":
        txn_time = base_time.replace(hour=random.randint(0, 5), minute=random.randint(0, 59))
        amount = random.randint(6000, 10000)
        merchant = "ATM-CORP"
        mcc = "6011"
        channel = "ATM"
    elif anomaly_type == "geo_jump":
        txn_time = base_time
        amount = random.randint(100, 500)
        # Start in NYC
        lat, lon, city, country = 40.7128, -74.0060, "NYC", "US"
        # Then jump to LA (will be next txn)
        merchant = "HOTEL"
        mcc = "7011"
        channel = "POS"
    elif anomaly_type == "velocity":
        txn_time = base_time
        amount = random.randint(10, 100)
        merchant = "AMAZON"
        mcc = "5999"
        channel = "ONLINE"
    else:
        txn_time = base_time.replace(hour=random.randint(9, 20), minute=random.randint(0, 59))
        amount = random.randint(10, 200)
        merchant = random.choice(["GROCERY", "RESTAURANT", "GAS", "RETAIL"])
        mcc = random.choice(["5411", "5812", "5541", "5331"])
        channel = "POS"
    
    return {
        "account_id": account_id,
        "amount": amount,
        "currency": "USD",
        "merchant": merchant,
        "mcc": mcc,
        "channel": channel,
        "txn_time": txn_time,
    }


def seed_oracle():
    print("Seeding Oracle database...")
    print("🔗 Using Oracle URI:", ORACLE_URI)
    
    # Parse the Oracle URI: oracle+oracledb://user:password@host:port/service
    # Convert to oracledb format: user/password@host:port/service
    connection_string = ORACLE_URI.replace("oracle+oracledb://", "")
    # Replace the first : with / to separate username from password
    if ":" in connection_string and "@" in connection_string:
        username_password, rest = connection_string.split("@", 1)
        username, password = username_password.split(":", 1)
        connection_string = f"{username}/{password}@{rest}"
    
    print(f"🔌 Connecting with: {username}/***@{rest}")
    conn = oracledb.connect(connection_string)
    cursor = conn.cursor()
    
    try:
        # Insert accounts
        accounts = []
        for i in range(10):
            # Create a variable to hold the returned id
            id_var = cursor.var(int)
            cursor.execute("""
                INSERT INTO accounts (id, customer_id, status)
                VALUES (seq_accounts.NEXTVAL, :customer_id, 'ACTIVE')
                RETURNING id INTO :id
            """, {"customer_id": generate_customer_id(), "id": id_var})
            account_id = id_var.getvalue()[0]
            accounts.append(account_id)
        
        conn.commit()
        print(f"Created {len(accounts)} accounts")
        
        # Insert transactions
        txn_count = 0
        for account_id in accounts:
            # Normal transactions
            for _ in range(random.randint(5, 15)):
                txn = generate_txn_data(account_id)
                cursor.execute("""
                    INSERT INTO transactions (
                        id, account_id, amount, currency, merchant, mcc, channel,
                        city, country, txn_time, status
                    )
                    VALUES (
                        seq_txns.NEXTVAL, :account_id, :amount, :currency, :merchant, :mcc, :channel,
                        'NYC', 'US', :txn_time, 'APPROVED'
                    )
                """, txn)
                txn_count += 1
            
            # Inject anomalies occasionally
            if random.random() < 0.3:
                txn = generate_txn_data(account_id, "midnight_high")
                cursor.execute("""
                    INSERT INTO transactions (
                        id, account_id, amount, currency, merchant, mcc, channel,
                        city, country, txn_time, status
                    )
                    VALUES (
                        seq_txns.NEXTVAL, :account_id, :amount, :currency, :merchant, :mcc, :channel,
                        'NYC', 'US', :txn_time, 'APPROVED'
                    )
                """, txn)
                txn_count += 1
            
            # Geo jump for first account
            if account_id == accounts[0]:
                txn1 = generate_txn_data(account_id, "geo_jump")
                txn1.update({"lat": 40.7128, "lon": -74.0060, "city": "NYC"})
                cursor.execute("""
                    INSERT INTO transactions (
                        id, account_id, amount, currency, merchant, mcc, channel,
                        lat, lon, city, country, txn_time, status
                    )
                    VALUES (
                        seq_txns.NEXTVAL, :account_id, :amount, :currency, :merchant, :mcc, :channel,
                        :lat, :lon, :city, 'US', :txn_time, 'APPROVED'
                    )
                """, txn1)
                txn_count += 1
                
                txn2 = generate_txn_data(account_id, "geo_jump")
                txn2.update({"lat": 34.0522, "lon": -118.2437, "city": "LA"})
                txn2["txn_time"] = txn2["txn_time"] + timedelta(hours=1)
                cursor.execute("""
                    INSERT INTO transactions (
                        id, account_id, amount, currency, merchant, mcc, channel,
                        lat, lon, city, country, txn_time, status
                    )
                    VALUES (
                        seq_txns.NEXTVAL, :account_id, :amount, :currency, :merchant, :mcc, :channel,
                        :lat, :lon, :city, 'US', :txn_time, 'APPROVED'
                    )
                """, txn2)
                txn_count += 1
        
        conn.commit()
        print(f"Created {txn_count} transactions")
        print("Oracle seeding complete!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding Oracle: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_oracle()
    print("\n=== Seeding Complete ===")
    print("Check alerts: curl http://localhost:8000/v1/alerts?status=open")

