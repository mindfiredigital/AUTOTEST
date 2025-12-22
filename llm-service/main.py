from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.rabbitmq import rabbitmq_connection
from app.config.logger import logger
from app.config.setting import settings
from app.services.rabbitmq_consumer import RabbitMQConsumer
from app.workers.worker import worker_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastAPI application...")
    consumer_task = None

    try:
        await rabbitmq_connection.connect()
        logger.info("RabbitMQ connection initialized")

        consumer = RabbitMQConsumer(channel_pool=rabbitmq_connection.channel_pool)
        consumer.register_handler("site_analyse_queue", worker_service.process_message)

        consumer_task = asyncio.create_task(consumer.consume_all())
        logger.info("RabbitMQ consumer started")

    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")

    yield

    logger.info("Shutting down FastAPI application...")

    if consumer_task:
        await consumer.stop()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("RabbitMQ consumer stopped")

    try:
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ connection: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "AutoTest API", "status": "running"}

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "rabbitmq": "connected"
            if rabbitmq_connection.connection_pool
            else "disconnected",
        }

    return app

app = create_app()
