"""Small wrapper for an aio-pika RabbitMQ connection pool.

Provides a reconnecting `RabbitMQConnection` that exposes connection and
channel Pools. Designed to be started at application startup and closed on
shutdown. Docstrings are intentionally concise for maintainability.
"""

import asyncio
import aio_pika
from aio_pika.pool import Pool
from app.config.setting import settings
from app.config.logger import logger


class RabbitMQConnection:
    """Manage shared connection and channel pools for RabbitMQ.

    Attributes:
        connection_pool: aio_pika.pool.Pool | None
        channel_pool: aio_pika.pool.Pool | None
        _lock: asyncio.Lock -- prevents concurrent connect attempts
    """

    def __init__(self):
        self.connection_pool = None
        self.channel_pool = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish connection and channel pools.

        Uses `connect_robust` and retries until RabbitMQ becomes available.
        The pools wrap a single underlying robust connection and provide
        short-lived channel objects from that connection.
        """

        async with self._lock:
            # If channel_pool exists, another startup already connected.
            if self.channel_pool:
                return

            while True:
                try:
                    logger.info("Connecting to RabbitMQ...")

                    # Create a single robust connection (reconnects internally)
                    connection = await aio_pika.connect_robust(
                        settings.RABBITMQ_URL,
                        heartbeat=120,
                        timeout=30,
                    )

                    # Return the same connection object when the pool requests it.
                    async def get_connection():
                        return connection

                    # Pool for acquiring the shared connection (max 5 concurrent users).
                    self.connection_pool = Pool(get_connection, max_size=5)

                    # Channel factory: acquire the shared connection and open a channel.
                    async def get_channel():
                        async with self.connection_pool.acquire() as conn:
                            return await conn.channel()

                    # Pool of channels for concurrent use (channels are short-lived).
                    self.channel_pool = Pool(get_channel, max_size=20)

                    logger.info("RabbitMQ connected successfully")
                    return

                except Exception as e:
                    # Log and retry after a short delay; useful during container startup.
                    logger.error(f"RabbitMQ not ready: {e}")
                    await asyncio.sleep(5)

    async def close(self) -> None:
        """Close pools and release resources.

        Closing the pools will close underlying channels and the connection.
        After closing, pool attributes are reset to None.
        """

        if self.channel_pool:
            await self.channel_pool.close()
        if self.connection_pool:
            await self.connection_pool.close()

        self.channel_pool = None
        self.connection_pool = None

        logger.info("RabbitMQ connection closed")


rabbitmq_connection = RabbitMQConnection()
