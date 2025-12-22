from app.config.logger import logger


class WorkerService:

    async def process_site_analyse(self, body: dict):
        """
        Handles SITE_ANALYSE_QUEUE

        Example responsibilities:
        - Validate input
        - Save site info
        - Trigger page extraction
        """
        try:
            logger.info(f"[SITE_ANALYSE] Started | payload={body}")

            site_id = body.get("site_id")
            url = body.get("url")

            if not site_id or not url:
                raise ValueError("site_id or url missing")

           

        except Exception as e:
            logger.exception(f"[SITE_ANALYSE] Failed | error={e}")
            raise


    async def process_page_extract(self, body: dict):
        """
        Handles PAGE_EXTRACT_QUEUE

        Example responsibilities:
        - Extract content from pages
        - Clean HTML
        - Store extracted text
        """
        try:
            logger.info(f"[PAGE_EXTRACT] Started | payload={body}")

            page_id = body.get("page_id")
            page_url = body.get("page_url")

            if not page_id or not page_url:
                raise ValueError("page_id or page_url missing")

        except Exception as e:
            logger.exception(f"[PAGE_EXTRACT] Failed | error={e}")
            raise


    async def process_llm_task(self, body: dict):
        """
        Handles LLM_QUEUE

        Example responsibilities:
        - Build prompt
        - Call LLM
        - Save response
        """
        try:
            logger.info(f"[LLM] Started | payload={body}")

            task_id = body.get("task_id")
            content = body.get("content")

            if not task_id or not content:
                raise ValueError("task_id or content missing")



        except Exception as e:
            logger.exception(f"[LLM] Failed | error={e}")
            raise


worker_service = WorkerService()
