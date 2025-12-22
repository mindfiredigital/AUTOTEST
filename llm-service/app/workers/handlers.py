"""
Message handlers for RabbitMQ consumer worker
Each handler processes a specific type of message
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.config.database import SessionLocal

logger = logging.getLogger(__name__)


# Queue names
QUEUE_SITE_ANALYSE = "site_analyse_queue"



async def handle_email_message(message: Dict[str, Any]):
    """
    Handle email messages

    Args:
        message: Message data containing email information
    """
    try:
        logger.info(f"Processing email message: {message}")
        print("message",message)

    except Exception as e:
        logger.error(f"Error handling email message: {e}")
        raise


def register_all_handlers(consumer):
    """
    Register all message handlers with the consumer

    Args:
        consumer: RabbitMQConsumer instance
    """
    consumer.register_handler(QUEUE_SITE_ANALYSE, handle_email_message)


    logger.info("All message handlers registered successfully")
