"""
ANALYTICA DSL - Data Sink Atoms
================================
Multiplatform data output connectors for DSL pipelines.

Supports output to:
- Web: HTTP/REST, GraphQL, WebSocket
- IoT: MQTT, CoAP, AMQP
- Databases: SQL, MongoDB, Redis, Elasticsearch
- Cloud: AWS S3, Azure Blob, GCP Storage
- Streaming: Kafka, RabbitMQ
- Files: CSV, JSON, XML, Parquet, Excel
- Notifications: Email, SMS, Push, Slack, Discord
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.parser import AtomRegistry, PipelineContext


def _sink_result(data: Any, metadata: Dict) -> Dict:
    """Wrap sink result with metadata"""
    return {
        "data": data,
        "sink": metadata,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "queued"
    }


# ============================================================
# WEB OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "http")
def sink_http(ctx: PipelineContext, **params) -> Dict:
    """
    Send data via HTTP/REST
    
    Usage:
        sink.http(url="https://api.example.com/data", method="POST")
    """
    data = ctx.get_data()
    url = params.get("url", params.get("_arg0", ""))
    method = params.get("method", "POST")
    headers = params.get("headers", {"Content-Type": "application/json"})
    
    ctx.log(f"HTTP {method} to {url}")
    
    return _sink_result(data, {
        "type": "http",
        "url": url,
        "method": method,
        "headers": headers
    })


@AtomRegistry.register("sink", "webhook")
def sink_webhook(ctx: PipelineContext, **params) -> Dict:
    """
    Send to webhook
    
    Usage:
        sink.webhook(url="https://hooks.example.com/...", format="json")
    """
    data = ctx.get_data()
    url = params.get("url", params.get("_arg0", ""))
    data_format = params.get("format", "json")
    secret = params.get("secret", "")
    
    ctx.log(f"Webhook to {url}")
    
    return _sink_result(data, {
        "type": "webhook",
        "url": url,
        "format": data_format,
        "signed": bool(secret)
    })


@AtomRegistry.register("sink", "websocket")
def sink_websocket(ctx: PipelineContext, **params) -> Dict:
    """
    Send via WebSocket
    
    Usage:
        sink.websocket(url="wss://stream.example.com", channel="updates")
    """
    data = ctx.get_data()
    url = params.get("url", params.get("_arg0", ""))
    channel = params.get("channel", "")
    
    ctx.log(f"WebSocket send to {url}")
    
    return _sink_result(data, {
        "type": "websocket",
        "url": url,
        "channel": channel
    })


# ============================================================
# IOT OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "mqtt")
def sink_mqtt(ctx: PipelineContext, **params) -> Dict:
    """
    Publish to MQTT broker
    
    Usage:
        sink.mqtt(broker="mqtt://localhost:1883", topic="sensors/output")
    """
    data = ctx.get_data()
    broker = params.get("broker", params.get("_arg0", ""))
    topic = params.get("topic", "")
    qos = params.get("qos", 0)
    retain = params.get("retain", False)
    
    ctx.log(f"MQTT publish to {broker} topic={topic}")
    
    return _sink_result(data, {
        "type": "mqtt",
        "broker": broker,
        "topic": topic,
        "qos": qos,
        "retain": retain
    })


@AtomRegistry.register("sink", "modbus")
def sink_modbus(ctx: PipelineContext, **params) -> Dict:
    """
    Write to Modbus device
    
    Usage:
        sink.modbus(host="192.168.1.100", unit=1, register=100)
    """
    data = ctx.get_data()
    host = params.get("host", params.get("_arg0", ""))
    port = params.get("port", 502)
    unit = params.get("unit", 1)
    register = params.get("register", 0)
    
    ctx.log(f"Modbus write to {host}:{port}")
    
    return _sink_result(data, {
        "type": "modbus",
        "host": host,
        "port": port,
        "unit": unit,
        "register": register
    })


# ============================================================
# DATABASE OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "sql")
def sink_sql(ctx: PipelineContext, **params) -> Dict:
    """
    Insert/Update SQL database
    
    Usage:
        sink.sql(dsn="postgresql://...", table="results", mode="insert")
    """
    data = ctx.get_data()
    dsn = params.get("dsn", params.get("_arg0", ""))
    table = params.get("table", "")
    mode = params.get("mode", "insert")  # insert, upsert, replace
    
    ctx.log(f"SQL {mode} to {table}")
    
    return _sink_result(data, {
        "type": "sql",
        "dsn": dsn,
        "table": table,
        "mode": mode
    })


@AtomRegistry.register("sink", "mongodb")
def sink_mongodb(ctx: PipelineContext, **params) -> Dict:
    """
    Insert to MongoDB
    
    Usage:
        sink.mongodb(uri="mongodb://...", collection="results")
    """
    data = ctx.get_data()
    uri = params.get("uri", params.get("_arg0", ""))
    collection = params.get("collection", "")
    mode = params.get("mode", "insert")  # insert, upsert, replace
    
    ctx.log(f"MongoDB {mode} to {collection}")
    
    return _sink_result(data, {
        "type": "mongodb",
        "uri": uri,
        "collection": collection,
        "mode": mode
    })


@AtomRegistry.register("sink", "redis")
def sink_redis(ctx: PipelineContext, **params) -> Dict:
    """
    Write to Redis
    
    Usage:
        sink.redis(url="redis://localhost", key="result", ttl=3600)
    """
    data = ctx.get_data()
    url = params.get("url", params.get("_arg0", ""))
    key = params.get("key", "")
    ttl = params.get("ttl", None)
    data_type = params.get("type", "string")
    
    ctx.log(f"Redis write to {key}")
    
    return _sink_result(data, {
        "type": "redis",
        "url": url,
        "key": key,
        "ttl": ttl,
        "data_type": data_type
    })


@AtomRegistry.register("sink", "elasticsearch")
def sink_elasticsearch(ctx: PipelineContext, **params) -> Dict:
    """
    Index to Elasticsearch
    
    Usage:
        sink.elasticsearch(url="http://localhost:9200", index="results")
    """
    data = ctx.get_data()
    url = params.get("url", params.get("_arg0", ""))
    index = params.get("index", "")
    
    ctx.log(f"Elasticsearch index to {index}")
    
    return _sink_result(data, {
        "type": "elasticsearch",
        "url": url,
        "index": index
    })


@AtomRegistry.register("sink", "influxdb")
def sink_influxdb(ctx: PipelineContext, **params) -> Dict:
    """
    Write to InfluxDB
    
    Usage:
        sink.influxdb(url="http://localhost:8086", bucket="metrics", measurement="sensor")
    """
    data = ctx.get_data()
    url = params.get("url", params.get("_arg0", ""))
    bucket = params.get("bucket", "")
    measurement = params.get("measurement", "")
    
    ctx.log(f"InfluxDB write to {bucket}/{measurement}")
    
    return _sink_result(data, {
        "type": "influxdb",
        "url": url,
        "bucket": bucket,
        "measurement": measurement
    })


# ============================================================
# CLOUD STORAGE OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "s3")
def sink_s3(ctx: PipelineContext, **params) -> Dict:
    """
    Upload to AWS S3
    
    Usage:
        sink.s3(bucket="my-bucket", key="output/data.json", format="json")
    """
    data = ctx.get_data()
    bucket = params.get("bucket", params.get("_arg0", ""))
    key = params.get("key", "")
    data_format = params.get("format", "json")
    
    ctx.log(f"S3 upload to s3://{bucket}/{key}")
    
    return _sink_result(data, {
        "type": "s3",
        "bucket": bucket,
        "key": key,
        "format": data_format
    })


@AtomRegistry.register("sink", "azure_blob")
def sink_azure_blob(ctx: PipelineContext, **params) -> Dict:
    """
    Upload to Azure Blob Storage
    """
    data = ctx.get_data()
    container = params.get("container", params.get("_arg0", ""))
    blob = params.get("blob", "")
    
    ctx.log(f"Azure Blob upload to {container}/{blob}")
    
    return _sink_result(data, {
        "type": "azure_blob",
        "container": container,
        "blob": blob
    })


@AtomRegistry.register("sink", "gcs")
def sink_gcs(ctx: PipelineContext, **params) -> Dict:
    """
    Upload to Google Cloud Storage
    """
    data = ctx.get_data()
    bucket = params.get("bucket", params.get("_arg0", ""))
    obj = params.get("object", "")
    
    ctx.log(f"GCS upload to gs://{bucket}/{obj}")
    
    return _sink_result(data, {
        "type": "gcs",
        "bucket": bucket,
        "object": obj
    })


# ============================================================
# STREAMING OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "kafka")
def sink_kafka(ctx: PipelineContext, **params) -> Dict:
    """
    Produce to Kafka topic
    
    Usage:
        sink.kafka(brokers="localhost:9092", topic="events")
    """
    data = ctx.get_data()
    brokers = params.get("brokers", params.get("_arg0", ""))
    topic = params.get("topic", "")
    key = params.get("key", None)
    
    ctx.log(f"Kafka produce to {topic}")
    
    return _sink_result(data, {
        "type": "kafka",
        "brokers": brokers,
        "topic": topic,
        "key": key
    })


# ============================================================
# FILE OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "file")
def sink_file(ctx: PipelineContext, **params) -> Dict:
    """
    Write to local file
    
    Usage:
        sink.file(path="/output/data.csv", format="csv")
    """
    data = ctx.get_data()
    path = params.get("path", params.get("_arg0", ""))
    data_format = params.get("format", "json")
    append = params.get("append", False)
    
    ctx.log(f"File write to {path}")
    
    return _sink_result(data, {
        "type": "file",
        "path": path,
        "format": data_format,
        "append": append
    })


# ============================================================
# NOTIFICATION OUTPUTS
# ============================================================

@AtomRegistry.register("sink", "email")
def sink_email(ctx: PipelineContext, **params) -> Dict:
    """
    Send email notification
    
    Usage:
        sink.email(to="user@example.com", subject="Report", template="report")
    """
    data = ctx.get_data()
    to = params.get("to", params.get("_arg0", ""))
    subject = params.get("subject", "")
    template = params.get("template", "")
    
    ctx.log(f"Email to {to}")
    
    return _sink_result(data, {
        "type": "email",
        "to": to,
        "subject": subject,
        "template": template
    })


@AtomRegistry.register("sink", "sms")
def sink_sms(ctx: PipelineContext, **params) -> Dict:
    """
    Send SMS notification
    
    Usage:
        sink.sms(to="+48123456789", message="Alert: {value}")
    """
    data = ctx.get_data()
    to = params.get("to", params.get("_arg0", ""))
    message = params.get("message", "")
    provider = params.get("provider", "twilio")
    
    ctx.log(f"SMS to {to}")
    
    return _sink_result(data, {
        "type": "sms",
        "to": to,
        "message": message,
        "provider": provider
    })


@AtomRegistry.register("sink", "slack")
def sink_slack(ctx: PipelineContext, **params) -> Dict:
    """
    Send to Slack
    
    Usage:
        sink.slack(channel="#alerts", message="Alert triggered")
        sink.slack(webhook="https://hooks.slack.com/...")
    """
    data = ctx.get_data()
    channel = params.get("channel", params.get("_arg0", ""))
    message = params.get("message", "")
    webhook = params.get("webhook", "")
    
    ctx.log(f"Slack to {channel}")
    
    return _sink_result(data, {
        "type": "slack",
        "channel": channel,
        "message": message,
        "webhook": webhook
    })


@AtomRegistry.register("sink", "discord")
def sink_discord(ctx: PipelineContext, **params) -> Dict:
    """
    Send to Discord
    
    Usage:
        sink.discord(webhook="https://discord.com/api/webhooks/...")
    """
    data = ctx.get_data()
    webhook = params.get("webhook", params.get("_arg0", ""))
    message = params.get("message", "")
    
    ctx.log(f"Discord webhook")
    
    return _sink_result(data, {
        "type": "discord",
        "webhook": webhook,
        "message": message
    })


@AtomRegistry.register("sink", "telegram")
def sink_telegram(ctx: PipelineContext, **params) -> Dict:
    """
    Send to Telegram
    
    Usage:
        sink.telegram(chat_id="123456789", message="Alert!")
    """
    data = ctx.get_data()
    chat_id = params.get("chat_id", params.get("_arg0", ""))
    message = params.get("message", "")
    
    ctx.log(f"Telegram to {chat_id}")
    
    return _sink_result(data, {
        "type": "telegram",
        "chat_id": chat_id,
        "message": message
    })


@AtomRegistry.register("sink", "push")
def sink_push(ctx: PipelineContext, **params) -> Dict:
    """
    Send push notification
    
    Usage:
        sink.push(provider="firebase", topic="alerts", title="Alert", body="...")
    """
    data = ctx.get_data()
    provider = params.get("provider", "firebase")
    topic = params.get("topic", "")
    token = params.get("token", "")
    title = params.get("title", "")
    body = params.get("body", "")
    
    ctx.log(f"Push notification via {provider}")
    
    return _sink_result(data, {
        "type": "push",
        "provider": provider,
        "topic": topic,
        "token": token,
        "title": title,
        "body": body
    })


# ============================================================
# DISPLAY OUTPUTS (for IoT displays, dashboards)
# ============================================================

@AtomRegistry.register("sink", "display")
def sink_display(ctx: PipelineContext, **params) -> Dict:
    """
    Send to display device
    
    Usage:
        sink.display(device="lcd-01", type="text", content="{value}")
        sink.display(device="led-matrix", type="gauge", value=75)
    """
    data = ctx.get_data()
    device = params.get("device", params.get("_arg0", ""))
    display_type = params.get("type", "text")
    content = params.get("content", "")
    
    ctx.log(f"Display output to {device}")
    
    return _sink_result(data, {
        "type": "display",
        "device": device,
        "display_type": display_type,
        "content": content
    })


@AtomRegistry.register("sink", "dashboard")
def sink_dashboard(ctx: PipelineContext, **params) -> Dict:
    """
    Push to real-time dashboard
    
    Usage:
        sink.dashboard(id="main", widget="chart-1")
    """
    data = ctx.get_data()
    dashboard_id = params.get("id", params.get("_arg0", ""))
    widget = params.get("widget", "")
    
    ctx.log(f"Dashboard update {dashboard_id}/{widget}")
    
    return _sink_result(data, {
        "type": "dashboard",
        "dashboard_id": dashboard_id,
        "widget": widget
    })
