from app.config.setting import settings
from app.workers.worker import worker_service

QUEUE_HANDLER_MAP = {
    settings.SITE_ANALYSE_QUEUE: worker_service.process_site_analyse,
    settings.PAGE_EXTRACT_QUEUE: worker_service.process_page_extract,
    settings.LLM_QUEUE: worker_service.process_llm_task,
}
