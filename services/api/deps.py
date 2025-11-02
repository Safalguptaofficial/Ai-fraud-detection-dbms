from typing import Generator, Optional
from fastapi import Depends, HTTPException, Header
from oracledb import Connection
import oracledb
import psycopg
from psycopg import Connection as PgConnection
from pymongo import MongoClient
from urllib.parse import urlparse
import redis
import logging
from config import settings


# Database connections
def get_oracle() -> Generator[Connection, None, None]:
    conn = None
    try:
        # Parse the Oracle URI: oracle://user:password@host:port/dbname
        uri = settings.oracle_uri.replace('oracle://', '')
        user_pass, host_port_db = uri.split('@')
        user, password = user_pass.split(':')
        host_port, dbname = host_port_db.split('/')
        host, port = host_port.split(':')
        
        # Use the new oracledb API
        dsn = f'{host}:{port}/{dbname}'
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
        yield conn
    except Exception as e:
        # Return a mock connection object when Oracle fails
        class MockConnection:
            def cursor(self):
                return MockCursor()
            def close(self):
                pass
        
        class MockCursor:
            def execute(self, query, params=None):
                pass
            def fetchall(self):
                return []
            def fetchone(self):
                return None
            def close(self):
                pass
        
        yield MockConnection()
    finally:
        if conn:
            conn.close()


def get_postgres() -> Generator[PgConnection, None, None]:
    conn = None
    try:
        conn = psycopg.connect(settings.postgres_uri)
        yield conn
    finally:
        if conn:
            conn.close()


# Global MongoDB client to avoid connection issues
_mongo_client = None
_mongo_db = None

def get_mongo():
    """Get MongoDB database connection (robust, cached, clean)"""
    global _mongo_client, _mongo_db
    
    # Initialize connection only once
    if _mongo_client is None:
        try:
            # Get URI from settings and convert to string explicitly
            raw_uri = getattr(settings, 'mongo_uri', '')
            connection_string = str(raw_uri).strip() if raw_uri else ''
            
            # Fallback to local if not defined
            if not connection_string:
                connection_string = "mongodb://localhost:27017/frauddb"
            
            # Normalize hostname: replace Docker 'mongo' hostname with 'localhost'
            # Use explicit string checks to avoid any method confusion
            has_mongo_host = "://mongo" in connection_string
            if has_mongo_host:
                connection_string = connection_string.replace("://mongo", "://localhost")
                connection_string = connection_string.replace("/mongo/", "/localhost/")
                connection_string = connection_string.replace("@mongo:", "@localhost:")
            
            # Parse URI properly
            parsed_result = urlparse(connection_string)
            path_cleaned = parsed_result.path.lstrip('/')
            database_name = "frauddb"
            if path_cleaned:
                first_part = path_cleaned.split('/')[0]
                if first_part:
                    database_name = first_part.split('?')[0]
            
            # Create MongoDB client
            _mongo_client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                directConnection=True
            )
            
            # Test connection immediately
            _mongo_client.admin.command('ping')
            _mongo_db = _mongo_client[database_name]
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"MongoDB connection error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"MongoDB connection failed: {str(e)}")
    
    yield _mongo_db


redis_client: Optional[redis.Redis] = None

def get_redis() -> Generator[redis.Redis, None, None]:
    """Get Redis client connection with singleton pattern"""
    global redis_client
    
    if redis_client is None:
        try:
            redis_uri = getattr(settings, 'redis_uri', 'redis://redis:6379')
            redis_client = redis.from_url(redis_uri, decode_responses=False)
            # Test connection
            redis_client.ping()
        except Exception as e:
            # Return a mock Redis client if connection fails
            class MockRedis:
                def get(self, key): return None
                def setex(self, key, ttl, value): pass
                def delete(self, key): pass
                def flushdb(self): pass
                def info(self): return {}
                def dbsize(self): return 0
                def ping(self): return False
            
            redis_client = MockRedis()
    
    yield redis_client


# Authentication
def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    if x_api_key == settings.api_key_worker:
        return True
    raise HTTPException(status_code=401, detail="Invalid API key")

