import asyncio
import signal
from app.config.rabbitmq import rabbitmq_connection
from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.workers.worker import worker_service
from app.config.logger import logger
from app.workers.queue_router import QUEUE_HANDLER_MAP
 
shutdown_event = asyncio.Event()
 
 
def shutdown():
    logger.info("Shutdown signal received")
    shutdown_event.set()
 
 
async def main():
    logger.info("Starting RabbitMQ Worker...")
 
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, shutdown)
    loop.add_signal_handler(signal.SIGINT, shutdown)
 
    await rabbitmq_connection.connect()
 
    consumer = RabbitMQConsumer(
        channel_pool=rabbitmq_connection.channel_pool
    )
    for queue_name, handler in QUEUE_HANDLER_MAP.items():
        consumer.register_handler(queue_name, handler)
     
    
 
    consumer_task = asyncio.create_task(consumer.consume_all())
    logger.info("RabbitMQ consumer started")
 
    await shutdown_event.wait()
 
    logger.info("Stopping worker...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
 
    await rabbitmq_connection.close()
    logger.info("Worker stopped")
 
 
if __name__ == "__main__":
    asyncio.run(main())
 