import os
import platform
import subprocess
from operations.local.logging import baton_log


def get_linux_processes():
    """Parse the output of `ps aux` into a list of dictionaries representing the parsed
    process information from each row of the output. Keys are mapped to column names,
    parsed from the first line of the process' output.
    :rtype: list[dict]
    :returns: List of dictionaries, each representing a parsed row from the command output
    """
    output = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE).stdout.readlines()
    output = [out.decode() for out in output]
    headers = [h for h in " ".join(output[0].strip().split()).split() if h]
    raw_data = map(lambda s: s.strip().split(None, len(headers) - 1), output[1:])
    return [dict(zip(headers, r)) for r in raw_data]


def is_process_running(process_name="/usr/lib/R/bin/exec/R"):
    if platform.system() == "Windows":
        baton_log.warning(
            "'ps aux' not supported on windows. Consider using 'wsl ps aux' and running R on wsl linux. Returning False for process not running."
        )
        return False
    for process in get_linux_processes():
        if process_name in process["COMMAND"]:
            baton_log.info(f"Running process found: {process_name}")
            return True
    baton_log.info(f"Running process not found: {process_name}")
    return False


def log_subprocess_output(process, re_encode=False, error_cases=[]):
    """Captures output from running subprocess.

    Set re_encode to True if you are dealing with characters that don't match what your logger
    can interpret, and you cannot include those by switching to utf-8 or utf-16.
    """

    while True:
        output = (
            process.stdout.readline()
            .decode()
            .encode("cp1252", "replace")
            .decode("cp1252")
            if re_encode
            else process.stdout.readline().decode()
        )
        if output:
            baton_log.info(output)
            for error_case in error_cases:
                if error_case in output:
                    baton_log.error(
                        "Detected error in log output on stdout or stderr from Python subprocess. Halting execution."
                    )
                    raise Exception(error_case)
        else:
            break


def checkout_git_branch(branch_name):
    process = subprocess.Popen(
        "git pull",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )
    # Keep checking stdout/stderr until the child process exits
    while process.poll() is None:
        log_subprocess_output(process, re_encode=True)
        break

    process = subprocess.Popen(
        f"git checkout {branch_name}",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )
    # Keep checking stdout/stderr until the child process exits
    while process.poll() is None:
        log_subprocess_output(
            process,
            re_encode=True,
            error_cases=[
                "error: Your local changes to the following files would be overwritten by checkout:"
            ],
        )
        break

    process = subprocess.Popen(
        "git pull",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )
    # Keep checking stdout/stderr until the child process exits
    while process.poll() is None:
        log_subprocess_output(process, re_encode=True)
        break
