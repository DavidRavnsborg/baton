from operations.http.rpa import (
    wait_and_get_element,
    wait_and_send_keys_to_element,
    wait_and_click_element,
    wait_scroll_and_ctrl_click_element,
    wait_and_hit_enter,
    wait_and_select_element_from_dropdown,
    wait_for_element_to_be_clickable,
    wait_for_element_to_be_visible,
    dismiss_alert,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from time import sleep


def navigate_to_my_reports(driver: WebDriver):
    driver.get("https://choicesforyouth.emhware.ca/reports/")
    # wait_and_click_element(
    #   driver = driver,
    #   by = By.XPATH,
    #   selector = "//td[contains(@title, 'Reports')]//img[contains(@alt, 'Reports Icon')]"
    # )
    wait_and_click_element(
        driver=driver, by=By.ID, selector="idSpan_idButtonFavoriteReportMenu"
    )


def select_pinned_report(driver: WebDriver, report: str):
    wait_scroll_and_ctrl_click_element(
        driver=driver, by=By.XPATH, selector=f"//tr//td[contains(text(), '{report}')]"
    )


def select_report_from_list(driver: WebDriver, report: str):
    wait_and_click_element(
        driver=driver, by=By.XPATH, selector=f"//option[@title = {report}]"
    )


def select_report_date(driver: WebDriver, date: str, id: str):
    date_element = wait_and_get_element(driver=driver, by=By.ID, selector=id)
    driver.execute_script(
        "arguments[0].setAttribute('value', arguments[1])", date_element, date
    )


def select_report_date_range(
    driver: WebDriver,
    start_date: str,
    end_date="",
    input_id_start="idCalDateaStartDate",
    input_id_end="idCalDateaEndDate",
):
    select_report_date(driver, start_date, input_id_start)

    # TODO: make sure this works
    if end_date == None:
        return
    select_report_date(driver, end_date, input_id_end)


def select_all_activities(driver: WebDriver):
    wait_and_click_element(driver=driver, by=By.ID, selector="idaActivityIdsSelectAll")


def select_all_methods(driver: WebDriver):
    wait_and_click_element(driver=driver, by=By.ID, selector="idaMethodCdsSelectAll")


def select_program(driver: WebDriver, program: str):
    wait_and_select_element_from_dropdown(
        driver,
        by_selector_tuple_dropdown=(By.ID, "idaProgramId"),
        by_selector_tuple_option=(
            By.XPATH,
            f"//select[@id='idaProgramId']//option[@title='{program}']",
        ),
        throw_exception=True,
    )


def select_all_programs(driver: WebDriver):
    wait_and_click_element(driver=driver, by=By.ID, selector="idaProgramIdsSelectAll")


def select_all_workers(driver: WebDriver):
    # We actually have to unselect all workers in order to select all workers, because selecting all
    # only selects our own user as a worker.
    wait_and_click_element(driver=driver, by=By.ID, selector="idaWorkerIdsUnselectAll")


def select_case_date_type(driver: WebDriver, case_data_type):
    wait_and_select_element_from_dropdown(
        driver,
        (By.ID, "idTd_aTypeCd"),
        (By.XPATH, f"//td[@id='idTd_aTypeCd']//option[@title='{case_data_type}']"),
    )


def select_case_data_results_field_list(driver: WebDriver, field: str):
    try:
        # XPath's title wrapped in single quotes
        selector = f"//select[@id='idaFieldIds']//option[contains(@title, '{field}')]"
        wait_scroll_and_ctrl_click_element(driver, By.XPATH, selector)
    except:
        # XPath's title wrapped in double quotes
        print(
            f"Could not select {field} with single quotes around title in XPath, trying double quotes."
        )
        selector = f'//select[@id="idaFieldIds"]//option[contains(@title, "{field}")]'
        wait_scroll_and_ctrl_click_element(driver, By.XPATH, selector)


def select_emhware_report_fields(driver: WebDriver):
    raise NotImplementedError()


def run_report(driver: WebDriver):
    wait_and_click_element(driver=driver, by=By.ID, selector="idImg_idButtonRun")


def download_report(driver: WebDriver):
    wait_and_click_element(
        driver=driver, by=By.ID, selector="idButtonCSV", wait_time=45
    )
