from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.rabbitmq import rabbitmq_connection
from app.config.logger import logger
from app.config.setting import settings
from app.workers.worker import worker_service
import asyncio
from app.services.rabbitmq_consumer import rabbitmq_consumer



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting FastAPI application...")
    print("Starting FastAPI application...")

    # Initialize RabbitMQ connection
    try:
        await rabbitmq_connection.connect()
        logger.info("RabbitMQ connection initialized")
        print("RabbitMQ connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ: {e}")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application...")

    # Close RabbitMQ connection
    try:
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ connection: {e}")


def create_app() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG,
        lifespan=lifespan
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
        """Root endpoint"""
        return {
            "message": "AutoTest API",
            "version": "1.0.0",
            "status": "running",
        }


    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "rabbitmq": "connected" if rabbitmq_connection.connection_pool else "disconnected",
        }

    return app


async def main():
    await rabbitmq_consumer.consume_all()

if __name__ == "__main__":
    asyncio.run(main())

app = create_app()
