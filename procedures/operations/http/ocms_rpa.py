from datetime import datetime
from re import search as regex
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
import time
from typing import Callable
from operations.http.rpa import (
    element_exists,
    wait_and_get_element,
    wait_and_send_keys_to_element,
    wait_and_click_element,
    wait_and_hit_enter,
    wait_and_select_element_from_dropdown,
    wait_for_element_to_be_clickable,
    wait_for_element_to_be_visible,
    wait_scroll_and_click_element,
    dismiss_alert,
)
from operations.local.logging import baton_log


comment_indicating_registration_form_is_not_yet_submitted_and_processed = (
    "Waiting for registration form"
)


def _get_home_url(url: str):
    return f"{url}/default.aspx"


def _navigate_to_home_page_then_navbar_link(
    driver: WebDriver, navbar_id: str, url: str
):
    """Navigate to home page, then to navbar link."""
    driver.get(_get_home_url(url))
    time.sleep(5)
    wait_and_click_element(driver, By.ID, navbar_id)


def _navigate_to_home_page_then_navbar_link_xpath(
    driver: WebDriver, navbar_xpath: str, url: str
):
    """Navigate to home page, then to navbar link."""
    driver.get(_get_home_url(url))
    wait_and_click_element(driver, By.XPATH, navbar_xpath)


def _update_phone_number(driver: WebDriver, phone_number: str):
    phone_number = phone_number.split("-")
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtTelephone_I",
        "",
    )
    time.sleep(3)
    for digits in phone_number:
        wait_and_send_keys_to_element(
            driver,
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtTelephone_I",
            digits,
            clear=False,
        )
        time.sleep(3)


def _update_custom_nych_questions(driver: WebDriver):
    def _update_custom_question(row: int, answer: str):
        answer_selector = (
            lambda answer: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_panelCustomAgencyItems_ucCustomAgencyModule_GridCustomAgencyItems_DXEditor12_DDD_L_LBT']//td[text()='{answer}']"
        )
        wait_scroll_and_click_element(
            driver,
            By.ID,
            f"ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_panelCustomAgencyItems_ucCustomAgencyModule_GridCustomAgencyItems_DXDataRow{str(row)}",
        )
        time.sleep(5)
        wait_and_select_element_from_dropdown(
            driver,
            (
                By.ID,
                "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_panelCustomAgencyItems_ucCustomAgencyModule_GridCustomAgencyItems_DXEditor12_B-1Img",
            ),
            (By.XPATH, answer_selector(answer)),
        )
        wait_and_click_element(
            driver,
            By.ID,
            f"ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_panelCustomAgencyItems_ucCustomAgencyModule_GridCustomAgencyItems_DXCBtn{row}",
        )
        # Because clicking 'Update' on an Agency Specific Questions freezes the page
        time.sleep(5)

    _update_custom_question(0, "Yes")
    _update_custom_question(1, "No")
    _update_custom_question(2, "No")


def _update_participant_language(driver: WebDriver, language: str):
    language_selector = (
        lambda language: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_GridClientLanguage_DXEditor1_DDD_L_LBT']//td[contains(text(),'{language}')]"
    )
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_GridClientLanguage_header0_AddNew",
    )
    time.sleep(5)
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_GridClientLanguage_DXEditor1_B-1Img",
    )
    if wait_for_element_to_be_clickable(driver, By.XPATH, language_selector(language)):
        wait_and_click_element(driver, By.XPATH, language_selector(language))
        # Update language button
        wait_and_click_element(
            driver,
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_GridClientLanguage_DXCBtn0",
        )
    else:
        # Cancel adding language button, if matching language is not found
        wait_and_click_element(
            driver,
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_GridClientLanguage_DXCBtn1",
        )
    # Because clicking 'Update' on language selection freezes the page
    time.sleep(5)


def _navigate_to_participant_profile(driver: WebDriver, ocms_id: str, url: str):
    baton_log.info(f"Navigating to client profile with OCMS ID {ocms_id}")
    _navigate_to_home_page_then_navbar_link_xpath(
        driver, "//li[@title='Find Client or Group Activity in My Agency']", url
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelNamed_txtClientId_I",
        ocms_id,
    )
    wait_and_click_element(
        driver, By.ID, "ctl00_ContentTitle_ContentPlaceHolderMaster_Button_Search_CD"
    )
    # When the OCMS search finds the matching profile, then click the profile link
    wait_and_click_element(
        driver, By.ID, "ctl00_ContentTitle_ContentPlaceHolderMaster_GridMaster_DXCBtn0"
    )


def _add_comment(driver: WebDriver, comment: str, overwrite_existing=False):
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtComments_I",
        comment,
        clear=overwrite_existing,
    )


def _remove_comment(driver: WebDriver, comment: str):
    existing_text = wait_and_get_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtComments_I",
    ).text
    text_without_comment = existing_text.replace(comment, "")
    _add_comment(driver, text_without_comment, overwrite_existing=True)


def _populate_dropdown_with_option(
    driver: WebDriver,
    by: By,
    input_element_selector: str,
    option: str,
    input_clear_button_selector=None,
):
    """This is unfortunately what is required to populate and select an item inside the list of a
    dropdown element on OCMS using Robotic Process Automation. I am fairly certain they intentionally
    designed dropdowns to be difficult to automate.
    """
    baton_log.info(
        f"Attempting to populate dropdown under '{input_element_selector}' with '{option}'"
    )
    explicit_wait_time = 3  # seconds
    baton_log.debug(
        f"sleeping {explicit_wait_time} before interacting with input dropdown"
    )
    time.sleep(explicit_wait_time)
    wait_for_element_to_be_clickable(
        driver, by, input_element_selector, valid_exceptions=()
    )
    # Click inside the input box
    input_element = driver.find_element(by, input_element_selector)
    input_element.click()
    baton_log.debug(f"sleeping {explicit_wait_time} after clicking input box")
    time.sleep(explicit_wait_time)
    if input_clear_button_selector:
        # Then click the button which clears the contents of the cell
        driver.find_element(by, input_clear_button_selector).click()
    else:
        # If we are missing a clear button, then select all text...
        input_element.send_keys(Keys.CONTROL, "a")
    baton_log.debug(
        f"sleeping {explicit_wait_time} after attempting to clear form field"
    )
    time.sleep(explicit_wait_time)
    input_element.send_keys(option)
    baton_log.debug(f"sleeping {explicit_wait_time} after sending option text {option}")
    time.sleep(explicit_wait_time)
    wait_and_hit_enter(driver, by, input_element_selector)
    baton_log.debug(f"sleeping {explicit_wait_time} after hitting enter")
    time.sleep(explicit_wait_time)
    # TODO: See if this is still required for dropdowns with a clear button. It is not required (and
    # disrupts) dropdowns without a clear button.
    # if input_clear_button_selector:
    #     driver.execute_script("arguments[0].click();", input_element)
    # input_element.click()


def _wait_and_populate_dropdown_then_select_element(
    driver: WebDriver, by: By, input_element_selector: str, option: str, verbose=False
):
    """Handles select dropdowns that are not pre-populated on page load. Also only applies to
    select dropdowns which do not respond to an ordinary element.clear() command, requiring a
    click on a clear button on the page.
    """
    if option == "":
        # Because hitting enter later with "-- Not Set --" text refreshes the form for some reason
        return
    _populate_dropdown_with_option(driver, by, input_element_selector, option, None)


def _wait_and_populate_dropdown_with_clear_button_then_select_element(
    driver: WebDriver,
    by: By,
    input_element_selector: str,
    input_clear_button_selector: str,
    selector_function: Callable,
    option: str,
    fallback_option=None,
    clear_on_fallback=False,
):
    """Handles select dropdowns that are not pre-populated on page load. Also only applies to
    select dropdowns which do not respond to an ordinary element.clear() command, requiring a
    click on a clear button on the page.
    """
    if option == "":
        # Because hitting enter later with "-- Not Set --" text refreshes the form for some reason
        return
    _populate_dropdown_with_option(
        driver,
        by,
        input_element_selector,
        option,
        input_clear_button_selector,
    )
    if element_exists(
        driver=driver,
        by=By.XPATH,
        selector=f"//td[text() = '{option}'][contains(@class, 'dxeListBoxItemSelected_DevEx')]",
        element_not_found_message=f"Could not find selected '{option}' option.",
    ):
        return
    elif fallback_option:
        _populate_dropdown_with_option(
            driver,
            by,
            input_element_selector,
            fallback_option,
            input_clear_button_selector,
        )
    elif clear_on_fallback:
        baton_log.info(f"Reverting to the default selection by clearing field.")
        driver.find_element(by, input_clear_button_selector).click()
    else:
        raise Exception(
            f"Unable to select select dropdown option {option} with selector {selector_function(option)}"
        )


def login(driver: WebDriver, username: str, password: str, url: str):
    """Returns an ocms_id if a new user is created, empty string if not."""
    driver.get(url)
    wait_and_send_keys_to_element(driver, By.ID, "panelLogin_txtUserName_I", username)
    wait_and_send_keys_to_element(driver, By.ID, "panelLogin_txtPassword_I", password)
    wait_and_click_element(driver, By.CSS_SELECTOR, "#panelLogin_btnLogin_CD > span")
    if wait_for_element_to_be_visible(
        driver,
        By.ID,
        "panelResetPassword_lblForcePWChangeTitle",
        valid_exceptions=(TimeoutException),
        wait_time=8,
    ):
        raise Exception(
            f"The password for {username} is expired. Please log into OCMS and update it."
        )


def select_site_hierarchy(driver, select_entire_org=True):
    driver.switch_to.frame(
        "ctl00_ContentTitle_ContentPlaceHolderMaster_pcLocationFinder_CIF-1"
    )
    time.sleep(2)
    if select_entire_org:
        wait_and_click_element(
            driver,
            By.XPATH,
            "//td[contains(text(), 'North York Community House')]",
        )
    else:
        wait_and_click_element(
            driver,
            By.XPATH,
            "//td[contains(text(), 'NYCH Central Office')]",
        )
    # time.sleep(999)
    # wait_and_click_element(
    #     driver, By.ID, "ctl00_ContentPlaceHolderMaster_TreeMaster_R-8866"
    # )
    time.sleep(2)
    wait_and_click_element(driver, By.ID, "ctl00_ContentPlaceHolderMaster_BtnSelect_CD")
    # ctl00_ContentPlaceHolderMaster_TreeMaster_R-16854
    driver.switch_to.default_content()


def _check_and_download_report(driver, text, max_wait_time, time_waited=0):
    """Check back periodically to see when the report is done (should take no longer than 5
    minutes).
    """
    time_to_wait = 30  # seconds
    if time_waited > max_wait_time:
        raise Exception(
            f"Timed out waiting for report to download after {max_wait_time} seconds."
        )
    wait_and_click_element(driver, By.ID, "ctl00_panelIndicator_sysReportIndicator")
    driver.switch_to.frame("ctl00_pcBriefcase_CIF-1")
    # If the name of the report is not yet a link, it is not ready for download
    if wait_for_element_to_be_visible(
        driver,
        By.XPATH,
        f"//tr[@id='ctl00_ContentPlaceHolderMaster_GridMaster_DXDataRow0']/td[contains(text(), '{text}')]",
    ):
        # driver.find_element(
        #     By.ID, "ctl00_ContentPlaceHolderMaster_GridMaster_DXMainTable"
        # ).send_keys(Keys.ESCAPE)
        # actions = ActionChains(driver)
        # actions.send_keys(Keys.ESCAPE)
        # actions.perform()
        driver.switch_to.default_content()
        wait_and_click_element(driver, By.ID, "ctl00_pcBriefcase_HCB-1")
        time.sleep(time_to_wait)
        # Recursively check again
        _check_and_download_report(
            driver, text, max_wait_time, time_waited + time_to_wait
        )
        return
    # If the name of the report has become a link, it is ready for download
    wait_and_click_element(
        driver,
        By.XPATH,
        f"//tr[@id='ctl00_ContentPlaceHolderMaster_GridMaster_DXDataRow0']//a[contains(text(), '{text}')]",
    )
    driver.switch_to.default_content()


def download_ocms_recent_visits_report(
    driver: WebDriver,
    date_start: datetime,
    date_end: datetime,
    program_name: str,
    max_wait_time: int,
    url: str,
):
    date_pattern = "%Y/%m/%d"
    date_start_str = date_start.strftime(date_pattern)
    date_end_str = date_end.strftime(date_pattern)
    report_name = "Visits Report"
    baton_log.info(
        f"Requesting new {report_name} in OCMS from {date_start_str} to {date_end_str}"
    )
    # Navigate to home page, click My Reports, then Client Contact List
    _navigate_to_home_page_then_navbar_link_xpath(
        driver, "//li[@title='My Reports']", url
    )
    wait_and_click_element(driver, By.XPATH, f"//a[contains(text(), '{report_name}')]")
    # Fill out the submission form and submit
    _wait_and_populate_dropdown_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlPartner_I']",
        program_name,
    )
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_FindLocation_CD",
    )
    select_site_hierarchy(driver)
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateServiceDateFrom_I",
        date_start_str,
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateServiceDateTo_I",
        date_end_str,
    )
    _wait_and_populate_dropdown_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlOFormat_I']",
        "Microsoft Excel",
    )
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_Execute_Job_CD",
    )
    # Wait 5 seconds for new report to show up
    time.sleep(5)
    _check_and_download_report(driver, report_name, max_wait_time)


def download_ocms_clients_report(
    driver: WebDriver,
    date_start: datetime,
    date_end: datetime,
    max_wait_time: int,
    url: str,
):
    date_pattern = "%Y/%m/%d"
    date_start_str = date_start.strftime(date_pattern)
    date_end_str = date_end.strftime(date_pattern)
    report_name = "Client Contact List"
    baton_log.info(
        f"Requesting new {report_name} in OCMS from {date_start_str} to {date_end_str}"
    )
    # Navigate to home page, click My Reports, then Client Contact List
    _navigate_to_home_page_then_navbar_link_xpath(
        driver, "//li[@title='My Reports']", url
    )
    wait_and_click_element(driver, By.XPATH, f"//a[contains(text(), '{report_name}')]")
    # Fill out the submission form and submit
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_FindLocation_CD",
    )
    select_site_hierarchy(driver)
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateServiceDateFrom_I",
        date_start_str,
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateServiceDateTo_I",
        date_end_str,
    )
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_Execute_Job_CD",
    )
    # Wait 5 seconds for new report to show up
    time.sleep(5)
    _check_and_download_report(driver, report_name, max_wait_time)


def create_participant(
    driver: WebDriver,
    user_info: object,
    ignore_ocms_duplicate_detection: bool,
    url: str,
) -> str:
    """Creates participant in OCMS. Checks for duplicates found.
    Returns ocms_id if created, and '' if it was not able to be created.
    """
    _navigate_to_home_page_then_navbar_link_xpath(
        driver, "//li[@title='Register New Client']", url
    )
    wait_and_click_element(
        driver,
        By.CSS_SELECTOR,
        "td#ctl00_ContentTitle_ContentPlaceHolderMaster_MasterNews_ICell > table > tbody > tr > td > table >tbody > tr > td:nth-child(3) > div > a",
    )
    baton_log.info(
        f"Submitting {user_info['first_name']} {user_info['last_name']} with Jotform Unique ID {user_info['jotform_submission_id']} in OCMS"
    )
    # Select 'Yes' from dropdown for privacy agreement
    wait_and_select_element_from_dropdown(
        driver,
        (
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelTop_ddlAcceptedPrivacyStatement_I",
        ),
        (
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelTop_ddlAcceptedPrivacyStatement_DDD_L_LBI1T0",
        ),
    )
    # Fill out the rest of the form
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtFirstName_I",
        user_info["first_name"],
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtLastName_I",
        user_info["last_name"],
    )
    time.sleep(5)
    gender_selector = (
        lambda gender: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlGender_DDD_L_LBT']//td[contains(text(),'{gender}')]"
    )
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlGender_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlGender_B0']",
        gender_selector,
        user_info["gender"],
        "Other",
    )
    # wait_and_send_keys_to_element(driver, By.ID, 'ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateDOB_I', user_info['birth_date'])
    if "preferred_language" in user_info:
        language_selector = (
            lambda language: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlOfficialLanguage_DDD_L_LBT']//td[contains(text(),'{language}')]"
        )
    wait_and_select_element_from_dropdown(
        driver,
        (
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlOfficialLanguage_B-1Img",
        ),
        (By.XPATH, language_selector(user_info["preferred_language"])),
        (By.XPATH, language_selector("Unknown")),
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtEmail_I",
        user_info["email"],
    )
    _update_phone_number(driver, user_info["phone"])
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtAddressPostalCode13_I",
        user_info["postal_code"][:3],
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtAddressPostalCode46_I",
        user_info["postal_code"][3:],
    )
    _update_custom_nych_questions(driver)
    _add_comment(
        driver, comment_indicating_registration_form_is_not_yet_submitted_and_processed
    )
    # Select "Registration Site"
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_FindLocation_CD",
    )
    select_site_hierarchy(driver, select_entire_org=False)
    # Submit form
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_CheckDuplicates_CD",
    )
    # Dismiss alert for not having a pre-filled OCMS id on new user creation
    # TODO: Decide whether it's required for both of these  dismiss_alerts to be kept.
    # NOTE: the alert was sometimes being canceled by the wait_for_element_to_be_clickable
    # function when duplicates_modal_cancel_button_selector was not present.
    dismiss_alert(driver, "No alert detected on first attempt to dismiss alert")
    # Check for OCMS detecting a duplicate
    duplicates_modal_cancel_button_selector = "ctl00_ContentTitle_ContentPlaceHolderMaster_pcDuplicateControl_BtnCancelDuplicate_CD"
    duplicates_modal_ignore_and_submit_selector = (
        "ctl00_ContentTitle_ContentPlaceHolderMaster_pcDuplicateControl_BtnSaveClient"
    )
    if wait_for_element_to_be_clickable(
        driver,
        by=By.ID,
        selector=duplicates_modal_cancel_button_selector,
        element_not_found_message="No duplicates detected by OCMS",
        valid_exceptions=(TimeoutException, UnexpectedAlertPresentException),
    ):
        if not ignore_ocms_duplicate_detection:
            baton_log.info("Detected potential duplicate in OCMS")
        wait_and_click_element(driver, By.ID, duplicates_modal_cancel_button_selector)
        return ""
        baton_log.info(
            f"Ignoring OCMS detection of a possible duplicate. ignore_ocms_duplicate_detection: {ignore_ocms_duplicate_detection}"
        )
        wait_and_click_element(
            driver, By.ID, duplicates_modal_ignore_and_submit_selector
        )
    # TODO: Decide whether it's required for both of these  dismiss_alerts to be kept.
    # NOTE: the alert was sometimes being canceled by the wait_for_element_to_be_clickable
    # function when duplicates_modal_cancel_button_selector was not present.
    dismiss_alert(driver, "No alert detected on second attempt to dismiss alert")
    # Ensure OCMS submission worked - i.e. we are on the page indicating the client was created.
    baton_log.info(f"Submitting client profile in OCMS, awaiting confirmation.")
    if wait_for_element_to_be_visible(
        driver,
        by=By.XPATH,
        selector="//span[contains(text(), 'Confirmed, a client profile has been created for this user.')]",
        element_not_found_message=f"Client profile for jotform_submission_id {user_info['jotform_submission_id']} was not succesfully created",
    ):
        # Get OCMS ID of new user
        time.sleep(5)
        name_and_ocms_id_str = driver.find_element(
            By.ID,
            "ctl00_ContentTitle_ContentPlaceHolderMaster_panelConfirmation_txtConfirmationClientName_I",
        ).get_attribute("value")
        baton_log.info(f"Created {name_and_ocms_id_str}. Extracting OCMS ID.")
        ocms_id = regex("(?<=\().+?(?=\))", name_and_ocms_id_str).group()
        baton_log.info(f"OCMS ID of newly created client profile is {ocms_id}")
        return ocms_id
    # ... and if it didn't work, log why it didn't work so we can debug it more easily, then flag
    # it as a potential duplicate requiring review.
    else:
        all_possible_entry_error_elems = driver.find_elements(
            By.XPATH, "//img[contains(@class, 'dxEditors_edtError_PlasticBlue')]"
        )
        active_error_elems = [
            element
            for element in all_possible_entry_error_elems
            if element.is_displayed()
        ]
        baton_log.info(
            f"{len(active_error_elems)} reasons for being unable to create new client profile for submission:"
        )
        for element in active_error_elems:
            baton_log.info(
                f"{element.get_attribute('title')} on element with id {element.get_attribute('id')}"
            )
        return ""


def update_participant(driver: WebDriver, user_info: object, url: str) -> bool:
    """Updates existing participant in OCMS."""
    _navigate_to_participant_profile(driver, user_info["ocms_id"], url)
    baton_log.info(
        f"Updating submission with Jotform Registration Form ID {user_info['jotform_submission_id']} and OCMS ID {user_info['ocms_id']}"
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateDateOfLanding_I",
        user_info["landing_date"],
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_dateDateOfArrival_I",
        user_info["arrival_date"],
    )
    country_of_origin_selector = (
        lambda country_of_origin: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlCountryOfOrigin_DDD_L_LBT']//td[contains(text(),'{country_of_origin}')]"
    )
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlCountryOfOrigin_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlCountryOfOrigin_B0']",
        country_of_origin_selector,
        user_info["country_of_origin"],
        "-- Not Set --",
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtAddressStreetNo_I",
        user_info["street_number"],
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtAddressStreetName_I",
        user_info["street_name"],
    )
    street_type_selector = (
        lambda street_type: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlAddressStreetType_DDD_L_LBT']//td[contains(text(),'{street_type}')]"
    )
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlAddressStreetType_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlAddressStreetType_B0']",
        street_type_selector,
        user_info["street_type"],
        "-- Not Set --",
    )
    street_direction_selector = (
        lambda street_direction: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlAddressStreetDirection_DDD_L_LBT']//td[contains(text(),'{street_direction}')]"
    )
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlAddressStreetDirection_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlAddressStreetDirection_B0']",
        street_direction_selector,
        user_info["street_direction"],
        clear_on_fallback=True,
    )
    wait_and_send_keys_to_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_txtAddressStreetUnit_I",
        user_info["unit_number"],
    )
    employment_status_selector = (
        lambda employment_status: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlEmploymentStatus_DDD_L_LBT']//td[contains(text(),'{employment_status}')]"
    )
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlEmploymentStatus_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlEmploymentStatus_B0']",
        employment_status_selector,
        user_info["employment_status"],
        clear_on_fallback=True,
    )
    # NOTE: Single and double quotes have been inverted here intentionally, so that single quotes do
    # not break the Xpath selector.
    highest_education_selector = (
        lambda highest_education: f'//table[@id="ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlEducationLevel_DDD_L_LBT"]//td[contains(text(),"{highest_education}")]'
    )
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlEducationLevel_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlEducationLevel_B0']",
        highest_education_selector,
        user_info["education_level"],
        clear_on_fallback=True,
    )
    _update_participant_language(driver, user_info["primary_language"])
    if user_info["secondary_language"]:
        _update_participant_language(driver, user_info["secondary_language"])
    housing_status_selector = (
        lambda housing_status: f"//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_DDD_L_LBT']//td[contains(text(),'{housing_status}')]"
    )
    print("Check here")
    print(housing_status_selector(user_info["housing_status"]))
    print(
        "//table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_DDD_L_LBT']//td[contains(text(),'Not Set')]"
    )
    # print("Sleeping")
    # time.sleep(9999)
    # Clicks //input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_I']
    # then clears fields contents with //td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_B0']
    # then
    # then tries and fails on //table[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_DDD_L_LBT']//td[contains(text(),'Not Set')]
    _wait_and_populate_dropdown_with_clear_button_then_select_element(
        driver,
        By.XPATH,
        "//input[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_I']",
        "//td[@id='ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_ddlHousingStatus_B0']",
        housing_status_selector,
        user_info["housing_status"],
        clear_on_fallback=True,
    )
    time.sleep(5)
    _remove_comment(
        driver, comment_indicating_registration_form_is_not_yet_submitted_and_processed
    )
    wait_and_click_element(
        driver,
        By.ID,
        "ctl00_ContentTitle_ContentPlaceHolderMaster_panelMain_Button_CheckDuplicates_CD",
    )
    dismiss_alert(driver, "No alert detected on first attempt to dismiss alert")
    # Check that the profile was successfully saved
    time.sleep(5)
    wait_for_element_to_be_visible(
        driver,
        By.XPATH,
        "//div[@id='ctl00_FF_SystemInformationContainer']/span[contains(text(), 'Client was successfully saved')]",
    )
    return True
