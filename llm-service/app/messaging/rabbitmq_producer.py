"""Helper to publish messages to RabbitMQ using the shared channel pool.

Provides a small, explicit publisher that ensures a connection is available
and publishes JSON-encoded persistent messages with optional priority.
"""

import json
from aio_pika import Message, DeliveryMode
from app.config.rabbitmq import rabbitmq_connection
from app.config.logger import logger


class RabbitMQProducer:
    """Publish messages to named queues via the app's channel pool."""

    @staticmethod
    async def publish_message(queue_name: str, message, priority: int = 0) -> None:
        """Publish `message` (JSON) to `queue_name` with optional `priority`.

        Ensures the shared `rabbitmq_connection` is connected, declares the
        target queue (idempotent), and publishes a persistent message to the
        default exchange using the queue name as the routing key.
        """

        # Ensure connection/pools are established before publishing
        if not rabbitmq_connection.channel_pool:
            await rabbitmq_connection.connect()

        # Acquire a short-lived channel from the pool and publish
        async with rabbitmq_connection.channel_pool.acquire() as channel:
            # Declare the queue to ensure it exists; idempotent operation
            await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={"x-max-priority": 10},
            )

            msg = Message(
                json.dumps(message).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=priority,
                content_type="application/json",
            )

            # Publish to the default exchange using the queue name as routing key
            await channel.default_exchange.publish(msg, routing_key=queue_name)

            logger.info(f"[PRODUCER] Published to {queue_name}: {message}")


rabbitmq_producer = RabbitMQProducer()
