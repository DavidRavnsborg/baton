import pandas as pd
from operations.http.azure import get_secrets, AzureStorage
from operations.local.config import load_config
from operations.http.azure_helper import print_table_diff
from operations.local.io import get_file_name, read_dataframe_with_unknown_header_row
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os


def lemr_geocode_storage_client(config_path):
    config = load_config(config_path)
    secrets = get_secrets(
        vault_url=config["key_vault"],
        secret_names=[
            "azure-storage-connect-str",
        ],
    )
    storage_client = AzureStorage(connection_str=secrets["azure-storage-connect-str"])
    return storage_client
