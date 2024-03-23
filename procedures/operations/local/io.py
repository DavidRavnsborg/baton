import os
import pandas as pd
import time
from operations.local.logging import baton_log


def get_file_name(file_path, with_extension=False):
    """Gets name of the file of the caller.
    file_path must receive the __file__ parameter from the caller.
    """
    file_name = lambda path: os.path.basename(path)
    if with_extension:
        return file_name(file_path)
    return file_name(file_path).split(".")[0]


def read_dataframe_with_unknown_header_row(
    file_path,
    pd_read_func=pd.read_csv,
    str_in_column_header="Last Name",
    str_in_footer=None,
    header_offset=1,
    nrows_offset=-1,
):
    df = pd_read_func(file_path)

    def find_row(text_in_row):
        for column in df.columns:
            result = df[df[column].astype(str).str.match(text_in_row)]
            if len(result) > 0 and len(result.index.values) == 1:
                if len(result) > 1:
                    baton_log.warning(
                        f"{text_in_row} found multiple times in Dataframe {file_path}."
                    )
                # If we find a matching row, and only a single matching row, return the index of the row
                return result.index.values[0]
        raise Exception(f"'{text_in_row}' text not found in Dataframe.")

    # Unclear why the header row is indexed at 2 less than the actual header row, but we need to skip
    # 1 less row than the header row location. The skiprows argument references on the actual row
    # number, as you would see it in excel.
    skip_rows = find_row(str_in_column_header) + header_offset
    nrows = None
    if str_in_footer:
        nrows = find_row(str_in_footer) - skip_rows + nrows_offset
        baton_log.info(
            f"The header row for {file_path} starts at row {skip_rows+1} and the table ends at {skip_rows+nrows+1}."
        )
    else:
        baton_log.info(f"The header row for {file_path} starts at row {skip_rows+1}.")
    return pd_read_func(file_path, skiprows=skip_rows, nrows=nrows)


def delete_folder_contents(download_dir, wait_time=0):
    if not os.path.isdir(download_dir):
        baton_log.info(
            f"Folder {download_dir} does not exists yet. Skipping deleting folder contents."
        )
        return
    baton_log.info(f"Deleting contents of downloads folder: {download_dir}")
    files = os.listdir(download_dir)
    baton_log.info(files)
    for file in files:
        file_path = f"{download_dir}/{file}"
        os.remove(file_path)
    baton_log.info(f"Waiting {wait_time} seconds for file(s) to delete")
    time.sleep(wait_time)


def verify_file_has_downloaded(wait_time, download_dir, filename, verbose=True):
    """Checks if an expected filename has been download."""
    baton_log.info(f"Waiting {wait_time} seconds for file(s) to download")
    time.sleep(wait_time)
    files = os.listdir(download_dir)
    baton_log.info("Files in folder:")
    for file in files:
        baton_log.info(file)
    if filename not in files:
        raise Exception(f"Filename {filename} not found in folder: {download_dir}.")

    return files


def verify_unknown_named_files_have_downloaded(
    wait_time, download_dir, file_count=0, disallow_too_many_files=True, verbose=True
):
    """Checks if an expected number of files have been downloaded.
    NOTE: This expects the download directory to be empty unless disallow_too_many_files is False.
    """
    # Explicit wait, giving time for the file to finish downloading
    # TODO: Add decorator for re-trying a function. Might apply to both http and local operations.
    # 			Can work by constant frequency polling, or exponential decay (like
    # 			http_helper.wait_until_retry).
    baton_log.info(f"Waiting {wait_time} seconds for file(s) to download")
    time.sleep(wait_time)
    files = os.listdir(download_dir)
    if verbose:
        baton_log.info("Files in folder:")
        for file in files:
            baton_log.info(file)
    if file_count == 0:
        return files
    elif len(files) < file_count:
        raise Exception(
            f"Only {len(files)}/{file_count} files found. You might need to provide more time for the download(s) to complete, or check your download location in the config."
        )
    elif len(files) > file_count and disallow_too_many_files:
        raise Exception(
            f"Too many files found in {download_dir}. Check the download location or file download logic."
        )

    return files


def verify_file_has_downloaded(wait_time, filename, download_dir):
    """Checks if a file has been downloaded."""
    # Explicit wait, giving time for the file to finish downloading
    # TODO: Add decorator for re-trying a function. Might apply to both http and local operations.
    # 			Can work by constant frequency polling, or exponential decay (like
    # 			http_helper.wait_until_retry).
    files = os.listdir(download_dir)
    for file in files:
        if filename in file:
            return file
