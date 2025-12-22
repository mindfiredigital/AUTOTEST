import aio_pika
from aio_pika.pool import Pool
from typing import Optional
import logging
from app.config.setting import settings
from app.config.logger import logger



class RabbitMQConnection:
    def __init__(self):
        self.connection_pool: Optional[Pool] = None
        self.channel_pool: Optional[Pool] = None
        self._connection = None

    async def connect(self):
        """Initialize RabbitMQ connection pools"""
        try:
            async def get_connection():
                return await aio_pika.connect_robust(
                    settings.RABBITMQ_URL,
                    timeout=30,
                )

            self.connection_pool = Pool(get_connection, max_size=10)

            async def get_channel():
                async with self.connection_pool.acquire() as connection:
                    return await connection.channel()

            self.channel_pool = Pool(get_channel, max_size=50)

            logger.info("RabbitMQ connection pools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ connection: {e}")
            raise

    async def close(self):
        """Close RabbitMQ connection pools"""
        try:
            if self.channel_pool:
                await self.channel_pool.close()
            if self.connection_pool:
                await self.connection_pool.close()
            logger.info("RabbitMQ connection pools closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Global RabbitMQ connection instance
rabbitmq_connection = RabbitMQConnection()


async def get_rabbitmq_channel():
    """Dependency to get RabbitMQ channel"""
    if not rabbitmq_connection.channel_pool:
        await rabbitmq_connection.connect()
        logger.info("RabbitMQ connection initialized")
    async with rabbitmq_connection.channel_pool.acquire() as channel:
        yield channel
