"""
RabbitMQ Worker Service
This worker consumes messages from RabbitMQ queues and processes them asynchronously
"""
from app.services.rabbitmq_consumer import rabbitmq_consumer
from app.workers.handlers import register_all_handlers
from app.config.logger import logger


class WorkerService:
    def __init__(self):
        self.running = False

    async def start(self):
        """Start the worker service"""
        logger.info("Starting RabbitMQ Worker Service...")
        print("Starting RabbitMQ Worker Service...")

        # Register all message handlers
        register_all_handlers(rabbitmq_consumer)

        self.running = True

        try:
            # Start consuming messages
            await rabbitmq_consumer.consume_all()
        except Exception as e:
            logger.error(f"Worker service error: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the worker service"""
        if not self.running:
            return

        logger.info("Stopping RabbitMQ Worker Service...")
        self.running = False

        try:
            await rabbitmq_consumer.close()
        except Exception as e:
            logger.error(f"Error stopping worker service: {e}")

        logger.info("Worker service stopped")


worker_service = WorkerService()



