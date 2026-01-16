from app.config.setting import settings
from app.workers.worker import worker_service

QUEUE_HANDLER_MAP = {
    settings.PAGE_EXTRACT_QUEUE: worker_service.process_page_extract,
    settings.PAGE_ANALYSE_QUEUE: worker_service.process_page_analyse,
}
