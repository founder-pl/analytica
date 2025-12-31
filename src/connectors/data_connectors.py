"""
ANALYTICA Data Connectors
=========================

Universal data connectors for various sources:
- Database (PostgreSQL, MySQL, SQLite, MongoDB)
- Cloud Storage (S3, GCS, Azure Blob)
- APIs (REST, GraphQL)
- Messaging (Kafka, RabbitMQ, Redis)
"""

from typing import Any, Dict, List, Optional, Union, Generator
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from contextlib import contextmanager
import json


# ============================================================
# BASE CONNECTOR
# ============================================================

@dataclass
class ConnectionConfig:
    """Connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    ssl: bool = False
    options: Dict[str, Any] = field(default_factory=dict)


class DataConnector(ABC):
    """Base class for data connectors"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection"""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query and return results"""
        pass
    
    @abstractmethod
    def fetch_all(self, table: str, limit: int = None) -> List[Dict]:
        """Fetch all records from table"""
        pass
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# ============================================================
# POSTGRESQL CONNECTOR
# ============================================================

class PostgreSQLConnector(DataConnector):
    """PostgreSQL database connector"""
    
    def connect(self) -> bool:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            self._connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                cursor_factory=RealDictCursor
            )
            return True
        except Exception as e:
            print(f"PostgreSQL connection error: {e}")
            return False
    
    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: Dict = None) -> List[Dict]:
        cursor = self._connection.cursor()
        cursor.execute(query, params or {})
        
        if cursor.description:
            results = [dict(row) for row in cursor.fetchall()]
        else:
            results = []
            self._connection.commit()
        
        cursor.close()
        return results
    
    def fetch_all(self, table: str, limit: int = None) -> List[Dict]:
        query = f"SELECT * FROM {table}"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute(query)
    
    def insert(self, table: str, data: Dict) -> int:
        """Insert record and return ID"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({k})s" for k in data.keys()])
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        
        result = cursor.fetchone()
        self._connection.commit()
        cursor.close()
        
        return result['id'] if result else None
    
    def update(self, table: str, data: Dict, where: Dict) -> int:
        """Update records, return affected count"""
        set_clause = ", ".join([f"{k} = %({k})s" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = %(where_{k})s" for k in where.keys()])
        
        params = {**data, **{f"where_{k}": v for k, v in where.items()}}
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        
        affected = cursor.rowcount
        self._connection.commit()
        cursor.close()
        
        return affected


# ============================================================
# MYSQL CONNECTOR
# ============================================================

class MySQLConnector(DataConnector):
    """MySQL database connector"""
    
    def connect(self) -> bool:
        try:
            import mysql.connector
            
            self._connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password
            )
            return True
        except Exception as e:
            print(f"MySQL connection error: {e}")
            return False
    
    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: Dict = None) -> List[Dict]:
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(query, params or {})
        
        if cursor.description:
            results = cursor.fetchall()
        else:
            results = []
            self._connection.commit()
        
        cursor.close()
        return results
    
    def fetch_all(self, table: str, limit: int = None) -> List[Dict]:
        query = f"SELECT * FROM {table}"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute(query)


# ============================================================
# SQLITE CONNECTOR
# ============================================================

class SQLiteConnector(DataConnector):
    """SQLite database connector"""
    
    def __init__(self, database_path: str):
        config = ConnectionConfig(database=database_path)
        super().__init__(config)
    
    def connect(self) -> bool:
        try:
            import sqlite3
            
            self._connection = sqlite3.connect(self.config.database)
            self._connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"SQLite connection error: {e}")
            return False
    
    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: Dict = None) -> List[Dict]:
        cursor = self._connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if cursor.description:
            results = [dict(row) for row in cursor.fetchall()]
        else:
            results = []
            self._connection.commit()
        
        cursor.close()
        return results
    
    def fetch_all(self, table: str, limit: int = None) -> List[Dict]:
        query = f"SELECT * FROM {table}"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute(query)


# ============================================================
# MONGODB CONNECTOR
# ============================================================

class MongoDBConnector(DataConnector):
    """MongoDB database connector"""
    
    def connect(self) -> bool:
        try:
            from pymongo import MongoClient
            
            uri = f"mongodb://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}"
            self._client = MongoClient(uri)
            self._connection = self._client[self.config.database]
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            return False
    
    def disconnect(self):
        if hasattr(self, '_client') and self._client:
            self._client.close()
            self._connection = None
    
    def execute(self, query: str, params: Dict = None) -> List[Dict]:
        """For MongoDB, query is collection name, params is filter"""
        collection = self._connection[query]
        return list(collection.find(params or {}))
    
    def fetch_all(self, table: str, limit: int = None) -> List[Dict]:
        collection = self._connection[table]
        cursor = collection.find()
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def insert(self, collection: str, data: Dict) -> str:
        result = self._connection[collection].insert_one(data)
        return str(result.inserted_id)
    
    def aggregate(self, collection: str, pipeline: List[Dict]) -> List[Dict]:
        """Run aggregation pipeline"""
        return list(self._connection[collection].aggregate(pipeline))


# ============================================================
# REST API CONNECTOR
# ============================================================

class RESTAPIConnector:
    """REST API connector"""
    
    def __init__(
        self,
        base_url: str,
        auth_type: str = None,  # basic, bearer, api_key
        auth_credentials: Dict = None,
        headers: Dict = None
    ):
        self.base_url = base_url.rstrip('/')
        self.auth_type = auth_type
        self.auth_credentials = auth_credentials or {}
        self.default_headers = headers or {}
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    def _build_headers(self) -> Dict[str, str]:
        headers = {**self.default_headers}
        
        if self.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.auth_credentials.get('token', '')}"
        elif self.auth_type == "api_key":
            key_name = self.auth_credentials.get('header_name', 'X-API-Key')
            headers[key_name] = self.auth_credentials.get('api_key', '')
        
        return headers
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET request"""
        response = self._get_client().get(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            params=params,
            headers=self._build_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict = None, json_data: Dict = None) -> Dict:
        """POST request"""
        response = self._get_client().post(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            data=data,
            json=json_data,
            headers=self._build_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, json_data: Dict) -> Dict:
        """PUT request"""
        response = self._get_client().put(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            json=json_data,
            headers=self._build_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> bool:
        """DELETE request"""
        response = self._get_client().delete(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            headers=self._build_headers()
        )
        response.raise_for_status()
        return True
    
    def paginate(
        self, 
        endpoint: str, 
        page_param: str = "page",
        per_page: int = 100,
        data_key: str = "data"
    ) -> Generator[Dict, None, None]:
        """Paginated GET request"""
        page = 1
        while True:
            response = self.get(endpoint, {page_param: page, "per_page": per_page})
            
            items = response.get(data_key, [])
            if not items:
                break
            
            for item in items:
                yield item
            
            page += 1
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# S3 CONNECTOR
# ============================================================

class S3Connector:
    """AWS S3 connector"""
    
    def __init__(
        self,
        bucket: str,
        aws_access_key: str = None,
        aws_secret_key: str = None,
        region: str = "eu-central-1",
        endpoint_url: str = None  # For S3-compatible services
    ):
        self.bucket = bucket
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        self.endpoint_url = endpoint_url
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import boto3
            
            self._client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
        return self._client
    
    def list_objects(self, prefix: str = "") -> List[Dict]:
        """List objects in bucket"""
        response = self._get_client().list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix
        )
        return response.get('Contents', [])
    
    def get_object(self, key: str) -> bytes:
        """Get object content"""
        response = self._get_client().get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()
    
    def get_json(self, key: str) -> Dict:
        """Get JSON object"""
        content = self.get_object(key)
        return json.loads(content.decode('utf-8'))
    
    def put_object(self, key: str, content: Union[bytes, str]) -> bool:
        """Upload object"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        self._get_client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content
        )
        return True
    
    def put_json(self, key: str, data: Dict) -> bool:
        """Upload JSON object"""
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return self.put_object(key, content)
    
    def delete_object(self, key: str) -> bool:
        """Delete object"""
        self._get_client().delete_object(Bucket=self.bucket, Key=key)
        return True


# ============================================================
# REDIS CONNECTOR
# ============================================================

class RedisConnector:
    """Redis connector for caching and messaging"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            import redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
        return self._client
    
    def get(self, key: str) -> Optional[str]:
        """Get value"""
        return self._get_client().get(key)
    
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value with optional TTL"""
        return self._get_client().set(key, value, ex=ttl)
    
    def get_json(self, key: str) -> Optional[Dict]:
        """Get JSON value"""
        value = self.get(key)
        return json.loads(value) if value else None
    
    def set_json(self, key: str, data: Dict, ttl: int = None) -> bool:
        """Set JSON value"""
        return self.set(key, json.dumps(data), ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        return bool(self._get_client().delete(key))
    
    def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        return self._get_client().publish(channel, message)
    
    def subscribe(self, channel: str):
        """Subscribe to channel"""
        pubsub = self._get_client().pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# FACTORY
# ============================================================

def create_connector(
    connector_type: str,
    **kwargs
) -> Union[DataConnector, RESTAPIConnector, S3Connector, RedisConnector]:
    """
    Factory function to create connector
    
    Types: postgresql, mysql, sqlite, mongodb, rest, s3, redis
    """
    connectors = {
        "postgresql": lambda: PostgreSQLConnector(ConnectionConfig(**kwargs)),
        "mysql": lambda: MySQLConnector(ConnectionConfig(**kwargs)),
        "sqlite": lambda: SQLiteConnector(kwargs.get("database", ":memory:")),
        "mongodb": lambda: MongoDBConnector(ConnectionConfig(**kwargs)),
        "rest": lambda: RESTAPIConnector(**kwargs),
        "s3": lambda: S3Connector(**kwargs),
        "redis": lambda: RedisConnector(**kwargs),
    }
    
    if connector_type.lower() not in connectors:
        raise ValueError(f"Unknown connector type: {connector_type}")
    
    return connectors[connector_type.lower()]()


__all__ = [
    'ConnectionConfig',
    'DataConnector',
    'PostgreSQLConnector',
    'MySQLConnector',
    'SQLiteConnector',
    'MongoDBConnector',
    'RESTAPIConnector',
    'S3Connector',
    'RedisConnector',
    'create_connector'
]
