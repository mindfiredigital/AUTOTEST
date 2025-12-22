import json
from typing import Dict, Any, Optional
import aio_pika
from aio_pika import DeliveryMode, Message
from app.config.rabbitmq import rabbitmq_connection
from app.config.logger import logger



class RabbitMQProducer:
    """RabbitMQ Producer service for publishing messages"""

    @staticmethod
    async def publish_message(
        queue_name: str,
        message: Dict[str, Any],
        priority: int = 0,
    ) -> bool:
        try:
            if not rabbitmq_connection.channel_pool:
                await rabbitmq_connection.connect()
                logger.info("RabbitMQ initialized successfully")

            async with rabbitmq_connection.channel_pool.acquire() as channel:
                await channel.declare_queue(
                    queue_name,
                    durable=True,
                    arguments={"x-max-priority": 10},
                )

                message_body = json.dumps(message).encode()

                aio_message = Message(
                    message_body,
                    delivery_mode=DeliveryMode.PERSISTENT,
                    priority=priority,
                    content_type="application/json",
                )

                await channel.default_exchange.publish(
                    aio_message,
                    routing_key=queue_name,
                )

                logger.info(f"Message published to '{queue_name}': {message}")
                return True

        except Exception as e:
            logger.error(f"Failed to publish message to queue '{queue_name}': {e}")
            print(f"Failed to publish message to queue '{queue_name}': {e}")
            return False


    @staticmethod
    async def publish_to_exchange(
        exchange_name: str,
        routing_key: str,
        message: Dict[str, Any],
        exchange_type: str = "topic",
        priority: int = 0,
    ) -> bool:
        """
        Publish a message to an exchange with routing key

        Args:
            exchange_name: Name of the exchange
            routing_key: Routing key for message routing
            message: Dictionary containing message data
            exchange_type: Type of exchange (direct, topic, fanout, headers)
            priority: Message priority

        Returns:
            bool: True if message was published successfully
        """
        try:
            async with rabbitmq_connection.channel_pool.acquire() as channel:
                # Declare exchange
                exchange = await channel.declare_exchange(
                    exchange_name,
                    type=exchange_type,
                    durable=True,
                )

                # Prepare message
                message_body = json.dumps(message).encode()

                aio_message = Message(
                    message_body,
                    delivery_mode=DeliveryMode.PERSISTENT,
                    priority=priority,
                    content_type="application/json",
                )

                # Publish message
                await exchange.publish(
                    aio_message,
                    routing_key=routing_key,
                )

                logger.info(
                    f"Message published to exchange '{exchange_name}' "
                    f"with routing key '{routing_key}': {message}"
                )
                return True

        except Exception as e:
            logger.error(
                f"Failed to publish message to exchange '{exchange_name}': {e}"
            )
            return False


# Singleton instance
rabbitmq_producer = RabbitMQProducer()
