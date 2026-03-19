"""Simple RabbitMQ consumer helper using a channel Pool.

The consumer registers queue handlers and runs per-queue consumption loops.
Docstrings are concise; behavior is preserved (acks, retries, logging).
"""

import asyncio
import json
from app.config.logger import logger


class RabbitMQConsumer:
    """Consume messages from named queues and dispatch to handlers.

    Use `register_handler` to attach an async function for a queue name, then
    run `consume_all` to start consumption for all registered queues.
    """

    def __init__(self, channel_pool):
        # aio_pika.pool.Pool for channels (provided by the app startup)
        self.channel_pool = channel_pool
        # map queue_name -> async handler(callable)
        self.handlers = {}
        # event used to signal stopping the consumers
        self._stop_event = asyncio.Event()

    def register_handler(self, queue_name: str, handler):
        """Register an async handler for `queue_name`.

        Handler should be async and accept a single `body` dict argument.
        """

        self.handlers[queue_name] = handler
        logger.info(f"Registered handler for queue: {queue_name}")

    async def consume_queue(self, queue_name: str):
        """Consume a single queue in a loop; retries on connection errors.

        The loop reads messages, decodes JSON payloads, acknowledges them
        and forwards the payload to the registered handler. On error the
        consumer logs the exception and continues (connection-level errors
        are retried after a short sleep).
        """

        handler = self.handlers[queue_name]

        while not self._stop_event.is_set():
            try:
                # Acquire a short-lived channel from the shared pool
                async with self.channel_pool.acquire() as channel:
                    queue = await channel.declare_queue(
                        queue_name,
                        durable=True,
                        arguments={"x-max-priority": 10},
                    )

                    # Iterate messages as they arrive
                    async for message in queue.iterator():
                        try:
                            body = json.loads(message.body.decode())
                            logger.info(f"[CONSUMER] {queue_name} | payload={body}")

                            # Acknowledge if channel is still open
                            if not message.channel.is_closed:
                                await message.ack()

                            # Dispatch to the user-provided handler
                            await handler(body)

                        except Exception:
                            # Handler or payload processing error
                            logger.exception(f"[CONSUMER] Error in {queue_name}")

            except Exception:
                # Connection-level error (e.g., broker restart). Sleep then retry.
                logger.exception(f"[CONSUMER] Connection lost for {queue_name}, retrying...")
                await asyncio.sleep(5)

    async def consume_all(self):
        """Start consumers for all registered queues concurrently."""

        tasks = [asyncio.create_task(self.consume_queue(queue)) for queue in self.handlers]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Signal consumers to stop on next loop iteration."""

        self._stop_event.set()
