from azure.data.tables import UpdateMode
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log


def lemr_update_geocoder_submission(
    config_path: str, row_key: str, key_value_pairs: dict
):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"], secret_names=["azure-storage-connect-str"]
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])

    # Update submissions table
    py_runner_config = config["storage"]["tables"]["runner"]
    baton_log.info(
        f"Updating geocoder submission with {py_runner_config['partition']} and {row_key}."
    )
    entity = {"PartitionKey": py_runner_config["partition"], "RowKey": row_key}
    for key, value in key_value_pairs.items():
        entity[key] = value
    storage_client.update_entity(
        entity=entity, tablename=py_runner_config["table"], update_mode=UpdateMode.MERGE
    )
    baton_log.info(f"Updated submission to {entity} using MERGE update mode.")
