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


def lemr_get_apartment_building_registration(config):
    container_name = config["storage"]["azure_container_open_data"]
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )
    url = config["cmhc"]["toronto"]["apartment_building_registration"]["url"]
    filename = config["cmhc"]["toronto"]["apartment_building_registration"]["filename"]

    if not is_downloadable(url):
        raise Exception(f"File at is not downloadable: {url}")
    response = requests.get(url)
    open(filename, "wb").write(response.content)
    print(os.listdir())
    # file = verify_unknown_named_files_have_downloaded(wait_time=20,
    #   download_dir='',
    #   file_count=1)[0]
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    storage_client.upload_file(
        container_name=container_name,
        local_file_path=filename,
        blob_name=filename,
        overwrite=True,
    )
    storage_client.list_blobs(container_name=container_name)


if __name__ == "__main__":
    procedure_name = get_file_name(__file__)
    print(f"Running {procedure_name} procedure")
    lemr_get_apartment_building_registration(load_config())
    print(f"Execution of {procedure_name} finished")
