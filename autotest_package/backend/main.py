# from fastapi import FastAPI
# import os
# from sqlalchemy import create_engine, text

# app = FastAPI(title="AutoTest FastAPI Backend", version="1.0.0")

# # Database connection
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL) if DATABASE_URL else None

# @app.get("/")
# async def root():
#     return {"message": "FastAPI Backend is running!"}

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "database_url": DATABASE_URL}

# @app.get("/db-test")
# async def test_database():
#     if not engine:
#         return {"error": "Database URL not configured"}
    
#     try:
#         with engine.connect() as connection:
#             result = connection.execute(text("SELECT 1"))
#             return {"database": "connected", "test_query": "success"}
#     except Exception as e:
#         return {"database": "connection_failed", "error": str(e)}


from fastapi import FastAPI, HTTPException, BackgroundTasks
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, inspect
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import pika
import json
from typing import Dict, Any, Optional
import asyncio
import aio_pika
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoTest FastAPI Backend", version="1.0.0")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True) if DATABASE_URL else None

# RabbitMQ connection
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

# Pydantic models
class QueueCreateRequest(BaseModel):
    queue_name: str
    durable: bool = True
    auto_delete: bool = False
    arguments: Optional[Dict[str, Any]] = None

class MessageRequest(BaseModel):
    message: Dict[Any, Any]
    routing_key: str = ""
    exchange: str = ""
    persistent: bool = True

class ConsumeRequest(BaseModel):
    queue_name: str
    max_messages: int = 10
    auto_ack: bool = False

@app.get("/")
async def root():
    return {"message": "FastAPI Backend is running!", "database_url": DATABASE_URL, "rabbitmq_url": RABBITMQ_URL}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "database_url": DATABASE_URL,
        "rabbitmq_url": RABBITMQ_URL,
        "timestamp": datetime.now().isoformat()
    }

# RabbitMQ connection test
@app.get("/rabbitmq-test")
async def test_rabbitmq():
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Test queue creation
        test_queue = "test_queue"
        channel.queue_declare(queue=test_queue, durable=True)
        
        # Send a test message
        test_message = {
            "message": "RabbitMQ connection test",
            "timestamp": datetime.now().isoformat()
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=test_queue,
            body=json.dumps(test_message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        
        connection.close()
        
        return {
            "rabbitmq": "connected",
            "test": "success",
            "queue": test_queue,
            "message_sent": test_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RabbitMQ connection failed: {str(e)}")

@app.post("/send-message")
async def send_message(queue_name: str, message: Dict[Any, Any]):
    """Send a message to a RabbitMQ queue"""
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Add timestamp to message
        message_with_timestamp = {
            **message,
            "timestamp": datetime.now().isoformat(),
            "sent_from": "fastapi_backend"
        }
        
        # Send message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message_with_timestamp),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        connection.close()
        
        return {
            "status": "success",
            "queue": queue_name,
            "message_sent": message_with_timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.get("/queue-info/{queue_name}")
async def get_queue_info(queue_name: str):
    """Get information about a RabbitMQ queue"""
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Get queue information
        method = channel.queue_declare(queue=queue_name, durable=True, passive=True)
        message_count = method.method.message_count
        consumer_count = method.method.consumer_count
        
        connection.close()
        
        return {
            "queue_name": queue_name,
            "message_count": message_count,
            "consumer_count": consumer_count,
            "status": "active"
        }
        
    except Exception as e:
        return {
            "queue_name": queue_name,
            "error": str(e),
            "status": "error"
        }

@app.get("/db-test")
async def test_database():
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            return {
                "database": "connected", 
                "test_query": "success",
                "test_value": test_value,
                "database_name": "AutoTestDB"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.post("/initialize-database")
async def initialize_database():
    """Initialize database and create example tables to confirm connection"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            
            try:
                # Create users table
                create_users_table = text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """)
                connection.execute(create_users_table)
                
                # Create products table
                create_products_table = text("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL,
                    stock_quantity INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """)
                connection.execute(create_products_table)
                
                # Insert sample data
                insert_sample_users = text("""
                INSERT IGNORE INTO users (name, email) VALUES 
                ('John Doe', 'john.doe@example.com'),
                ('Jane Smith', 'jane.smith@example.com'),
                ('Mike Johnson', 'mike.johnson@example.com')
                """)
                connection.execute(insert_sample_users)
                
                insert_sample_products = text("""
                INSERT IGNORE INTO products (name, description, price, stock_quantity) VALUES 
                ('Laptop', 'High-performance laptop for development', 999.99, 10),
                ('Mouse', 'Wireless optical mouse', 29.99, 50),
                ('Keyboard', 'Mechanical keyboard with RGB lighting', 79.99, 25)
                """)
                connection.execute(insert_sample_products)
                
                # Commit the transaction
                trans.commit()
                
                return {
                    "status": "success",
                    "message": "Database initialized successfully",
                    "tables_created": ["users", "products"],
                    "sample_data": "inserted",
                    "database": "AutoTestDB"
                }
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/tables")
async def list_tables():
    """List all tables in the database"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_info = {}
        for table in tables:
            columns = inspector.get_columns(table)
            table_info[table] = [col['name'] for col in columns]
        
        return {
            "database": "AutoTestDB",
            "total_tables": len(tables),
            "tables": table_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tables: {str(e)}")

@app.get("/users")
async def get_users():
    """Get all users from the users table"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users"))
            users = []
            for row in result:
                users.append({
                    "id": row.id,
                    "name": row.name,
                    "email": row.email,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })
            
            return {
                "database": "AutoTestDB",
                "total_users": len(users),
                "users": users
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.get("/products")
async def get_products():
    """Get all products from the products table"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM products"))
            products = []
            for row in result:
                products.append({
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "price": float(row.price) if row.price else None,
                    "stock_quantity": row.stock_quantity,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })
            
            return {
                "database": "AutoTestDB",
                "total_products": len(products),
                "products": products
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@app.delete("/reset-database")
async def reset_database():
    """Reset database by dropping and recreating tables (use with caution!)"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                # Drop tables if they exist
                connection.execute(text("DROP TABLE IF EXISTS products"))
                connection.execute(text("DROP TABLE IF EXISTS users"))
                
                trans.commit()
                
                return {
                    "status": "success",
                    "message": "Database reset successfully",
                    "action": "All tables dropped",
                    "database": "AutoTestDB"
                }
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")
    
@app.post("/create-queue")
async def create_or_get_queue(request: QueueCreateRequest):
    """Create a new queue or get existing queue information"""
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Check if queue exists by trying to declare it passively
        queue_exists = False
        try:
            method = channel.queue_declare(
                queue=request.queue_name, 
                passive=True  # This will raise an exception if queue doesn't exist
            )
            queue_exists = True
            existing_message_count = method.method.message_count
            existing_consumer_count = method.method.consumer_count
        except pika.exceptions.ChannelClosedByBroker:
            # Queue doesn't exist, need to recreate connection and channel
            connection.close()
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            queue_exists = False
        
        if queue_exists:
            connection.close()
            return {
                "status": "exists",
                "queue_name": request.queue_name,
                "message": f"Queue '{request.queue_name}' already exists",
                "message_count": existing_message_count,
                "consumer_count": existing_consumer_count,
                "durable": True  # Existing queues are assumed durable
            }
        else:
            # Create new queue
            method = channel.queue_declare(
                queue=request.queue_name,
                durable=request.durable,
                auto_delete=request.auto_delete,
                arguments=request.arguments or {}
            )
            
            connection.close()
            
            return {
                "status": "created",
                "queue_name": request.queue_name,
                "message": f"Queue '{request.queue_name}' created successfully",
                "durable": request.durable,
                "auto_delete": request.auto_delete,
                "arguments": request.arguments,
                "message_count": 0,
                "consumer_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error creating/checking queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create/check queue: {str(e)}")
    
# @app.post("/consume-messages")
# async def consume_messages(request: ConsumeRequest):
#     """Consume messages from a queue"""
#     if not RABBITMQ_URL:
#         raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
#     try:
#         connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
#         channel = connection.channel()
        
#         # Check if queue exists
#         try:
#             method = channel.queue_declare(queue=request.queue_name, passive=True)
#             total_messages = method.method.message_count
#         except pika.exceptions.ChannelClosedByBroker:
#             connection.close()
#             raise HTTPException(status_code=404, detail=f"Queue '{request.queue_name}' does not exist")
        
#         messages = []
#         messages_consumed = 0
        
#         # Consume messages
#         while messages_consumed < request.max_messages:
#             method_frame, header_frame, body = channel.basic_get(
#                 queue=request.queue_name,
#                 auto_ack=request.auto_ack
#             )
            
#             if method_frame is None:
#                 # No more messages
#                 break
                
#             try:
#                 # Try to decode as JSON
#                 message_data = json.loads(body.decode('utf-8'))
#             except (json.JSONDecodeError, UnicodeDecodeError):
#                 # If not JSON, treat as plain text
#                 message_data = body.decode('utf-8', errors='ignore')
            
#             message_info = {
#                 "delivery_tag": method_frame.delivery_tag,
#                 "exchange": method_frame.exchange,
#                 "routing_key": method_frame.routing_key,
#                 "message_count": method_frame.message_count,
#                 "body": message_data,
#                 "properties": {
#                     "content_type": header_frame.content_type,
#                     "delivery_mode": header_frame.delivery_mode,
#                     "timestamp": header_frame.timestamp.isoformat() if header_frame.timestamp else None,
#                     "message_id": header_frame.message_id,
#                     "user_id": header_frame.user_id
#                 },
#                 "consumed_at": datetime.now().isoformat()
#             }
            
#             messages.append(message_info)
#             messages_consumed += 1
            
#             # If auto_ack is False, manually acknowledge the message
#             if not request.auto_ack:
#                 channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        
#         # Get updated queue info
#         final_method = channel.queue_declare(queue=request.queue_name, passive=True)
#         remaining_messages = final_method.method.message_count
        
#         connection.close()
        
#         return {
#             "status": "success",
#             "queue_name": request.queue_name,
#             "messages_consumed": messages_consumed,
#             "messages_before": total_messages,
#             "messages_remaining": remaining_messages,
#             "auto_ack": request.auto_ack,
#             "messages": messages
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error consuming messages: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to consume messages: {str(e)}")
    
@app.post("/consume-messages")
async def consume_messages(request: ConsumeRequest):
    """Consume messages from a queue"""
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Check if queue exists
        try:
            method = channel.queue_declare(queue=request.queue_name, passive=True)
            total_messages = method.method.message_count
        except pika.exceptions.ChannelClosedByBroker:
            connection.close()
            raise HTTPException(status_code=404, detail=f"Queue '{request.queue_name}' does not exist")
        
        messages = []
        messages_consumed = 0
        
        # Consume messages
        while messages_consumed < request.max_messages:
            method_frame, header_frame, body = channel.basic_get(
                queue=request.queue_name,
                auto_ack=request.auto_ack
            )
            
            if method_frame is None:
                # No more messages
                break
                
            try:
                # Try to decode as JSON
                message_data = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON, treat as plain text
                message_data = body.decode('utf-8', errors='ignore')
            
            # Fix timestamp handling
            timestamp_str = None
            if header_frame.timestamp:
                if isinstance(header_frame.timestamp, int):
                    # Convert Unix timestamp to ISO format
                    timestamp_str = datetime.fromtimestamp(header_frame.timestamp).isoformat()
                else:
                    # Assume it's already a datetime object
                    timestamp_str = header_frame.timestamp.isoformat()
            
            message_info = {
                "delivery_tag": method_frame.delivery_tag,
                "exchange": method_frame.exchange,
                "routing_key": method_frame.routing_key,
                "message_count": method_frame.message_count,
                "body": message_data,
                "properties": {
                    "content_type": header_frame.content_type,
                    "delivery_mode": header_frame.delivery_mode,
                    "timestamp": timestamp_str,  # ← Fixed line
                    "message_id": header_frame.message_id,
                    "user_id": header_frame.user_id
                },
                "consumed_at": datetime.now().isoformat()
            }
            
            messages.append(message_info)
            messages_consumed += 1
            
            # If auto_ack is False, manually acknowledge the message
            if not request.auto_ack:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        
        # Get updated queue info
        final_method = channel.queue_declare(queue=request.queue_name, passive=True)
        remaining_messages = final_method.method.message_count
        
        connection.close()
        
        return {
            "status": "success",
            "queue_name": request.queue_name,
            "messages_consumed": messages_consumed,
            "messages_before": total_messages,
            "messages_remaining": remaining_messages,
            "auto_ack": request.auto_ack,
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consuming messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to consume messages: {str(e)}")


import time
from typing import Dict, Any, List, Optional

# Add this new endpoint after your existing consume-messages endpoint
@app.post("/consume-messages-with-delay")
async def consume_messages_with_delay(
    queue_name: str,
    max_messages: int = 2,
    delay_seconds: int = 10,
    auto_ack: bool = False
):
    """
    Consume messages with acknowledgment delay for testing unacknowledged state
    
    Args:
        queue_name: Name of the queue to consume from
        max_messages: Maximum number of messages to consume
        delay_seconds: Seconds to wait before acknowledging messages
        auto_ack: If True, messages are auto-acknowledged (no delay effect)
    """
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Check if queue exists
        try:
            method = channel.queue_declare(queue=queue_name, passive=True)
            total_messages = method.method.message_count
        except pika.exceptions.ChannelClosedByBroker:
            connection.close()
            raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' does not exist")
        
        messages = []
        messages_consumed = 0
        delivery_tags = []  # Store delivery tags for delayed acknowledgment
        
        print(f"🚀 Starting consumption of {max_messages} messages from '{queue_name}'")
        print(f"⏰ Will wait {delay_seconds} seconds before acknowledging")
        
        # Step 1: Consume messages WITHOUT acknowledging them
        while messages_consumed < max_messages:
            method_frame, header_frame, body = channel.basic_get(
                queue=queue_name,
                auto_ack=auto_ack  # Only auto-ack if explicitly requested
            )
            
            if method_frame is None:
                # No more messages available
                print(f"📭 No more messages available after consuming {messages_consumed}")
                break
                
            try:
                # Try to decode as JSON
                message_data = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON, treat as plain text
                message_data = body.decode('utf-8', errors='ignore')
            
            # Fix timestamp handling (same as fixed consume-messages endpoint)
            timestamp_str = None
            if header_frame.timestamp:
                if isinstance(header_frame.timestamp, int):
                    # Convert Unix timestamp to ISO format
                    timestamp_str = datetime.fromtimestamp(header_frame.timestamp).isoformat()
                else:
                    # Assume it's already a datetime object
                    timestamp_str = header_frame.timestamp.isoformat()
            
            message_info = {
                "delivery_tag": method_frame.delivery_tag,
                "exchange": method_frame.exchange,
                "routing_key": method_frame.routing_key,
                "message_count": method_frame.message_count,
                "body": message_data,
                "properties": {
                    "content_type": header_frame.content_type,
                    "delivery_mode": header_frame.delivery_mode,
                    "timestamp": timestamp_str,
                    "message_id": header_frame.message_id,
                    "user_id": header_frame.user_id
                },
                "consumed_at": datetime.now().isoformat()
            }
            
            messages.append(message_info)
            
            # Store delivery tag for later acknowledgment (only if not auto-ack)
            if not auto_ack:
                delivery_tags.append(method_frame.delivery_tag)
            
            messages_consumed += 1
            print(f"✅ Consumed message {messages_consumed}: delivery_tag={method_frame.delivery_tag}")
        
        # At this point: messages are consumed but NOT acknowledged (if auto_ack=False)
        if not auto_ack and delivery_tags:
            print(f"🔍 CHECK NOW! {len(delivery_tags)} messages should be UNACKNOWLEDGED")
            print(f"🕐 Use '/list-queues' endpoint to see messages_unacknowledged count")
            print(f"⏳ Waiting {delay_seconds} seconds before acknowledgment...")
            
            # Wait for the specified delay
            time.sleep(delay_seconds)
            
            print("🔄 Now acknowledging all consumed messages...")
            
            # Step 2: Acknowledge all consumed messages
            for i, delivery_tag in enumerate(delivery_tags, 1):
                channel.basic_ack(delivery_tag=delivery_tag)
                print(f"✅ Acknowledged message {i}/{len(delivery_tags)} (delivery_tag={delivery_tag})")
        
        # Get final queue statistics
        try:
            final_method = channel.queue_declare(queue=queue_name, passive=True)
            remaining_messages = final_method.method.message_count
        except:
            remaining_messages = "unknown"
        
        connection.close()
        
        return {
            "status": "success",
            "queue_name": queue_name,
            "messages_consumed": messages_consumed,
            "messages_before": total_messages,
            "messages_remaining": remaining_messages,
            "auto_ack": auto_ack,
            "delay_seconds": delay_seconds,
            "acknowledgment_method": "immediate" if auto_ack else f"delayed by {delay_seconds}s",
            "messages": messages,
            "testing_note": f"If auto_ack=False, messages were unacknowledged for {delay_seconds} seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in consume-messages-with-delay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to consume messages with delay: {str(e)}")


@app.post("/send-message-to-queue")
async def send_message_to_queue(queue_name: str, request: MessageRequest):
    """Send a message to a specific queue with enhanced options"""
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Ensure queue exists
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Prepare message
        message_with_metadata = {
            **request.message,
            "timestamp": datetime.now().isoformat(),
            "sent_from": "fastapi_backend",
            "queue_name": queue_name
        }
        
        # Set message properties
        properties = pika.BasicProperties(
            delivery_mode=2 if request.persistent else 1,  # 2 = persistent, 1 = transient
            timestamp=int(datetime.now().timestamp()),
            message_id=f"msg_{datetime.now().timestamp()}",
            content_type="application/json"
        )
        
        # Send message
        channel.basic_publish(
            exchange=request.exchange,
            routing_key=request.routing_key or queue_name,
            body=json.dumps(message_with_metadata),
            properties=properties
        )
        
        # Get queue info after sending
        method = channel.queue_declare(queue=queue_name, passive=True)
        message_count = method.method.message_count
        
        connection.close()
        
        return {
            "status": "success",
            "queue_name": queue_name,
            "message_sent": message_with_metadata,
            "persistent": request.persistent,
            "queue_message_count": message_count,
            "sent_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
    
@app.get("/list-queues")
async def list_all_queues():
    """List all queues with their information"""
    if not RABBITMQ_URL:
        raise HTTPException(status_code=500, detail="RabbitMQ URL not configured")
    
    try:
        # Use RabbitMQ Management API through HTTP requests
        import requests
        from urllib.parse import urlparse
        
        # Parse RabbitMQ URL to get credentials
        parsed_url = urlparse(RABBITMQ_URL)
        username = parsed_url.username or "admin"
        password = parsed_url.password or "admin123"
        hostname = "autotest_rabbitmq"  # Container name
        
        # Make API request to management plugin
        response = requests.get(
            f"http://{hostname}:15672/api/queues",
            auth=(username, password),
            timeout=10
        )
        
        if response.status_code == 200:
            queues_data = response.json()
            
            queue_summary = []
            for queue in queues_data:
                queue_summary.append({
                    "name": queue.get("name"),
                    "vhost": queue.get("vhost"),
                    "durable": queue.get("durable"),
                    "auto_delete": queue.get("auto_delete"),
                    "messages": queue.get("messages", 0),
                    "messages_ready": queue.get("messages_ready", 0),
                    "messages_unacknowledged": queue.get("messages_unacknowledged", 0),
                    "consumers": queue.get("consumers", 0),
                    "state": queue.get("state"),
                    "node": queue.get("node")
                })
            
            return {
                "status": "success",
                "total_queues": len(queue_summary),
                "queues": queue_summary
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch queue information from management API")
            
    except requests.RequestException as e:
        logger.error(f"Error fetching queues via API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list queues: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing queues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list queues: {str(e)}")
    
@app.get("/health/rabbitmq")
async def rabbitmq_health():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        connection.close()
        return {"status": "healthy", "service": "rabbitmq"}
    except Exception as e:
        return {"status": "unhealthy", "service": "rabbitmq", "error": str(e)}
    
import threading
import time
from datetime import datetime
from typing import Dict, Any
import uuid

# Global storage for active consumers with proper stop mechanism
active_consumers = {}
consumer_stop_flags = {}  # Flags to signal consumers to stop

class ConsumerManager:
    def __init__(self):
        self.consumers = {}
        self.stop_flags = {}
    
    def create_consumer_id(self, queue_name: str, consumer_name: str) -> str:
        return f"{queue_name}_{consumer_name}_{uuid.uuid4().hex[:8]}"
    
    def add_consumer(self, consumer_id: str, consumer_info: dict):
        self.consumers[consumer_id] = consumer_info
    
    def remove_consumer(self, consumer_id: str):
        if consumer_id in self.consumers:
            del self.consumers[consumer_id]
        if consumer_id in self.stop_flags:
            del self.stop_flags[consumer_id]
    
    def get_consumers(self):
        # Return JSON-serializable data only
        result = {}
        for consumer_id, info in self.consumers.items():
            result[consumer_id] = {
                "queue": info["queue"],
                "name": info["name"], 
                "started_at": info["started_at"],
                "status": info["status"],
                "messages_processed": info.get("messages_processed", 0)
            }
        return result
    
    def stop_consumer(self, consumer_id: str):
        if consumer_id in self.consumers:
            self.consumers[consumer_id]["status"] = "stopping"
            self.stop_flags[consumer_id] = True
            return True
        return False
    
    def should_stop(self, consumer_id: str) -> bool:
        return self.stop_flags.get(consumer_id, False)

# Global consumer manager
consumer_manager = ConsumerManager()

@app.post("/start-consumer")
async def start_persistent_consumer(queue_name: str, consumer_name: str = "default"):
    """Start a persistent consumer that stays connected"""
    
    # Check if consumer already exists for this queue/name combo
    existing_consumer = None
    for consumer_id, info in consumer_manager.consumers.items():
        if info["queue"] == queue_name and info["name"] == consumer_name and info["status"] == "running":
            existing_consumer = consumer_id
            break
    
    if existing_consumer:
        return {
            "status": "already_running",
            "consumer_id": existing_consumer,
            "message": f"Consumer '{consumer_name}' already running for queue '{queue_name}'"
        }
    
    # Create unique consumer ID
    consumer_id = consumer_manager.create_consumer_id(queue_name, consumer_name)
    
    def consumer_worker():
        messages_processed = 0
        connection = None
        channel = None
        
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            
            # Declare queue to ensure it exists
            channel.queue_declare(queue=queue_name, durable=True)
            
            def callback(ch, method, properties, body):
                nonlocal messages_processed
                
                # Check if we should stop
                if consumer_manager.should_stop(consumer_id):
                    print(f"🛑 Consumer '{consumer_name}' received stop signal")
                    ch.stop_consuming()
                    return
                
                try:
                    # Process message
                    message_data = json.loads(body.decode('utf-8'))
                    print(f"🔄 Consumer '{consumer_name}' processing: {message_data}")
                    
                    # Simulate processing time
                    time.sleep(0.5)
                    
                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    messages_processed += 1
                    
                    # Update processed count
                    if consumer_id in consumer_manager.consumers:
                        consumer_manager.consumers[consumer_id]["messages_processed"] = messages_processed
                    
                    print(f"✅ Consumer '{consumer_name}' processed message {messages_processed}")
                    
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Start consuming
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            
            print(f"🚀 Consumer '{consumer_name}' started for queue '{queue_name}'")
            
            # Update status to running
            if consumer_id in consumer_manager.consumers:
                consumer_manager.consumers[consumer_id]["status"] = "running"
            
            # Start consuming (blocking call)
            channel.start_consuming()
            
        except Exception as e:
            print(f"💥 Consumer error: {e}")
            if consumer_id in consumer_manager.consumers:
                consumer_manager.consumers[consumer_id]["status"] = "error"
        finally:
            # Clean shutdown
            print(f"🧹 Cleaning up consumer '{consumer_name}'...")
            
            try:
                if channel and channel.is_open:
                    channel.stop_consuming()
                    channel.close()
                if connection and not connection.is_closed:
                    connection.close()
            except Exception as e:
                print(f"Error during cleanup: {e}")
            
            # Update final status
            if consumer_id in consumer_manager.consumers:
                consumer_manager.consumers[consumer_id]["status"] = "stopped"
                consumer_manager.consumers[consumer_id]["stopped_at"] = datetime.now().isoformat()
            
            print(f"🛑 Consumer '{consumer_name}' stopped (processed {messages_processed} messages)")
    
    # Create consumer info
    consumer_info = {
        "queue": queue_name,
        "name": consumer_name,
        "started_at": datetime.now().isoformat(),
        "status": "starting",
        "messages_processed": 0
    }
    
    # Add to manager
    consumer_manager.add_consumer(consumer_id, consumer_info)
    
    # Start consumer in background thread
    consumer_thread = threading.Thread(target=consumer_worker, daemon=True)
    consumer_thread.start()
    
    return {
        "status": "started",
        "consumer_id": consumer_id,
        "consumer_name": consumer_name,
        "queue_name": queue_name,
        "message": f"Persistent consumer started for queue '{queue_name}'"
    }

@app.post("/stop-consumer")
async def stop_persistent_consumer(queue_name: str, consumer_name: str = "default"):
    """Stop a specific persistent consumer"""
    
    # Find the consumer
    target_consumer_id = None
    for consumer_id, info in consumer_manager.consumers.items():
        if info["queue"] == queue_name and info["name"] == consumer_name and info["status"] in ["running", "starting"]:
            target_consumer_id = consumer_id
            break
    
    if not target_consumer_id:
        raise HTTPException(
            status_code=404, 
            detail=f"No active consumer found for queue '{queue_name}' with name '{consumer_name}'"
        )
    
    # Signal consumer to stop
    success = consumer_manager.stop_consumer(target_consumer_id)
    
    if success:
        return {
            "status": "stopping",
            "consumer_id": target_consumer_id,
            "consumer_name": consumer_name,
            "queue_name": queue_name,
            "message": f"Stop signal sent to consumer '{consumer_name}' for queue '{queue_name}'"
        }
    else:
        raise HTTPException(status_code=404, detail="Consumer not found")

@app.post("/stop-all-consumers")
async def stop_all_consumers():
    """Stop all active consumers"""
    
    stopped_consumers = []
    
    for consumer_id, info in list(consumer_manager.consumers.items()):
        if info["status"] in ["running", "starting"]:
            consumer_manager.stop_consumer(consumer_id)
            stopped_consumers.append({
                "consumer_id": consumer_id,
                "queue": info["queue"],
                "name": info["name"]
            })
    
    return {
        "status": "stopping_all",
        "stopped_count": len(stopped_consumers),
        "stopped_consumers": stopped_consumers,
        "message": f"Stop signal sent to {len(stopped_consumers)} consumers"
    }

@app.get("/active-consumers")
async def list_active_consumers():
    """List all consumers with their status"""
    
    consumers_data = consumer_manager.get_consumers()
    
    # Count by status
    status_counts = {"running": 0, "starting": 0, "stopping": 0, "stopped": 0, "error": 0}
    for info in consumers_data.values():
        status = info.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1
    
    return {
        "total_consumers": len(consumers_data),
        "status_summary": status_counts,
        "consumers": consumers_data
    }

@app.delete("/cleanup-consumers")
async def cleanup_stopped_consumers():
    """Remove stopped/error consumers from the list"""
    
    removed_count = 0
    consumers_to_remove = []
    
    for consumer_id, info in list(consumer_manager.consumers.items()):
        if info["status"] in ["stopped", "error"]:
            consumers_to_remove.append(consumer_id)
    
    for consumer_id in consumers_to_remove:
        consumer_manager.remove_consumer(consumer_id)
        removed_count += 1
    
    return {
        "status": "cleaned",
        "removed_count": removed_count,
        "message": f"Removed {removed_count} stopped/error consumers"
    }




