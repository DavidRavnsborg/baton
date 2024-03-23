import pandas as pd
import os
from operations.http.azure import get_secrets, AzureStorage
from operations.http.http_helper import is_downloadable
from operations.local.config import load_config
from operations.local.io import (
    get_file_name,
    verify_unknown_named_files_have_downloaded,
)


def lemr_download_files_from_azure(
    files, downloads_folder, config_path="../configs/purpose-lemr-local.yaml"
):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    file_paths = []

    if not os.path.exists(downloads_folder):
        raise Exception(
            f"Downloads folder does not exist - please ensure a valid downloads folder has been created, and the downloads_folder parameter is correct. downloads_folder: {downloads_folder}"
        )
    for file in files:
        city_folder = os.path.normpath(
            f"{downloads_folder}/{file['container']}"
        ).replace("\\", "/")
        file_folder = os.path.dirname(f"{city_folder}/{file['name']}")
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)

        file_paths.append(
            storage_client.download_file(
                container_name=file["container"],
                local_file_folder=city_folder,
                blob_name=file["name"],
            )
        )
    print(f"Files downloaded to {downloads_folder}")
    return file_paths
