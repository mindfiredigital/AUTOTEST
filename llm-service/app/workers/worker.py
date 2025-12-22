"""
Worker Service
Contains business logic only (NO RabbitMQ code)
"""
import json
from app.config.logger import logger


class WorkerService:
    async def process_message(self, body: dict):
        """
        Business logic for processing a message.

        - Called by RabbitMQConsumer
        - No RabbitMQ knowledge here
        """
        try:
            logger.info(f"Processing message: {body}")

            # 🔥 Your actual logic here
            # database operations
            # LLM calls
            # API calls
            # etc

            logger.info("Message processed successfully")

        except Exception as e:
            logger.exception(f"Worker error: {e}")
            raise


worker_service = WorkerService()
