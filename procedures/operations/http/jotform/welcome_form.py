from operations.http.jotform.base import (
    get_form_responses,
    answer_or_blank,
    update_participant_submission,
    get_submission,
)
from operations.local.logging import baton_log


def _only_submissions_which_definitely_must_be_entered_into_ocms_filter(
    submission, indices
):
    """Only includes submissions which are guaranteed to not be duplicates, and which need to be
    entered into OCMS.
    NOTE: True indicates the submission gets filtered out, False indicates it gets included.
    """
    if "answer" not in submission["answers"][indices["submission_status"]]:
        return True
    elif (
        submission["answers"][indices["submission_status"]]["answer"]
        == "Needs new profile"
    ):
        return False
    return True


def _get_participants_from_welcome_form(
    api_key: str, form_id: str, filters: list, indices: dict
) -> list:
    new_submissions = get_form_responses(api_key, form_id, filters)
    new_participants = []
    for submission in new_submissions:
        baton_log.info(
            f"Creating participant data object from submission {submission['id']}"
        )
        new_participants.append(
            {
                "jotform_submission_id": submission["id"],
                "first_name": answer_or_blank(submission, indices["name"], "first"),
                "last_name": answer_or_blank(submission, indices["name"], "last"),
                "gender": answer_or_blank(submission, indices["gender"]),
                "preferred_language": answer_or_blank(
                    submission, indices["preferred_language"]
                ),
                "email": answer_or_blank(submission, indices["email"]),
                "phone": answer_or_blank(submission, indices["phone"]),
                "postal_code": answer_or_blank(
                    submission, indices["postal_code"]
                ).replace(" ", ""),
                "submission_status": answer_or_blank(
                    submission, indices["submission_status"]
                ),
            }
        )
    return new_participants


def get_new_participants_from_welcome_form(
    api_key: str, welcome_form_config: object
) -> list:
    baton_log.info("Requesting new submissions from Jotform Welcome Form.")
    indices = welcome_form_config["indices"]
    # If submissions have a value in "Submission status", filter them out
    filters = [
        lambda submission: "answer"
        in submission["answers"][indices["submission_status"]]
    ]
    return _get_participants_from_welcome_form(
        api_key, welcome_form_config["form_id"], filters, indices
    )


def get_confirmed_non_duplicate_participants_from_welcome_form(
    api_key: str, welcome_form_config: object
) -> list:
    baton_log.info(
        "Requesting latest submissions confirmed as non-duplicates from Jotform Welcome Form."
    )
    indices = welcome_form_config["indices"]
    # If submissions have a value in "Submission status", filter them out
    filters = [
        lambda submission: _only_submissions_which_definitely_must_be_entered_into_ocms_filter(
            submission, indices
        )
    ]
    return _get_participants_from_welcome_form(
        api_key, welcome_form_config["form_id"], filters, indices
    )


def update_participant_submission_as_possible_duplicate(
    api_key: str, submission_id: str, config: object
):
    """POST update status as possible duplicate in Welcome Form"""
    status = "Possible duplicate"
    request_body = {
        f"submission[{config['jotform']['welcome_form']['indices']['submission_status']}]": status
    }
    update_participant_submission(api_key, submission_id, request_body, config["http"])
    baton_log.info(f"Updated submission status of {submission_id} to {status}")


def update_participant_submission_as_added_to_ocms(
    api_key: str, submission_id: str, config: object
):
    """POST update status as added to ocms in Welcome Form"""
    status = "Added to OCMS"
    request_body = {
        f"submission[{config['jotform']['welcome_form']['indices']['submission_status']}]": status
    }
    update_participant_submission(api_key, submission_id, request_body, config["http"])
    baton_log.info(f"Updated submission status of {submission_id} to {status}")


def update_participant_submission_ocms_id(
    api_key: str, submission_id: str, ocms_id: int, config: object
):
    """POST submission status with OCMS ID in Welcome Form"""
    request_body = {
        f"submission[{config['jotform']['welcome_form']['indices']['ocms_id']}]": str(
            ocms_id
        )
    }
    update_participant_submission(api_key, submission_id, request_body, config["http"])
    baton_log.info(f"Updated OCMS ID of {submission_id} to {ocms_id}")
