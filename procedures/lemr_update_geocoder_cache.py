from azure.data.tables import UpdateMode
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log


def lemr_update_geocoder_cache(
    config_path: str,
    row_key: str,
    key_value_pairs: dict,
    partition: str,
    debug_query=False,
):
    """`debug_query` runs a query filter with the `partition` and `row_key`, to debug whether the
    record currently exists.
    """
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"], secret_names=["azure-storage-connect-str"]
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])

    # Update submissions table
    py_cache_config = config["storage"]["tables"]["cache"]
    baton_log.info(
        f"Updating geocoder submission with PartitionKey: '{partition}' and RowKey: '{row_key}'."
    )
    entity = {"PartitionKey": partition, "RowKey": row_key}
    for key, value in key_value_pairs.items():
        entity[key] = value
    baton_log.info("Check this")
    baton_log.info(entity)
    if debug_query:
        filter = f"PartitionKey eq '{partition}' and RowKey eq '{row_key}'"
        baton_log.info(
            f"Querying table {py_cache_config['table']} with KQL query: {filter}"
        )
        baton_log.info(
            storage_client.query_entities(
                filter=filter, tablename=py_cache_config["table"]
            )
        )
    storage_client.update_entity(
        entity=entity, tablename=py_cache_config["table"], update_mode=UpdateMode.MERGE
    )
    baton_log.info(f"Updated submission to {entity} using MERGE update mode.")
