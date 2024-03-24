from operations.local.logging import baton_log
from datetime import datetime
import logging
import time


new_log_filename = f"BATON-DEMO"
baton_log.info(f"Swapping to new log file {new_log_filename}.")
time.sleep(1)
baton_log.replace_logger(
    log_name=new_log_filename,
    use_azure_monitor=False,
    level=logging.INFO,
    timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
)
baton_log.info("hi")
