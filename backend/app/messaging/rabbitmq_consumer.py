"""Simple RabbitMQ consumer helpers using a pooled channel.

Provides `RabbitMQConsumer` which registers handlers per-queue and
consumes messages using a provided `channel_pool` (aio_pika.pool.Pool).
"""

import asyncio
import json
from app.config.logger import logger


class RabbitMQConsumer:
    """Consume messages from registered queues using a channel pool.

    Handlers can be registered with `register_handler(queue_name, handler)`.
    Consumers run until `stop()` is called.
    """

    def __init__(self, channel_pool):
        """Initialize with a `channel_pool` (Pool-like object)."""
        self.channel_pool = channel_pool
        self.handlers = {}
        self._stop_event = asyncio.Event()

    def register_handler(self, queue_name: str, handler):
        """Register an async handler function for a given queue name."""
        self.handlers[queue_name] = handler
        logger.info(f"Registered handler for queue: {queue_name}")

    async def consume_queue(self, queue_name: str):
        """Continuously consume a queue and dispatch messages to its handler.

        Retries on connection errors and acknowledges messages after
        successful handling.
        """

        handler = self.handlers[queue_name]

        while not self._stop_event.is_set():
            try:
                async with self.channel_pool.acquire() as channel:
                    queue = await channel.declare_queue(
                        queue_name,
                        durable=True,
                        arguments={"x-max-priority": 10},
                    )

                    async for message in queue.iterator():
                        try:
                            body = json.loads(message.body.decode())
                            logger.info(f"[CONSUMER] {queue_name} | payload={body}")
                            if not message.channel.is_closed:
                                await message.ack()

                            await handler(body)

                        except Exception:
                            logger.exception(f"[CONSUMER] Error in {queue_name}")

            except Exception:
                logger.exception(
                    f"[CONSUMER] Connection lost for {queue_name}, retrying..."
                )
                await asyncio.sleep(5)

    async def consume_all(self):
        """Start consumers for all registered queues concurrently."""
        tasks = [asyncio.create_task(self.consume_queue(queue)) for queue in self.handlers]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Signal running consumers to stop gracefully."""
        self._stop_event.set()
