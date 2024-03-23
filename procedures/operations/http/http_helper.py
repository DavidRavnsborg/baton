import inspect
import json
import requests
import time


def is_downloadable(url):
    """
    Does the url contain a downloadable resource
    from: https://www.codementor.io/@aviaryan/downloading-files-from-urls-in-python-77q3bs0un
    """
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get("content-type")
    if "text" in content_type.lower():
        return False
    if "html" in content_type.lower():
        return False
    return True


def wait_until_retry(retries, response, http_config):
    print(f"Retries: {retries}")
    caller_func_name = inspect.stack()[1].function
    wait_time = (
        http_config["growth_rate_of_backoff"] ** retries
        * http_config["initial_retry_timeout"]
    )
    if wait_time >= http_config["timeout_limit"]:
        raise TimeoutError(
            f"Request timed out after {retries} attempts of {caller_func_name}. Final request response: {response}"
        )
    print(
        f"Invalid response on request made in {caller_func_name}. Re-attempting after {wait_time} seconds."
    )
    time.sleep(wait_time)


def decode_response(content):
    return json.loads(content.decode())
