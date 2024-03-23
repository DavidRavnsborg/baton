import requests
import json
from operations.http.http_helper import decode_response, wait_until_retry


def _filter_submission(submission: object, filters: list) -> bool:
    """Filters is a list of lambdas/functions which take a submission as an argument, and return
    True/False.
    """
    # Evaluate the filters to bool results
    filters = [filter(submission) for filter in filters]
    # Only consider submissions that are marked active (Jotform appears to sometimes do things like re-create rows when columns change).
    filters.append(submission["status"] != "ACTIVE")
    # If any filter values are True, then the result will be over >= 1 and will be re-cast as True (i.e. filter this submission)
    return bool(sum(filters))


def get_form_responses(api_key: str, form_id: str, filters: list):
    # GET submissions
    submissions = decode_response(
        requests.get(
            url=f"https://api.jotform.com/form/{form_id}/submissions?apiKey={api_key}",
        ).content
    )
    if submissions["responseCode"] != 200:
        raise Exception(
            f"Getting form {form_id} responses request failed. Check that api_key and form_id are correct."
        )
    new_submissions = [
        submission
        for submission in submissions["content"]
        if not _filter_submission(submission, filters)
    ]
    print(
        f"Submissions length: {len(submissions['content'])}; Filtered submissions length: {len(new_submissions)}"
    )
    print(f"get Jotform resultSet: {submissions['resultSet']}")
    return new_submissions


def format_jotform_date(date: object) -> str:
    if "year" not in date:
        return ""
    return f"{date['year']}/{date['month']}/{date['day']}"


def answer_or_blank(submission: str, index: str, sub_level=None) -> str:
    """Helper for optional fields that are not required in OCMS or the Welcome Form, which
    may be blank or filled.
    """
    if not sub_level:
        return (
            submission["answers"][index]["answer"]
            if "answer" in submission["answers"][index]
            else ""
        )
    return (
        submission["answers"][index]["answer"][sub_level]
        if "answer" in submission["answers"][index]
        else ""
    )


def update_participant_submission(
    api_key: str,
    submission_id: str,
    request_body: object,
    http_config: object,
    attempt=1,
) -> object:
    response = requests.post(
        url=f"https://api.jotform.com/submission/{submission_id}?apiKey={api_key}",
        data=request_body,
    )
    content_response = decode_response(response.content)
    # TODO: Add additional request failures which don't require re-attempts here, rather than waiting
    # to retry them until we reach the timeout limit below.
    if content_response["responseCode"] in [400, 401, 403]:
        print(
            f"ERROR: Unable to update Jotform submissionStatus. Skipping submission. Response: {content_response}"
        )
    elif content_response["responseCode"] != 200:
        wait_until_retry(attempt, content_response, http_config)
        # Recursively retry
        update_participant_submission(
            api_key=api_key,
            submission_id=submission_id,
            request_body=request_body,
            http_config=http_config,
            attempt=attempt + 1,
        )

    return response


def get_submission(api_key: str, submission_id: str):
    return json.loads(
        requests.get(
            f"https://api.jotform.com/submission/{submission_id}?apiKey={api_key}"
        ).content.decode()
    )
