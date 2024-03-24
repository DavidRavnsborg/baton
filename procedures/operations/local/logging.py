from azure.monitor.opentelemetry import configure_azure_monitor
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from datetime import datetime
from functools import wraps
import logging
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.sdk.trace import TracerProvider
import os


def class_init_timestamp_decorator(init):
    """Allows the BatonLogger, or another class, to receive the same timestamp argument every time
    it is initialized.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    @wraps(init)
    def wrapper(self, **kwargs):
        if "timestamp" in kwargs:
            init(self, **kwargs)
        else:
            init(self, timestamp=timestamp, **kwargs)

    return wrapper


class BatonLogger:
    """Handles Baton logging. Can write to multiple streams.

    NOTE: You are able to make logging level of different logging streams be configurable. You
    can currently set a level for the logger, and modify this function to set one for different
    logging streams.
    """

    @class_init_timestamp_decorator
    def __init__(
        self,
        log_name: str,
        use_azure_monitor: bool,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        timestamp=None,
        attributes={},
    ):
        self.log_name = f"{timestamp}-{log_name}.log"
        self.level = level
        self.formatter = logging.Formatter(format)
        self.set_attributes(attributes)
        logger = logging.getLogger(__name__)
        logger.setLevel(self.level)
        # If the logger has handlers, clear them
        if logger.hasHandlers():
            logger.handlers.clear()
        self.logger = logger

        self._console()
        if len(self.log_name) > 0:
            self._file()
        if use_azure_monitor:
            self._azure()

    def set_attributes(self, attributes):
        self.attributes = attributes

    def debug(self, message):
        self.logger.debug(message, extra=self.attributes)

    def info(self, message):
        self.logger.info(message, extra=self.attributes)

    def warning(self, message):
        self.logger.warning(message, extra=self.attributes)

    def error(self, message):
        self.logger.error(message, extra=self.attributes)

    def critical(self, message):
        self.logger.critical(message, extra=self.attributes)

    def _configure_handler(self, handler):
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        handler.encoding = "utf-8"
        logging.getLogger().addHandler(handler)
        self.logger.addHandler(handler)

    def _console(self):
        # Create a logging handler and attach it to the logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        # Allow utf-8 chars (R Targets pipeline logs utf-8 chars)
        console_handler.encoding = "utf-8"
        # Add the handler to the logger
        self.logger.addHandler(console_handler)

    def _file(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        # Create a file handler
        file_handler = logging.FileHandler(f"logs/{self.log_name}")
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        # Allow utf-8 chars (R Targets pipeline logs utf-8 chars)
        file_handler.encoding = "utf-8"
        # Add the handler to the logger
        self.logger.addHandler(file_handler)

    def _azure(self):
        # Configure OpenTelemetry to use Azure Monitor with the specified connection
        # string.
        try:
            configure_azure_monitor(connection_string="")
        except:
            baton_log.warning(
                "Error initializing Azure Monitor. Check your connection_string and ensure it matches the one in your Azure Monitor environment."
            )

    def _azure_custom(self):
        """Alternative approach to directing logs to Azure Monitor."""
        # Create a provider
        trace.set_tracer_provider(TracerProvider())
        logger_provider = LoggerProvider()
        set_logger_provider(logger_provider)
        exporter = AzureMonitorLogExporter(connection_string="")
        logger_provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))

        # Create a logging handler and attach it to the logger
        open_telemetry_handler = LoggingHandler()
        open_telemetry_handler.setLevel(self.level)
        open_telemetry_handler.setFormatter(self.formatter)
        open_telemetry_handler.encoding = "utf-8"
        self.logger.addHandler(open_telemetry_handler)


class BatonLoggerProxy:
    def __init__(self):
        self._baton_logger = None

    def __getattr__(self, name):
        if self._baton_logger is None:
            self.initialize_default_logger()
        return getattr(self._baton_logger, name)

    def initialize_default_logger(self):
        """Initializes the default BatonLogger instance."""
        self._baton_logger = BatonLogger(
            log_name=f"INFO-baton", use_azure_monitor=False, level=logging.INFO
        )

    def replace_logger(
        self,
        log_name: str,
        use_azure_monitor: bool = False,
        level=logging.INFO,
        timestamp=None,
    ):
        """Replaces the current BatonLogger instance with a new one, configured with the given parameters."""
        # Create a new BatonLogger instance with the provided configuration
        self._baton_logger = BatonLogger(
            log_name=log_name,
            use_azure_monitor=use_azure_monitor,
            level=level,
            timestamp=timestamp,
        )


# Set up the logger and make it available as a module-level variable
baton_log = BatonLoggerProxy()
