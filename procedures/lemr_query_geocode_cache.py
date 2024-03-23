import pandas as pd
import sys
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log


def lemr_query_geocode_cache(
    config_path, partition_key, convert_TableEntity_to_dict=False
):  # convert_to_df = False):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    baton_log.info(f"Querying entities on partition_key {partition_key}")
    entities = storage_client.query_entities(
        filter=f"PartitionKey eq '{partition_key}'",
        verbose=False,
        tablename="geocodecache",
    )

    baton_log.info(f"Adding timestamps.")
    for entity in entities:
        entity["cached_date"] = entity._metadata["timestamp"].timestamp()

    if convert_TableEntity_to_dict:
        entities = [dict(entity) for entity in entities]

    return entities


if __name__ == "__main__":
    if len(sys.argv) > 1:
        city = sys.argv[1]
        city_cache = lemr_query_geocode_cache(
            "C:/dev/lemr-pipeline/python/baton/configs/purpose-lemr-local.yaml", city
        )
        print(f"Length of geocode cache for {city}: {len(city_cache)}")
        print(f"Type of city_cache is {type(city_cache)}")
