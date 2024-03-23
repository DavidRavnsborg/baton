from operations.local.logging import baton_log
from datetime import datetime
import logging

new_log_filename = f"BATON-DEMO-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
# baton_log.info(f"Swapping to new log file {new_log_filename}.")
baton_log.replace_logger(
    log_name=new_log_filename, use_azure_monitor=True, level=logging.INFO
)
baton_log.info("hi")
