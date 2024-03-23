from azure.data.tables import UpdateMode
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log


def lemr_update_geocoder_usage(
    config_path: str, partition_key: str, row_key: str, addresses_geocoded: int
):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"], secret_names=["azure-storage-connect-str"]
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])

    # Update submissions table
    api_key_config = config["storage"]["tables"]["api_key_usage"]
    baton_log.info(f"Updating api key usage with {partition_key} and {row_key}.")
    entity = {
        "PartitionKey": partition_key,
        "RowKey": row_key,
        "addresses_geocoded": addresses_geocoded,
    }
    storage_client.update_entity(
        entity=entity, tablename=api_key_config["table"], update_mode=UpdateMode.MERGE
    )
    baton_log.info(f"Updated api key usage to {entity} using MERGE update mode.")
