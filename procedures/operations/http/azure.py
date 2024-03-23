from azure.data.tables import TableClient, TableServiceClient, UpdateMode
from azure.core.pipeline.transport import RequestsTransport
from azure.keyvault.secrets import SecretClient
from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from operations.local.logging import baton_log
import os


def _get_cli_credential():
    return AzureCliCredential()


def _get_default_credential():
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)


def get_secrets(secret_names: list, vault_url: str) -> dict:
    credential = _get_cli_credential()
    # Configure a custom HTTP transport with a 20 second connection timeout
    transport = RequestsTransport(connection_timeout=20)
    client = SecretClient(
        vault_url=vault_url, credential=credential, transport=transport
    )
    baton_log.info("Requesting secrets from Azure Key Vault")
    return {
        secret_name: client.get_secret(secret_name).value
        for secret_name in secret_names
    }


class AzureStorage:
    """Used for interacting with Azure Storage.
    See MS docs at: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python?tabs=environment-variable-windows
    """

    def __init__(self, connection_str: str):
        self.connection_str = connection_str
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_str
        )
        self.table_service_client = TableServiceClient.from_connection_string(
            connection_str
        )
        baton_log.info("Connected to Azure storage")

    # TABLES

    def add_entity(self, entity: object, tablename="dripCampaign"):
        table_client = self.table_service_client.get_table_client(table_name=tablename)
        entity = table_client.create_entity(entity=entity)

    def update_entity(
        self, entity: object, tablename: str, update_mode=UpdateMode.MERGE
    ):
        table_client = self.table_service_client.get_table_client(table_name=tablename)
        entity = table_client.update_entity(entity=entity, mode=update_mode)

    def batch_update_entities(
        self, entities: list, tablename: str, update_mode=UpdateMode.MERGE
    ):
        table_client = self.table_service_client.get_table_client(table_name=tablename)
        operations = [("update", entity, {"mode": update_mode}) for entity in entities]
        # baton_log.info(f"Batch operations are: {operations}")

        # Submit all operations as a transaction
        try:
            metadata = table_client.submit_transaction(operations)
            baton_log.info("Batch update successful.")
            baton_log.warning(operations[0])
            baton_log.warning("operations are:")
            baton_log.warning(operations)
            return metadata
        except Exception as e:
            baton_log.error(f"Error during batch update: {e}")
            return None

    def delete_entity(self, partition_key: str, row_key: str, tablename="dripCampaign"):
        table_client = self.table_service_client.get_table_client(table_name=tablename)
        table_client.delete_entity(partition_key=partition_key, row_key=row_key)

    def query_entities(self, filter="", verbose=False, tablename="dripCampaign"):
        '''Example filter: "PartitionKey eq 'Participants'"'''
        table_client = self.table_service_client.get_table_client(table_name=tablename)
        entities = table_client.query_entities(filter)
        if verbose:
            baton_log.debug(len(entities))
            for entity in entities:
                for key in entity.keys():
                    baton_log.debug(f"Key: {key}, Value: {entity[key]}")
        # Unpacks azure.core.paging.ItemPaged into a list of azure.data.tables._entity.TableEntity
        return [entity for entity in entities]

    # CONTAINERS

    def create_container(self, container_name: str):
        self.blob_service_client.create_container(container_name)

    def upload_file(
        self,
        container_name: str,
        local_file_path: str,
        blob_name: str,
        overwrite: bool,
        verbose=True,
    ):
        # TODO: Add data versioning for storage accounts which enable blob versioning (i.e. can retain)
        # multiple versions of the same blob.
        # Create a blob client using the local file name as the name for the blob.
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )
        if verbose:
            baton_log.debug(
                f"\nUploading file to Azure Storage as blob:\n\t {blob_name}"
            )
        # Upload the created file
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=overwrite)

    def download_file(
        self, container_name: str, local_file_folder: str, blob_name: str, verbose=True
    ):
        # Create a blob client using the local file name as the name for the blob
        container_client = self.blob_service_client.get_container_client(
            container=container_name
        )
        if verbose:
            baton_log.debug(
                f"\nDownloading blob from Azure Storage to file:\n\t {blob_name}"
            )
        # Upload the created file
        if not os.path.isdir(local_file_folder):
            baton_log.info(f"Making directory {local_file_folder}")
            os.mkdir(local_file_folder)
        file_path = f"{local_file_folder}/{blob_name}"
        with open(f"{local_file_folder}/{blob_name}", "wb") as download_file:
            blob_contents = container_client.download_blob(blob_name).readall()
            download_file.write(blob_contents)
        return file_path

    def _get_blobs(self, container_name: str):  # returns azure.core.paging.ItemPaged
        container_client = self.blob_service_client.get_container_client(
            container=container_name
        )
        # List the blobs in the container
        blobs = container_client.list_blobs()
        return blobs

    def get_blobs(self, container_name: str) -> list:
        return list(self._get_blobs(container_name))

    def print_blobs(self, container_name: str) -> list:
        blobs = self._get_blobs(container_name)
        baton_log.info("\nListing blobs...")
        for blob in blobs:
            baton_log.info(f"\t {blob.name}")
