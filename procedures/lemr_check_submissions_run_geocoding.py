from datetime import datetime
import logging
from opentelemetry import trace
import os
import subprocess
import uuid
from operations.http.azure import get_secrets, AzureStorage
from operations.http.azure_helper import upload_entities_to_table
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.io import get_file_name
from operations.local.logging import BatonLogger, baton_log
from operations.local.system import (
    is_process_running,
    checkout_git_branch,
    log_subprocess_output,
)


def lemr_check_submissions_run_geocoding(config, secrets):
    # This function uses the global baton_log, then replaces it with a cleaner
    # class specific log file attached to a new baton_log object, after the
    # submissions table has been queried and the class named has been obtained.
    global baton_log

    # If R is already running on the VM, exit
    if is_process_running(process_name="/usr/lib/R/bin/exec/R"):
        baton_log.info("R process already running. Exiting.")
        return

    # Get active submissions
    py_runner_config = config["storage"]["tables"]["runner"]
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    submissions = storage_client.query_entities(
        filter=f"PartitionKey eq '{py_runner_config['partition']}'",
        tablename=py_runner_config["table"],
    )
    baton_log.info(f"{len(submissions)} found in table py_runner_config['table']")
    active_submissions = [
        submission for submission in submissions if submission["status"] == "active"
    ]
    baton_log.info(
        f"{len(active_submissions)} 'active' submissions found in table py_runner_config['table']"
    )
    if len(active_submissions) == 0:
        baton_log.info("No submissions with 'active' status.")
        return

    current_submission = active_submissions[0]
    # for submission in submissions:
    #     print(submission)
    #     if submission['cleaner_name'] == 'halifax_building_permits':
    #         current_submission = submission
    #         break

    # Change baton_log to new instance named for the cleaner class
    new_log_filename = f"INFO-{current_submission['cleaner_name']}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    baton_log.info(f"Swapping to new log file {new_log_filename}.")
    baton_log = BatonLogger(
        log_name=new_log_filename, use_azure_monitor=True, level=logging.INFO
    )

    # Change to lemr-pipeline directory 2 levels up, prepare git branch, update config, and run
    # the Targets pipeline.
    os.chdir("../..")
    checkout_git_branch(current_submission["branch_name"])

    # Check which API key we should use, and how much capacity it has remaining
    api_key_config = config["storage"]["tables"]["api_key_usage"]
    partitions = api_key_config["partitions"]
    date_today = datetime.now().date()
    filter = "("
    for i, partition in enumerate(partitions):
        filter = f"{filter} PartitionKey eq '{partition}'"
        if i < len(partitions) - 1:
            filter = f"{filter} and"
    filter = f"{filter}) or date eq '{date_today}'"
    baton_log.info(f"Checking API Key Usage records with filter: {filter}")
    api_usage = storage_client.query_entities(
        filter=filter, tablename=api_key_config["table"]
    )
    baton_log.info(
        f"{len(api_usage)} records found: {[entity for entity in api_usage]}"
    )

    # If we are missing a record for API key usage today on one of our partition keys, create one with 0 addresses_geocoded
    if len(api_usage) < len(partitions):
        for partition in partitions:
            if partition not in [entity["PartitionKey"] for entity in api_usage]:
                entity = {
                    "PartitionKey": partition,
                    "RowKey": str(uuid.uuid4()),
                    "date": str(date_today),
                    "addresses_geocoded": 0,
                }
                baton_log.info(f"Creating record: {entity}")
                upload_entities_to_table(
                    entities=[entity],
                    table=api_key_config["table"],
                    storage_client=storage_client,
                    error_partition=api_key_config["error_partition"],
                )
                api_usage.append(entity)

    # Run the geocoder with the first API key that has available usage capacity
    for entity in api_usage:
        if entity["addresses_geocoded"] < api_key_config["usage_daily_limit"]:
            # Run R lemr-pipeline with args for env variables to be set in Targets
            r_command = [
                "Rscript",
                "run_clean_data_pipeline.R",
                current_submission["RowKey"],  # automation_row_key
                current_submission["cleaner_name"],  # automation_cleaner_class
                str(current_submission["rows_geocoded"]),  # automation_rows_geocoded
                secrets[entity["PartitionKey"]],  # BING_TOKEN
                entity["PartitionKey"],  # usage_partition_key
                entity["RowKey"],  # usage_row_key
                str(entity["addresses_geocoded"]),  # usage_addresses_geocoded
                str(api_key_config["usage_daily_limit"]),
            ]  # usage_daily_limit
            baton_log.info(f"Running r_command (first 2 parameters): {r_command[0:2]}")
            try:
                process = subprocess.Popen(
                    r_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                )
            except:
                process = subprocess.Popen(
                    r_command,
                    executable="/usr/bin/Rscript",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                )
            # Keep checking stdout/stderr until the child process exits
            while process.poll() is None:
                log_subprocess_output(process, re_encode=True)
            break


if __name__ == "__main__":
    config = load_config()
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=["azure-storage-connect-str", "PAKey", "ONPHAKey"],
    )
    procedure_name = get_file_name(__file__)
    # Azure
    # with trace.get_tracer_provider().start_as_current_span(procedure_name) as span:
    with trace.get_tracer(__name__).start_as_current_span(procedure_name) as span:
        baton_log.set_attributes(
            {
                "client": "internal",
                "project": "lemr",
                "app": "baton",
                "procedure": procedure_name,
            }
        )
        baton_log.info(f"Running {procedure_name} procedure.")
        lemr_check_submissions_run_geocoding(config=config, secrets=secrets)
        baton_log.info(f"Execution of {procedure_name} finished.")
