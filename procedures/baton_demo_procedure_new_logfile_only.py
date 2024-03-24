from operations.local.logging import baton_log
from datetime import datetime
import logging


new_log_filename = f"BATON-DEMO"
baton_log.replace_logger(
    log_name=new_log_filename, use_azure_monitor=False, level=logging.INFO
)
baton_log.info("hi")
