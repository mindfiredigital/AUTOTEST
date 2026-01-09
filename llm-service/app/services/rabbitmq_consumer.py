import asyncio
import json
from app.config.logger import logger


class RabbitMQConsumer:
    def __init__(self, channel_pool):
        self.channel_pool = channel_pool
        self.handlers = {}
        self._stop_event = asyncio.Event()

    def register_handler(self, queue_name: str, handler):
        self.handlers[queue_name] = handler
        logger.info(f"Registered handler for queue: {queue_name}")

    async def consume_queue(self, queue_name: str):
        handler = self.handlers[queue_name]

        while not self._stop_event.is_set():
            try:
                logger.info(f"Starting consumer for queue: {queue_name}")

                async with self.channel_pool.acquire() as channel:
                    queue = await channel.declare_queue(
                        queue_name,
                        durable=True,
                        arguments={"x-max-priority": 10},
                    )

                    async for message in queue.iterator():
                        if self._stop_event.is_set():
                            logger.info(
                                f"[CONSUMER] Stop signal received for {queue_name}"
                            )
                            return

                        try:
                            async with message.process():
                                body = json.loads(message.body.decode())

                                logger.info(
                                    f"[CONSUMER] Message received on {queue_name}: {body}"
                                )

                                await handler(body)

                        except Exception:
                            logger.exception(
                                f"[CONSUMER] Error processing message on {queue_name}"
                            )

            except Exception:
                logger.exception(
                    f"[CONSUMER] Connection lost for {queue_name}. Retrying in 5 seconds..."
                )
                await asyncio.sleep(5)

    async def consume_all(self):
        logger.info("RabbitMQ consumer started")

        tasks = [
            asyncio.create_task(self.consume_queue(queue))
            for queue in self.handlers
        ]

        for task in tasks:
            task.add_done_callback(
                lambda t: logger.exception(t.exception())
                if t.exception()
                else None
            )

        await asyncio.gather(*tasks)

    async def stop(self):
        logger.info("Stopping RabbitMQ consumers...")
        self._stop_event.set()
