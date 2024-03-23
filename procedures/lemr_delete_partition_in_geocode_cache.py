import pandas as pd
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log


def delete_partition_in_geocode_cache(config_path, partition_key):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    table_name = "geocodecache"
    baton_log.info("Querying entities...")
    entities = storage_client.query_entities(
        filter=f"PartitionKey eq '{partition_key}'", verbose=False, tablename=table_name
    )
    baton_log.info("Deleting entities...")
    for entity in entities:
        baton_log.info(entity["bing_formatted_address"])
        baton_log.info(entity["RowKey"])
        storage_client.delete_entity(
            partition_key=partition_key, row_key=entity["RowKey"], tablename=table_name
        )
    baton_log.info("Done.")
    return entities


# if __name__ == "__main__":
#   print(delete_partition_in_geocode_cache("C:/dev/lemr-pipeline/python/baton/configs/purpose-lemr-local.yaml", "winnipeg"))
