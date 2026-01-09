import asyncio
import signal

from aiormq import AMQPConnectionError
from app.config.rabbitmq import rabbitmq_connection
from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.config.logger import logger
from app.workers.queue_router import QUEUE_HANDLER_MAP

shutdown_event = asyncio.Event()


def shutdown():
    logger.info("Shutdown signal received")
    shutdown_event.set()


async def main():
    logger.info("Starting RabbitMQ Worker...")

    loop = asyncio.get_running_loop()

    # Signal handling (safe for Linux / Docker)
    try:
        loop.add_signal_handler(signal.SIGTERM, shutdown)
        loop.add_signal_handler(signal.SIGINT, shutdown)
    except NotImplementedError:
        logger.warning("Signal handlers not supported on this platform")

    # ---- RabbitMQ connection retry ----
    for attempt in range(1, 11):
        try:
            await rabbitmq_connection.connect()
            logger.info("RabbitMQ connected")
            break
        except AMQPConnectionError:
            logger.warning(f"RabbitMQ not ready, retry {attempt}/10")
            await asyncio.sleep(2)
    else:
        logger.error("RabbitMQ connection failed after retries")
        return

    # ---- Consumer setup ----
    consumer = RabbitMQConsumer(rabbitmq_connection.channel_pool)

    for queue_name, handler in QUEUE_HANDLER_MAP.items():
        consumer.register_handler(queue_name, handler)

    consumer_task = asyncio.create_task(consumer.consume_all())
    logger.info("RabbitMQ consumer started")

    # Log if consumer crashes
    consumer_task.add_done_callback(
        lambda t: logger.exception(t.exception())
        if t.exception()
        else None
    )

    # ---- Wait for shutdown ----
    await shutdown_event.wait()

    logger.info("Stopping worker...")

    await consumer.stop()

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled")

    await rabbitmq_connection.close()
    logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
