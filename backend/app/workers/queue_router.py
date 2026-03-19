"""Mapping of RabbitMQ queue names to worker handler callables.

This module exposes `QUEUE_HANDLER_MAP`, a simple dictionary that
connects queue names (from settings) to the corresponding handler
functions on the worker service. The map is consumed by the
RabbitMQ consumer initialization to register handlers.
"""

from app.config.setting import settings
from app.workers.worker import worker_service

# Map queue name -> handler function (callable accepting the message payload)
QUEUE_HANDLER_MAP = {
    settings.PAGE_STATUS_UPDATE_QUEUE: worker_service.process_page_status_update,
    settings.SITE_STATUS_UPDATE_QUEUE: worker_service.process_site_status_update,
}