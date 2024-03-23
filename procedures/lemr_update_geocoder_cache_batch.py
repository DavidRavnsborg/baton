from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log
import pandas as pd
import time


def lemr_update_geocoder_cache_batch(config_path: str, entities_df: pd.DataFrame):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"], secret_names=["azure-storage-connect-str"]
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])

    # Update submissions table
    py_cache_config = config["storage"]["tables"]["cache"]
    baton_log.info(
        f"Updating {len(entities_df)} geocoder submissions with batch update."
    )
    entities = entities_df.to_dict("records")

    batch_size = 100  # Azure batch update limit
    total_entities = len(entities)
    start_index = 0
    metadata = []
    while start_index <= total_entities:
        end_index = min(start_index + batch_size, total_entities)
        if end_index < 0:
            # Easier to parse log messages in logs than exception messages from R Targets pipeline
            baton_log.error(
                f"end_index is less than 0 ({end_index}). start_index: {start_index}, batch_size: {batch_size}, total_entities: {total_entities}"
            )
            raise Exception(
                f"end_index is less than 0 ({end_index}). start_index: {start_index}, batch_size: {batch_size}, total_entities: {total_entities}"
            )
        batch_entities = entities[start_index:end_index]

        try:
            metadata.extend(
                storage_client.batch_update_entities(
                    entities=batch_entities, tablename=py_cache_config["table"]
                )
            )
            baton_log.info(
                f"Batch update successful for entities {start_index} to {end_index}."
            )
        except Exception as e:
            baton_log.error(
                f"Error during batch update for entities {start_index} to {end_index}: {e}"
            )

        start_index += batch_size

    baton_log.info(
        f"Finished updating {len(entities_df)} geocoder submissions with batch update."
    )

    return pd.DataFrame(metadata)
