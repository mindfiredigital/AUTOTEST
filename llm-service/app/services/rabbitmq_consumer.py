import asyncio
import json
import logging
from typing import Callable, Dict, Any
import aio_pika
from aio_pika import IncomingMessage
from app.config.setting import settings

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """RabbitMQ Consumer service for processing messages"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, queue_name: str, handler: Callable):
        """
        Register a handler function for a specific queue

        Args:
            queue_name: Name of the queue to handle
            handler: Async function to process messages
        """
        self.handlers[queue_name] = handler
        logger.info(f"Registered handler for queue: {queue_name}")

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=30,
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            logger.info("RabbitMQ consumer connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def process_message(
        self, message: IncomingMessage, handler: Callable
    ):
        """
        Process a single message

        Args:
            message: Incoming RabbitMQ message
            handler: Handler function to process the message
        """
        async with message.process():
            try:
                # Decode message
                body = json.loads(message.body.decode())
                logger.info(f"Processing message: {body}")

                # Execute handler
                await handler(body)

                logger.info(f"Message processed successfully")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise

    async def start_consuming(self, queue_name: str):
        """
        Start consuming messages from a specific queue

        Args:
            queue_name: Name of the queue to consume from
        """
        if queue_name not in self.handlers:
            raise ValueError(f"No handler registered for queue: {queue_name}")

        handler = self.handlers[queue_name]
        print(f"handler '{handler}'")

        # Declare queue
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-max-priority": 10}
        )
        print(f"queue '{queue}'")

        logger.info(f"Started consuming from queue: {queue_name}")

        # Start consuming
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self.process_message(message, handler)

    async def consume_all(self):
        """Start consuming from all registered queues"""
        if not self.handlers:
            logger.warning("No handlers registered")
            return

        await self.connect()

        # Create tasks for all queues
        tasks = [
            asyncio.create_task(self.start_consuming(queue_name))
            for queue_name in self.handlers.keys()
        ]

        logger.info(f"Consuming from {len(tasks)} queues")
        print(f"Consuming from {len(tasks)} queues")

        # Wait for all tasks
        await asyncio.gather(*tasks)

    async def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("RabbitMQ consumer connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ consumer connection: {e}")


# Global consumer instance
rabbitmq_consumer = RabbitMQConsumer()
