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

    async def consume_queue(self, queue_name):
        handler = self.handlers[queue_name]
        logger.info(f"Starting consumer for queue: {queue_name}")

        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={"x-max-priority": 10}
            )

            async for message in queue.iterator():
                if self._stop_event.is_set():
                    break

                async with message.process():
                    body = json.loads(message.body.decode())
                    await handler(body)

    async def consume_all(self):
        await asyncio.gather(
            *(self.consume_queue(q) for q in self.handlers)
        )

    async def stop(self):
        self._stop_event.set()
