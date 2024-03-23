import os
from operations.http.jotform.base import (
    get_form_responses,
    format_jotform_date,
    answer_or_blank,
    update_participant_submission,
    get_submission,
)
from operations.local.config import read_yaml
from operations.local.logging import baton_log


# class RegistrationForm:
#   def __init__(self, api_key):
#     self.api_key = api_key


def _submission_has_already_been_entered_into_ocms_filter(submission):
    """Only includes submissions which have been entered into OCMS by Robotic Process Automation.
    NOTE: True indicates the submission gets filtered out, False indicates it gets included.
    """
    if "33" not in submission["answers"] or "answer" not in submission["answers"]["33"]:
        return False
    # Cast string field to int (Jotform sends a string), then to bool, otherwise "0" == True
    try:
        return bool(int(submission["answers"]["33"]["answer"]))
    # This may only be temporarily required since I set the value of this to True rather than 1 or 0
    except:
        return bool(submission["answers"]["33"]["answer"])


def _map_jotform_education_to_ocms_education(education_level):
    """TODO: Move this to a common DTO object that can handle mappings - this is being implemented
    before we have a dedicated layer for that, but it's ultimately where these types of mappings
    should live.
    """
    mapping = read_yaml("data/education_jotform_to_ocms.yaml")
    # Some credential types were failing, because they come back as a key-value pair rather than a value. e.g. {'other': 'Phd'}
    if isinstance(education_level, dict):
        education_level = list(education_level.values())[0]
    if education_level in mapping:
        return mapping[education_level]
    return mapping["default"]


def get_participants_from_registration_form(
    api_key: str, registration_form_config: object
) -> list:
    baton_log.info("Requesting submissions from Jotform Registration Form.")
    indices = registration_form_config["indices"]
    # If submissions are marked as "Updated in OCMS", filter them out
    filters = [
        _submission_has_already_been_entered_into_ocms_filter,
    ]
    new_submissions = get_form_responses(
        api_key, registration_form_config["form_id"], filters
    )
    registered_participants = []
    for submission in new_submissions:
        baton_log.info(
            f"Creating participant data object from submission {submission['id']}"
        )
        registered_participants.append(
            {
                "jotform_submission_id": submission["id"],
                "welcome_form_submission_id": answer_or_blank(
                    submission, indices["welcome_form_submission_id"]
                ),
                "landing_date": format_jotform_date(
                    answer_or_blank(submission, indices["landing_date"])
                ),
                "arrival_date": format_jotform_date(
                    answer_or_blank(submission, indices["arrival_date"])
                ),
                "country_of_origin": answer_or_blank(
                    submission, indices["country_of_origin"]
                ),
                "street_number": answer_or_blank(submission, indices["street_number"]),
                "street_name": answer_or_blank(submission, indices["street_name"]),
                "street_type": answer_or_blank(submission, indices["street_type"]),
                "street_direction": answer_or_blank(
                    submission, indices["street_direction"]
                ),
                "unit_number": answer_or_blank(submission, indices["unit_number"]),
                "employment_status": answer_or_blank(
                    submission, indices["employment_status"]
                ),
                "education_level": _map_jotform_education_to_ocms_education(
                    answer_or_blank(submission, indices["education_level"])
                ),
                "primary_language": answer_or_blank(
                    submission, indices["primary_language"]
                ),
                "secondary_language": answer_or_blank(
                    submission, indices["secondary_language"]
                ),
                "housing_status": answer_or_blank(
                    submission, indices["housing_status"]
                ),
            }
        )
    return registered_participants


def update_participant_submission_updated_in_ocms(
    api_key: str, submission_id: str, http_config: object
):
    """POST submission status as Updated in OCMS in Registration Form"""
    request_body = {"submission[33]": 1}
    update_participant_submission(api_key, submission_id, request_body, http_config)
    baton_log.info(
        f"Updated Updated in OCMS status of {submission_id} from 0 (unchecked) to 1 (checked)"
    )
