import pandas as pd
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.local.logging import baton_log


def select_blob_name(blob_name, must_contain, must_not_contain):
    if len(must_not_contain) == 0:
        return must_contain in blob_name
    return must_contain in blob_name and must_not_contain not in blob_name


def lemr_list_raw_files_in_azure(
    config_path="../configs/purpose-lemr-local.yaml",
    must_contain="",
    must_not_contain="",
    verbose=False,
):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )
    containers = config["storage"]["containers"]

    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])

    all_cities_blobs = []
    for container in containers:
        blobs = storage_client.get_blobs(container_name=container)
        baton_log.info(f"{len(blobs)} blobs in {container}")
        all_cities_blobs = all_cities_blobs + [
            {
                "name": blob["name"],
                "container": blob["container"],
                "version_id": blob["version_id"],
                "last_modified": blob["last_modified"],
                "creation_time": blob["creation_time"],
            }
            for blob in blobs
            if select_blob_name(blob["name"], must_contain, must_not_contain)
        ]
    if verbose:
        print(
            f"Found {len(all_cities_blobs)} blobs, with must_contain={must_contain} and must_not_contain={must_not_contain}."
        )
    return all_cities_blobs
