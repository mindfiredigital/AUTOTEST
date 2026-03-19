"""Map worker queue names to their handler callables.

This mapping is used by the application's worker registration logic to
connect named queues (from settings) to the corresponding processing
functions on `worker_service`. Keys come from runtime configuration so the
map is evaluated at import time.
"""

from app.config.setting import settings
from app.workers.worker import worker_service


# QUEUE_HANDLER_MAP: settings.<QUEUE_NAME> -> async handler callable
QUEUE_HANDLER_MAP = {
    settings.PAGE_EXTRACT_QUEUE: worker_service.process_page_extract,
    settings.PAGE_ANALYSE_QUEUE: worker_service.process_page_analyse,
    settings.TEST_SCENARIO_QUEUE: worker_service.process_test_scenario,
    settings.TEST_CASE_QUEUE: worker_service.process_test_case,
    settings.PAGE_EXTRACT_SINGLE_QUEUE: worker_service.process_page_extract_single,
    settings.TEST_SCRIPT_QUEUE: worker_service.process_test_script,
    settings.TEST_EXECUTION_QUEUE: worker_service.process_test_execution,
    settings.SCENARIO_RERUN_QUEUE: worker_service.process_scenario_rerun,
    settings.AUTH_CREDENTIAL_UPDATE_QUEUE: worker_service._perform_login_and_discover,
}