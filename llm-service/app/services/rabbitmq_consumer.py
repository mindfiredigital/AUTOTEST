import asyncio
import json
from app.config.logger import logger
from aio_pika.exceptions import AMQPConnectionError

class RabbitMQConsumer:
    def __init__(self, channel_pool):
        self.channel_pool = channel_pool
        self.handlers = {}
        self._stop_event = asyncio.Event()

    def register_handler(self, queue_name, handler):
        self.handlers[queue_name] = handler
        logger.info(f"Registered handler for queue: {queue_name}")

    async def start_consuming_with_retry(self, queue_name, retries=10, delay=2):
        """Consume messages with retry if RabbitMQ is not ready."""
        for attempt in range(1, retries + 1):
            try:
                await self._consume_queue(queue_name)
                return
            except AMQPConnectionError:
                logger.warning(f"RabbitMQ not ready for queue '{queue_name}', retry {attempt}/{retries}...")
                await asyncio.sleep(delay)
        logger.error(f"Failed to connect to queue '{queue_name}' after {retries} retries.")

    async def _consume_queue(self, queue_name):
        handler = self.handlers[queue_name]
        logger.info(f"Starting consumer for queue: {queue_name}")

        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(queue_name, durable=True, arguments={"x-max-priority": 10})
            logger.info(f"Consuming from queue: {queue_name}")

            async for message in queue.iterator():
                if self._stop_event.is_set():
                    break
                async with message.process():
                    body = json.loads(message.body.decode())
                    await handler(body)

    async def consume_all(self):
        tasks = [
            asyncio.create_task(self.start_consuming_with_retry(queue))
            for queue in self.handlers
        ]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Gracefully stop all consumers."""
        self._stop_event.set()
