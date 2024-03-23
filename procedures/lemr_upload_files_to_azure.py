import pandas as pd
import os
import requests
from operations.http.azure import get_secrets, AzureStorage
from operations.http.http_helper import is_downloadable
from operations.local.config import load_config
from operations.local.io import (
    get_file_name,
    verify_unknown_named_files_have_downloaded,
)


def validate_region_container(region):
    if region not in {
        "vancouver",
        "calgary",
        "winnipeg",
        "toronto",
        "montreal",
        "halifax",
    }:
        raise Exception(
            f"Cannot infer city region from file path {region} - no matching region."
        )


def lemr_upload_files_to_azure(files, config_path="../configs/purpose-lemr-local.yaml"):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )

    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    for _, file in files.iterrows():
        validate_region_container(file["region"])
        storage_client.upload_file(
            container_name=file["region"],
            local_file_path=file["abs_path"],
            blob_name=file["azure_path"],
            overwrite=True,
        )
    return files
