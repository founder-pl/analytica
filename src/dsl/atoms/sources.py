"""
ANALYTICA DSL - Data Source Atoms
==================================
Multiplatform data source connectors for DSL pipelines.

Supports:
- Web: HTTP/REST, GraphQL, WebSocket
- IoT: MQTT, CoAP, AMQP, Modbus, OPC-UA
- Databases: SQL, MongoDB, Redis, Elasticsearch
- Cloud: AWS S3, Azure Blob, GCP Storage
- Streaming: Kafka, RabbitMQ, NATS
- Files: CSV, JSON, XML, Parquet, Excel
- APIs: Social, Finance, Weather, Blockchain
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

from ..core.parser import AtomRegistry, PipelineContext


# ============================================================
# SOURCE ATOM TYPE
# ============================================================

def _source_result(data: Any, metadata: Dict) -> Dict:
    """Wrap source data with metadata"""
    return {
        "data": data,
        "source": metadata,
        "fetched_at": datetime.utcnow().isoformat()
    }


# ============================================================
# WEB PROTOCOLS
# ============================================================

@AtomRegistry.register("source", "http")
def source_http(ctx: PipelineContext, **params) -> Dict:
    """
    Fetch data from HTTP/REST API
    
    Usage:
        source.http(url="https://api.example.com/data", method="GET")
        source.http(url="...", method="POST", body={...}, headers={...})
    """
    url = params.get("url", params.get("_arg0", ""))
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    body = params.get("body", None)
    auth = params.get("auth", None)  # {"type": "bearer", "token": "..."} or {"type": "basic", "user": "...", "pass": "..."}
    timeout = params.get("timeout", 30)
    retry = params.get("retry", 3)
    
    ctx.log(f"HTTP {method} {url}")
    
    # In production, this would use aiohttp/httpx
    return _source_result(
        {"_pending": True, "_url": url},
        {
            "type": "http",
            "url": url,
            "method": method,
            "headers": headers,
            "auth_type": auth.get("type") if auth else None,
            "timeout": timeout,
            "retry": retry
        }
    )


@AtomRegistry.register("source", "graphql")
def source_graphql(ctx: PipelineContext, **params) -> Dict:
    """
    Fetch data from GraphQL API
    
    Usage:
        source.graphql(endpoint="https://api.example.com/graphql", query="{ users { id name } }")
        source.graphql(endpoint="...", query="...", variables={"id": 1})
    """
    endpoint = params.get("endpoint", params.get("_arg0", ""))
    query = params.get("query", "")
    variables = params.get("variables", {})
    headers = params.get("headers", {})
    operation = params.get("operation", None)
    
    ctx.log(f"GraphQL query to {endpoint}")
    
    return _source_result(
        {"_pending": True, "_endpoint": endpoint},
        {
            "type": "graphql",
            "endpoint": endpoint,
            "query": query,
            "variables": variables,
            "operation": operation
        }
    )


@AtomRegistry.register("source", "websocket")
def source_websocket(ctx: PipelineContext, **params) -> Dict:
    """
    Connect to WebSocket for real-time data
    
    Usage:
        source.websocket(url="wss://stream.example.com", subscribe={"channel": "trades"})
    """
    url = params.get("url", params.get("_arg0", ""))
    subscribe = params.get("subscribe", {})
    reconnect = params.get("reconnect", True)
    buffer_size = params.get("buffer", 100)
    
    ctx.log(f"WebSocket connect to {url}")
    
    return _source_result(
        {"_streaming": True, "_url": url},
        {
            "type": "websocket",
            "url": url,
            "subscribe": subscribe,
            "reconnect": reconnect,
            "buffer_size": buffer_size
        }
    )


@AtomRegistry.register("source", "sse")
def source_sse(ctx: PipelineContext, **params) -> Dict:
    """
    Server-Sent Events stream
    
    Usage:
        source.sse(url="https://api.example.com/events")
    """
    url = params.get("url", params.get("_arg0", ""))
    
    ctx.log(f"SSE connect to {url}")
    
    return _source_result(
        {"_streaming": True, "_url": url},
        {"type": "sse", "url": url}
    )


# ============================================================
# IOT PROTOCOLS
# ============================================================

@AtomRegistry.register("source", "mqtt")
def source_mqtt(ctx: PipelineContext, **params) -> Dict:
    """
    Subscribe to MQTT broker for IoT data
    
    Usage:
        source.mqtt(broker="mqtt://localhost:1883", topic="sensors/#")
        source.mqtt(broker="...", topic="...", qos=1, client_id="analytica")
    """
    broker = params.get("broker", params.get("_arg0", ""))
    topic = params.get("topic", "#")
    qos = params.get("qos", 0)
    client_id = params.get("client_id", "analytica-dsl")
    username = params.get("username", None)
    password = params.get("password", None)
    tls = params.get("tls", False)
    
    ctx.log(f"MQTT subscribe to {broker} topic={topic}")
    
    return _source_result(
        {"_streaming": True, "_broker": broker, "_topic": topic},
        {
            "type": "mqtt",
            "broker": broker,
            "topic": topic,
            "qos": qos,
            "client_id": client_id,
            "tls": tls
        }
    )


@AtomRegistry.register("source", "coap")
def source_coap(ctx: PipelineContext, **params) -> Dict:
    """
    Fetch data from CoAP endpoint (Constrained Application Protocol)
    
    Usage:
        source.coap(uri="coap://sensor.local/temperature")
        source.coap(uri="...", observe=True)
    """
    uri = params.get("uri", params.get("_arg0", ""))
    observe = params.get("observe", False)
    confirmable = params.get("confirmable", True)
    
    ctx.log(f"CoAP {'observe' if observe else 'get'} {uri}")
    
    return _source_result(
        {"_pending": True, "_uri": uri},
        {
            "type": "coap",
            "uri": uri,
            "observe": observe,
            "confirmable": confirmable
        }
    )


@AtomRegistry.register("source", "amqp")
def source_amqp(ctx: PipelineContext, **params) -> Dict:
    """
    Consume from AMQP queue (RabbitMQ compatible)
    
    Usage:
        source.amqp(url="amqp://localhost", queue="sensor-data")
        source.amqp(url="...", exchange="events", routing_key="sensor.*")
    """
    url = params.get("url", params.get("_arg0", ""))
    queue = params.get("queue", "")
    exchange = params.get("exchange", "")
    routing_key = params.get("routing_key", "#")
    prefetch = params.get("prefetch", 10)
    
    ctx.log(f"AMQP consume from {url} queue={queue}")
    
    return _source_result(
        {"_streaming": True, "_url": url},
        {
            "type": "amqp",
            "url": url,
            "queue": queue,
            "exchange": exchange,
            "routing_key": routing_key,
            "prefetch": prefetch
        }
    )


@AtomRegistry.register("source", "modbus")
def source_modbus(ctx: PipelineContext, **params) -> Dict:
    """
    Read from Modbus device (industrial IoT)
    
    Usage:
        source.modbus(host="192.168.1.100", port=502, unit=1, register=0, count=10)
        source.modbus(host="...", type="holding", register=100)
    """
    host = params.get("host", params.get("_arg0", ""))
    port = params.get("port", 502)
    unit = params.get("unit", 1)
    register_type = params.get("type", "holding")  # holding, input, coil, discrete
    register = params.get("register", 0)
    count = params.get("count", 1)
    poll_interval = params.get("poll", 1000)  # ms
    
    ctx.log(f"Modbus read {host}:{port} unit={unit} reg={register}")
    
    return _source_result(
        {"_pending": True, "_host": host},
        {
            "type": "modbus",
            "host": host,
            "port": port,
            "unit": unit,
            "register_type": register_type,
            "register": register,
            "count": count,
            "poll_interval": poll_interval
        }
    )


@AtomRegistry.register("source", "opcua")
def source_opcua(ctx: PipelineContext, **params) -> Dict:
    """
    Read from OPC-UA server (industrial automation)
    
    Usage:
        source.opcua(endpoint="opc.tcp://localhost:4840", nodes=["ns=2;s=Temperature"])
        source.opcua(endpoint="...", nodes=[...], subscribe=True)
    """
    endpoint = params.get("endpoint", params.get("_arg0", ""))
    nodes = params.get("nodes", [])
    subscribe = params.get("subscribe", False)
    security = params.get("security", "None")  # None, Basic128Rsa15, Basic256Sha256
    
    ctx.log(f"OPC-UA {'subscribe' if subscribe else 'read'} {endpoint}")
    
    return _source_result(
        {"_pending": True, "_endpoint": endpoint},
        {
            "type": "opcua",
            "endpoint": endpoint,
            "nodes": nodes,
            "subscribe": subscribe,
            "security": security
        }
    )


@AtomRegistry.register("source", "serial")
def source_serial(ctx: PipelineContext, **params) -> Dict:
    """
    Read from serial port (sensors, Arduino, etc.)
    
    Usage:
        source.serial(port="/dev/ttyUSB0", baud=9600)
        source.serial(port="COM3", baud=115200, format="json")
    """
    port = params.get("port", params.get("_arg0", ""))
    baud = params.get("baud", 9600)
    data_format = params.get("format", "line")  # line, json, binary
    delimiter = params.get("delimiter", "\n")
    
    ctx.log(f"Serial read {port} @ {baud}")
    
    return _source_result(
        {"_streaming": True, "_port": port},
        {
            "type": "serial",
            "port": port,
            "baud": baud,
            "format": data_format,
            "delimiter": delimiter
        }
    )


# ============================================================
# DATABASES
# ============================================================

@AtomRegistry.register("source", "sql")
def source_sql(ctx: PipelineContext, **params) -> Dict:
    """
    Query SQL database
    
    Usage:
        source.sql(dsn="postgresql://user:pass@host/db", query="SELECT * FROM users")
        source.sql(dsn="mysql://...", query="...", params={"id": 1})
    """
    dsn = params.get("dsn", params.get("_arg0", ""))
    query = params.get("query", "")
    query_params = params.get("params", {})
    fetch = params.get("fetch", "all")  # all, one, many
    limit = params.get("limit", None)
    
    ctx.log(f"SQL query to {dsn.split('@')[-1] if '@' in dsn else dsn}")
    
    return _source_result(
        {"_pending": True, "_query": query[:50]},
        {
            "type": "sql",
            "dsn": dsn,
            "query": query,
            "params": query_params,
            "fetch": fetch,
            "limit": limit
        }
    )


@AtomRegistry.register("source", "mongodb")
def source_mongodb(ctx: PipelineContext, **params) -> Dict:
    """
    Query MongoDB collection
    
    Usage:
        source.mongodb(uri="mongodb://localhost/mydb", collection="users", filter={"active": True})
        source.mongodb(uri="...", collection="...", pipeline=[{"$match": {...}}])
    """
    uri = params.get("uri", params.get("_arg0", ""))
    collection = params.get("collection", "")
    query_filter = params.get("filter", {})
    pipeline = params.get("pipeline", None)  # Aggregation pipeline
    projection = params.get("projection", None)
    sort = params.get("sort", None)
    limit = params.get("limit", None)
    
    ctx.log(f"MongoDB query {collection}")
    
    return _source_result(
        {"_pending": True, "_collection": collection},
        {
            "type": "mongodb",
            "uri": uri,
            "collection": collection,
            "filter": query_filter,
            "pipeline": pipeline,
            "projection": projection,
            "sort": sort,
            "limit": limit
        }
    )


@AtomRegistry.register("source", "redis")
def source_redis(ctx: PipelineContext, **params) -> Dict:
    """
    Read from Redis
    
    Usage:
        source.redis(url="redis://localhost", key="mydata")
        source.redis(url="...", pattern="sensor:*", type="stream")
    """
    url = params.get("url", params.get("_arg0", ""))
    key = params.get("key", "")
    pattern = params.get("pattern", None)
    data_type = params.get("type", "string")  # string, hash, list, set, stream, timeseries
    
    ctx.log(f"Redis read {key or pattern}")
    
    return _source_result(
        {"_pending": True, "_key": key},
        {
            "type": "redis",
            "url": url,
            "key": key,
            "pattern": pattern,
            "data_type": data_type
        }
    )


@AtomRegistry.register("source", "elasticsearch")
def source_elasticsearch(ctx: PipelineContext, **params) -> Dict:
    """
    Search Elasticsearch
    
    Usage:
        source.elasticsearch(url="http://localhost:9200", index="logs", query={"match": {"level": "error"}})
    """
    url = params.get("url", params.get("_arg0", ""))
    index = params.get("index", "")
    query = params.get("query", {"match_all": {}})
    size = params.get("size", 100)
    sort = params.get("sort", None)
    aggregations = params.get("aggs", None)
    
    ctx.log(f"Elasticsearch search {index}")
    
    return _source_result(
        {"_pending": True, "_index": index},
        {
            "type": "elasticsearch",
            "url": url,
            "index": index,
            "query": query,
            "size": size,
            "sort": sort,
            "aggregations": aggregations
        }
    )


@AtomRegistry.register("source", "influxdb")
def source_influxdb(ctx: PipelineContext, **params) -> Dict:
    """
    Query InfluxDB (time series)
    
    Usage:
        source.influxdb(url="http://localhost:8086", bucket="sensors", query="from(bucket:\"sensors\") |> range(start: -1h)")
    """
    url = params.get("url", params.get("_arg0", ""))
    bucket = params.get("bucket", "")
    query = params.get("query", "")
    org = params.get("org", "")
    token = params.get("token", "")
    
    ctx.log(f"InfluxDB query {bucket}")
    
    return _source_result(
        {"_pending": True, "_bucket": bucket},
        {
            "type": "influxdb",
            "url": url,
            "bucket": bucket,
            "query": query,
            "org": org
        }
    )


# ============================================================
# CLOUD STORAGE
# ============================================================

@AtomRegistry.register("source", "s3")
def source_s3(ctx: PipelineContext, **params) -> Dict:
    """
    Read from AWS S3
    
    Usage:
        source.s3(bucket="my-bucket", key="data/file.json")
        source.s3(bucket="...", prefix="logs/", format="parquet")
    """
    bucket = params.get("bucket", params.get("_arg0", ""))
    key = params.get("key", "")
    prefix = params.get("prefix", "")
    data_format = params.get("format", "auto")
    region = params.get("region", "us-east-1")
    
    ctx.log(f"S3 read s3://{bucket}/{key or prefix}")
    
    return _source_result(
        {"_pending": True, "_bucket": bucket},
        {
            "type": "s3",
            "bucket": bucket,
            "key": key,
            "prefix": prefix,
            "format": data_format,
            "region": region
        }
    )


@AtomRegistry.register("source", "azure_blob")
def source_azure_blob(ctx: PipelineContext, **params) -> Dict:
    """
    Read from Azure Blob Storage
    
    Usage:
        source.azure_blob(container="mycontainer", blob="data.json")
    """
    container = params.get("container", params.get("_arg0", ""))
    blob = params.get("blob", "")
    prefix = params.get("prefix", "")
    account = params.get("account", "")
    
    ctx.log(f"Azure Blob read {container}/{blob or prefix}")
    
    return _source_result(
        {"_pending": True, "_container": container},
        {
            "type": "azure_blob",
            "container": container,
            "blob": blob,
            "prefix": prefix,
            "account": account
        }
    )


@AtomRegistry.register("source", "gcs")
def source_gcs(ctx: PipelineContext, **params) -> Dict:
    """
    Read from Google Cloud Storage
    
    Usage:
        source.gcs(bucket="my-bucket", object="data.json")
    """
    bucket = params.get("bucket", params.get("_arg0", ""))
    obj = params.get("object", params.get("key", ""))
    prefix = params.get("prefix", "")
    project = params.get("project", "")
    
    ctx.log(f"GCS read gs://{bucket}/{obj or prefix}")
    
    return _source_result(
        {"_pending": True, "_bucket": bucket},
        {
            "type": "gcs",
            "bucket": bucket,
            "object": obj,
            "prefix": prefix,
            "project": project
        }
    )


# ============================================================
# STREAMING PLATFORMS
# ============================================================

@AtomRegistry.register("source", "kafka")
def source_kafka(ctx: PipelineContext, **params) -> Dict:
    """
    Consume from Apache Kafka
    
    Usage:
        source.kafka(brokers="localhost:9092", topic="events")
        source.kafka(brokers="...", topics=["events", "logs"], group="analytica")
    """
    brokers = params.get("brokers", params.get("_arg0", ""))
    topic = params.get("topic", "")
    topics = params.get("topics", [topic] if topic else [])
    group = params.get("group", "analytica-dsl")
    offset = params.get("offset", "latest")  # latest, earliest, timestamp
    
    ctx.log(f"Kafka consume from {topics}")
    
    return _source_result(
        {"_streaming": True, "_topics": topics},
        {
            "type": "kafka",
            "brokers": brokers,
            "topics": topics,
            "group": group,
            "offset": offset
        }
    )


@AtomRegistry.register("source", "nats")
def source_nats(ctx: PipelineContext, **params) -> Dict:
    """
    Subscribe to NATS subject
    
    Usage:
        source.nats(url="nats://localhost:4222", subject="events.>")
    """
    url = params.get("url", params.get("_arg0", ""))
    subject = params.get("subject", ">")
    queue = params.get("queue", "")
    
    ctx.log(f"NATS subscribe to {subject}")
    
    return _source_result(
        {"_streaming": True, "_subject": subject},
        {
            "type": "nats",
            "url": url,
            "subject": subject,
            "queue": queue
        }
    )


# ============================================================
# FILE SOURCES
# ============================================================

@AtomRegistry.register("source", "file")
def source_file(ctx: PipelineContext, **params) -> Dict:
    """
    Read from local file
    
    Usage:
        source.file(path="/data/input.csv")
        source.file(path="...", format="json", encoding="utf-8")
    """
    path = params.get("path", params.get("_arg0", ""))
    data_format = params.get("format", "auto")  # auto, csv, json, xml, parquet, excel
    encoding = params.get("encoding", "utf-8")
    sheet = params.get("sheet", 0)  # For Excel
    delimiter = params.get("delimiter", ",")  # For CSV
    
    ctx.log(f"File read {path}")
    
    return _source_result(
        {"_pending": True, "_path": path},
        {
            "type": "file",
            "path": path,
            "format": data_format,
            "encoding": encoding,
            "sheet": sheet,
            "delimiter": delimiter
        }
    )


@AtomRegistry.register("source", "ftp")
def source_ftp(ctx: PipelineContext, **params) -> Dict:
    """
    Read from FTP/SFTP server
    
    Usage:
        source.ftp(host="ftp.example.com", path="/data/file.csv")
        source.ftp(host="...", path="...", protocol="sftp", user="...", key="...")
    """
    host = params.get("host", params.get("_arg0", ""))
    path = params.get("path", "")
    protocol = params.get("protocol", "ftp")  # ftp, sftp, ftps
    user = params.get("user", "anonymous")
    password = params.get("password", "")
    key = params.get("key", "")  # SSH key for SFTP
    
    ctx.log(f"{protocol.upper()} read {host}{path}")
    
    return _source_result(
        {"_pending": True, "_host": host},
        {
            "type": "ftp",
            "host": host,
            "path": path,
            "protocol": protocol,
            "user": user
        }
    )


# ============================================================
# EXTERNAL APIS
# ============================================================

@AtomRegistry.register("source", "api")
def source_api(ctx: PipelineContext, **params) -> Dict:
    """
    Generic API connector with presets
    
    Usage:
        source.api(provider="openweather", params={"city": "Warsaw"})
        source.api(provider="twitter", endpoint="search", params={"q": "#python"})
    """
    provider = params.get("provider", params.get("_arg0", ""))
    endpoint = params.get("endpoint", "")
    api_params = params.get("params", {})
    api_key = params.get("api_key", "")
    version = params.get("version", "v1")
    
    # API Presets
    presets = {
        "openweather": "https://api.openweathermap.org/data/2.5",
        "twitter": "https://api.twitter.com/2",
        "github": "https://api.github.com",
        "stripe": "https://api.stripe.com/v1",
        "twilio": "https://api.twilio.com",
        "sendgrid": "https://api.sendgrid.com/v3",
        "slack": "https://slack.com/api",
        "discord": "https://discord.com/api/v10",
        "telegram": "https://api.telegram.org",
        "binance": "https://api.binance.com/api/v3",
        "coinbase": "https://api.coinbase.com/v2",
        "alphavantage": "https://www.alphavantage.co/query",
        "polygon": "https://api.polygon.io",
        "newsapi": "https://newsapi.org/v2",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "huggingface": "https://api-inference.huggingface.co",
    }
    
    base_url = presets.get(provider, provider)
    
    ctx.log(f"API call to {provider}/{endpoint}")
    
    return _source_result(
        {"_pending": True, "_provider": provider},
        {
            "type": "api",
            "provider": provider,
            "base_url": base_url,
            "endpoint": endpoint,
            "params": api_params,
            "version": version
        }
    )


@AtomRegistry.register("source", "weather")
def source_weather(ctx: PipelineContext, **params) -> Dict:
    """
    Weather data source
    
    Usage:
        source.weather(location="Warsaw", provider="openweather")
        source.weather(lat=52.23, lon=21.01, forecast=True)
    """
    location = params.get("location", params.get("_arg0", ""))
    lat = params.get("lat", None)
    lon = params.get("lon", None)
    provider = params.get("provider", "openweather")
    forecast = params.get("forecast", False)
    days = params.get("days", 7)
    
    ctx.log(f"Weather data for {location or f'{lat},{lon}'}")
    
    return _source_result(
        {"_pending": True, "_location": location},
        {
            "type": "weather",
            "location": location,
            "lat": lat,
            "lon": lon,
            "provider": provider,
            "forecast": forecast,
            "days": days
        }
    )


@AtomRegistry.register("source", "finance")
def source_finance(ctx: PipelineContext, **params) -> Dict:
    """
    Financial market data
    
    Usage:
        source.finance(symbol="AAPL", provider="alphavantage")
        source.finance(symbols=["BTC", "ETH"], provider="binance", interval="1h")
    """
    symbol = params.get("symbol", params.get("_arg0", ""))
    symbols = params.get("symbols", [symbol] if symbol else [])
    provider = params.get("provider", "alphavantage")
    interval = params.get("interval", "1d")
    data_type = params.get("type", "ohlcv")  # ohlcv, quote, trades, orderbook
    
    ctx.log(f"Finance data for {symbols}")
    
    return _source_result(
        {"_pending": True, "_symbols": symbols},
        {
            "type": "finance",
            "symbols": symbols,
            "provider": provider,
            "interval": interval,
            "data_type": data_type
        }
    )


@AtomRegistry.register("source", "social")
def source_social(ctx: PipelineContext, **params) -> Dict:
    """
    Social media data
    
    Usage:
        source.social(platform="twitter", query="#AI", limit=100)
        source.social(platform="reddit", subreddit="python")
    """
    platform = params.get("platform", params.get("_arg0", ""))
    query = params.get("query", "")
    subreddit = params.get("subreddit", "")
    user = params.get("user", "")
    limit = params.get("limit", 100)
    
    ctx.log(f"Social data from {platform}")
    
    return _source_result(
        {"_pending": True, "_platform": platform},
        {
            "type": "social",
            "platform": platform,
            "query": query,
            "subreddit": subreddit,
            "user": user,
            "limit": limit
        }
    )


@AtomRegistry.register("source", "blockchain")
def source_blockchain(ctx: PipelineContext, **params) -> Dict:
    """
    Blockchain data
    
    Usage:
        source.blockchain(chain="ethereum", address="0x...")
        source.blockchain(chain="bitcoin", type="blocks", limit=10)
    """
    chain = params.get("chain", params.get("_arg0", "ethereum"))
    address = params.get("address", "")
    contract = params.get("contract", "")
    data_type = params.get("type", "transactions")  # transactions, blocks, tokens, nft
    limit = params.get("limit", 100)
    
    ctx.log(f"Blockchain data from {chain}")
    
    return _source_result(
        {"_pending": True, "_chain": chain},
        {
            "type": "blockchain",
            "chain": chain,
            "address": address,
            "contract": contract,
            "data_type": data_type,
            "limit": limit
        }
    )


@AtomRegistry.register("source", "rpc")
def source_rpc(ctx: PipelineContext, **params) -> Dict:
    """
    JSON-RPC / gRPC call
    
    Usage:
        source.rpc(url="http://localhost:8545", method="eth_blockNumber")
        source.rpc(url="...", method="...", params=[...], protocol="grpc")
    """
    url = params.get("url", params.get("_arg0", ""))
    method = params.get("method", "")
    rpc_params = params.get("params", [])
    protocol = params.get("protocol", "jsonrpc")  # jsonrpc, grpc
    
    ctx.log(f"RPC call {method} to {url}")
    
    return _source_result(
        {"_pending": True, "_method": method},
        {
            "type": "rpc",
            "url": url,
            "method": method,
            "params": rpc_params,
            "protocol": protocol
        }
    )


# ============================================================
# SPECIAL SOURCES
# ============================================================

@AtomRegistry.register("source", "scrape")
def source_scrape(ctx: PipelineContext, **params) -> Dict:
    """
    Web scraping source
    
    Usage:
        source.scrape(url="https://example.com", selector="div.data")
        source.scrape(url="...", selectors={"title": "h1", "price": ".price"})
    """
    url = params.get("url", params.get("_arg0", ""))
    selector = params.get("selector", "")
    selectors = params.get("selectors", {})
    wait = params.get("wait", 0)
    javascript = params.get("js", False)
    
    ctx.log(f"Scrape {url}")
    
    return _source_result(
        {"_pending": True, "_url": url},
        {
            "type": "scrape",
            "url": url,
            "selector": selector,
            "selectors": selectors,
            "wait": wait,
            "javascript": javascript
        }
    )


@AtomRegistry.register("source", "email")
def source_email(ctx: PipelineContext, **params) -> Dict:
    """
    Read emails (IMAP)
    
    Usage:
        source.email(server="imap.gmail.com", folder="INBOX", filter="UNSEEN")
    """
    server = params.get("server", params.get("_arg0", ""))
    folder = params.get("folder", "INBOX")
    email_filter = params.get("filter", "ALL")
    limit = params.get("limit", 50)
    
    ctx.log(f"Email read from {server}/{folder}")
    
    return _source_result(
        {"_pending": True, "_server": server},
        {
            "type": "email",
            "server": server,
            "folder": folder,
            "filter": email_filter,
            "limit": limit
        }
    )


@AtomRegistry.register("source", "calendar")
def source_calendar(ctx: PipelineContext, **params) -> Dict:
    """
    Calendar events source
    
    Usage:
        source.calendar(provider="google", calendar_id="primary")
        source.calendar(url="webcal://...", format="ical")
    """
    provider = params.get("provider", params.get("_arg0", ""))
    calendar_id = params.get("calendar_id", "primary")
    url = params.get("url", "")
    days_ahead = params.get("days", 30)
    
    ctx.log(f"Calendar events from {provider or url}")
    
    return _source_result(
        {"_pending": True, "_provider": provider},
        {
            "type": "calendar",
            "provider": provider,
            "calendar_id": calendar_id,
            "url": url,
            "days_ahead": days_ahead
        }
    )
