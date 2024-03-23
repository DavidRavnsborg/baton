from azure.data.tables import UpdateMode
import uuid
from operations.local.logging import baton_log


def print_table_diff(entities_before, entities_after):
    baton_log.info(f"Length of Table before: {len(entities_before)}")
    baton_log.info(f"Length of Table after: {len(entities_after)}")
    row_keys_before = {entity["RowKey"] for entity in entities_before}
    row_keys_after = {entity["RowKey"] for entity in entities_after}
    for row_key_before in row_keys_before:
        if row_key_before not in row_keys_after:
            baton_log.info(f"Added new row with RowKey {row_key_before['RowKey']}")
    baton_log.info("Finished diff.")


def upload_entities_to_table(entities, table, storage_client, error_partition):
    baton_log.info(f"Uploading entities to table {table}.")
    already_exists_count = 0
    for entity in entities:
        try:
            storage_client.add_entity(entity, tablename=table)
            baton_log.info(f"Added row {entity['RowKey']}")
        except Exception as e:
            if e.reason == "Conflict":
                already_exists_count += 1
            else:
                entity_error = entity.copy()
                entity_error["PartitionKey"] = error_partition
                entity_error["AttemptedRowKey"] = entity_error["RowKey"]
                entity_error["RowKey"] = str(uuid.uuid4())
                entity_error["error_reason"] = e.reason
                entity_error["error_status_code"] = e.status_code
                storage_client.add_entity(entity_error, tablename=table)
                baton_log.error(
                    f"Entity with RowKey {entity['RowKey']} encountered exception: {e}"
                )
    baton_log.info(
        f"Ignored {already_exists_count} rows that are already in the table {table}."
    )


def upload_entities_to_table_merge_if_conflict(
    entities, table, storage_client, error_partition
):
    baton_log.info(f"Uploading entities to table {table}.")
    already_exists_count = 0
    for entity in entities:
        try:
            storage_client.add_entity(entity, tablename=table)
            baton_log.info(f"Added row {entity['RowKey']}")
        except Exception as e:
            if e.reason == "Conflict":
                storage_client.update_entity(
                    entity=entity, tablename=table, update_mode=UpdateMode.MERGE
                )
            else:
                entity_error = entity.copy()
                entity_error["PartitionKey"] = error_partition
                entity_error["AttemptedRowKey"] = entity_error["RowKey"]
                entity_error["RowKey"] = str(uuid.uuid4())
                entity_error["error_reason"] = e.reason
                entity_error["error_status_code"] = e.status_code
                storage_client.add_entity(entity_error, tablename=table)
                baton_log.error(
                    f"Entity with RowKey {entity['RowKey']} encountered exception: {e}"
                )
    baton_log.info(
        f"Ignored {already_exists_count} rows that are already in the table {table}."
    )


def format_fields_for_azure_table(df_columns_index_or_series):
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "* ", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "*", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "?", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "\t", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "/", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "#", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "(", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        ")", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        ".", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        ",", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "-", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "'", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        ":", "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "+", "plus", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        " ", "_", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "___", "_", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "__", "_", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        '"', "", regex=False
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "^_", "", regex=True
    )
    df_columns_index_or_series = df_columns_index_or_series.str.replace(
        "_$", "", regex=True
    )
    return df_columns_index_or_series
