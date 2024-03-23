import os
import traceback
import yaml
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config, read_yaml, save_yaml
from operations.local.io import get_file_name
from operations.local.logging import baton_log
from operations.local.system import is_process_running, checkout_git_branch


def lemr_get_geocoder_submissions(config_path: str, row_key=""):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"], secret_names=["azure-storage-connect-str"]
    )
    py_runner_config = config["storage"]["tables"]["runner"]
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])

    filter = f"PartitionKey eq '{py_runner_config['partition']}'"
    if len(row_key) > 0:
        filter = f"{filter} and RowKey eq '{row_key}'"
    submissions = storage_client.query_entities(
        filter=filter, tablename=py_runner_config["table"]
    )
    baton_log.info(f"{len(submissions)} found in table py_runner_config['table']")
    return submissions


# if __name__ == '__main__':
#     try:
#         procedure_name = get_file_name(__file__)
#         baton_log.info(f"Running {procedure_name} procedure.")
#         submissions = lemr_get_geocoder_submissions(
#             config_path = "configs/purpose-lemr-local.yaml",
#             row_key = '1c3a66ad-689d-46fb-944d-f8eb395737c8')
#         print(submissions)
#         baton_log.info(f"Execution of {procedure_name} finished.")

#     except Exception as e:
#         baton_log.error(e, exc_info=True)
#         baton_log.critical("Procedure terminated.")
