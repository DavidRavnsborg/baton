from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException

# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from typing import Callable
from operations.local.logging import baton_log


# TODO: Move to config file - requires small refactor, see note in config file
implicit_wait_time = 30


def initialize_driver(config) -> WebDriver:
    """Initialize a local Selenium Driver."""
    downloads_folder = config["storage"]["downloads_folder"]
    # chromedriver_autoinstaller has a bug affecting versions 115+. Using manually downloaded driver
    # for now: https://github.com/yeongbin-jo/python-chromedriver-autoinstaller/issues/53
    # chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
    #                                       # and if it doesn't exist, download it automatically,
    #                                       # then add chromedriver to path
    # options = webdriver.ChromeOptions()
    options = webdriver.FirefoxOptions()
    # Sets the download folder before driver initialization - doesn't work for headless runs
    if downloads_folder != "":
        # Pre-initialization config for downloads
        prefs = {
            "download.prompt_for_download": False,
            "download.default_directory": downloads_folder,
        }
        # options.add_experimental_option("prefs", prefs)
    if config["rpa"]["headless"]:
        baton_log.info("Running RPA in headless mode.")
        options.add_argument("--headless")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", downloads_folder)
    # driver = webdriver.Chrome(service=Service(), options=options)
    driver = webdriver.Firefox(service=Service(), options=options)
    baton_log.info("Driver initialized.")
    # Sets the download folder after driver initialization - only works for headless runs
    if downloads_folder != "" and isinstance(driver, webdriver.Chrome):
        # Post-initialization config for downloads.
        # Headless downloads haven't worked in recent Selenium Chromedriver versions (and
        # Geckodriver/Firefox haven't been working on Linux with the selenium/standalone-firefox base
        # docker image).
        # This is overrides the default headless download behaviour, from this StackOverflow and the
        # attached Chromium discussion thread:
        # https://stackoverflow.com/a/47366981/724403
        driver.command_executor._commands["send_command"] = (
            "POST",
            "/session/$sessionId/chromium/send_command",
        )
        params = {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": downloads_folder},
        }
        command_result = driver.execute("send_command", params)
        baton_log.info(
            f"Result of setDownloadBehavior command on driver: {command_result}"
        )
    # elif downloads_folder != "" and isinstance(driver, webdriver.Firefox):
    #     print("YOLO")
    #     # driver.command_executor._commands["SET_CONTEXT"] = (
    #     #     "POST",
    #     #     "/session/$sessionId/moz/context",
    #     # )
    #     # driver.execute("SET_CONTEXT", {"context": "firefox"})
    #     # driver.execute_script(
    #     #     """
    #     #     Services.prefs.setBoolPref('browser.download.useDownloadDir', true);
    #     #     Services.prefs.setStringPref('browser.download.dir', arguments[0]);
    #     #     """,
    #     #     downloads_folder,
    #     # )
    #     # driver.execute("SET_CONTEXT", {"context": "content"})
    #     options = Options()
    #     # options.set_preference("browser.download.folderList", 2)
    #     # options.set_preference("browser.download.manager.showWhenStarting", False)
    #     options.set_preference("browser.download.dir", downloads_folder)
    #     # options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
    driver.implicitly_wait(config["rpa"]["implicit_wait_time"])
    driver.maximize_window()
    return driver


def intialize_remote_driver() -> WebDriver:
    """TODO"""
    raise NotImplementedError


def quit_driver(driver):
    """Termine execution of a local Selenium Driver.

    The extra wait time just provides some padding in-case a download or other operation is still
    in progress.
    """
    time_to_wait_before_quitting = 8
    baton_log.info(
        f"Job finished, exiting driver in {time_to_wait_before_quitting} seconds..."
    )
    time.sleep(time_to_wait_before_quitting)
    driver.quit()
    baton_log.info("Driver exited sucessfully.")


def dismiss_alert(driver: WebDriver, message_on_exception):
    try:
        # This keeps skipping past the alert without a time.sleep first
        wait_time = 5
        baton_log.info(
            f"Sleeping {wait_time} seconds before attempting to dismiss alert"
        )
        time.sleep(wait_time)
        Alert(driver).accept()
    except NoAlertPresentException:
        baton_log.info(message_on_exception)


def wait_and_get_element(driver: WebDriver, by: By, selector: str) -> WebElement:
    # NOTE: Might want to change the condition if not every element you grab will be "clickable"
    wait_for_element_to_be_clickable(driver, by, selector, valid_exceptions=())
    return driver.find_element(by, selector)


def wait_and_send_keys_to_element(
    driver: WebDriver, by: By, selector: str, text: str, clear=True
):
    wait_for_element_to_be_clickable(driver, by, selector, valid_exceptions=())
    element = driver.find_element(by, selector)
    if clear:
        element.clear()
    element.send_keys(text)


def wait_and_hit_enter(driver, by, selector: str):
    wait_for_element_to_be_clickable(driver, by, selector, valid_exceptions=())
    driver.find_element(by, selector).send_keys(Keys.ENTER)


def wait_and_select_element_from_dropdown(
    driver: WebDriver,
    by_selector_tuple_dropdown: tuple,
    by_selector_tuple_option: tuple,
    by_selector_tuple_option_fallback=None,
    pre_populate_dropdown=False,
    throw_exception=False,
):
    """Handles select dropdowns.
    NOTE: This does not properly handle dropdowns which do not pre-populate their options in the
    DOM. Use wait_and_populate_dropdown_then_select_element in that case.

    by_selector_tuple_dropdown: click to open the dropdown menu.
    by_selector_tuple_option: option to select in dropdown menu.
    by_selector_tuple_option_fallback: optional fallback option to select in dropdown menu, if
        by_selector_tuple_option is not found.
    pre_populate_dropdown: if the dropdown does not contain all html options in the DOM on page
    load, this types in the name of the item into the search box to populate that option, before
    trying to select it.
    """
    if pre_populate_dropdown:
        raise NotImplementedError("Need to implement pre_populate_dropdown")
    wait_and_click_element(
        driver, by_selector_tuple_dropdown[0], by_selector_tuple_dropdown[1]
    )
    if wait_for_element_to_be_clickable(
        driver, by_selector_tuple_option[0], by_selector_tuple_option[1]
    ):
        wait_and_click_element(
            driver, by_selector_tuple_option[0], by_selector_tuple_option[1]
        )
        return
    elif by_selector_tuple_option_fallback:
        baton_log.info(
            f"Selecting fallback option: {by_selector_tuple_option_fallback}"
        )
        wait_and_click_element(
            driver,
            by_selector_tuple_option_fallback[0],
            by_selector_tuple_option_fallback[1],
        )
    elif throw_exception:
        raise Exception(
            f"Unable to find element for selector: {by_selector_tuple_option}"
        )


def wait_and_click_element(
    driver: WebDriver, by: By, selector: str, wait_time=implicit_wait_time
):
    wait_for_element_to_be_clickable(
        driver, by, selector, valid_exceptions=(), wait_time=wait_time
    )
    driver.find_element(by, selector).click()


def wait_scroll_and_click_element(
    driver: WebDriver,
    by: By,
    selector: str,
    wait_time=implicit_wait_time,
    overscroll_px=50,
):
    wait_for_element_to_be_clickable(
        driver, by, selector, valid_exceptions=(), wait_time=wait_time
    )
    element = driver.find_element(by, selector)
    # Scroll to the element
    driver.execute_script("arguments[0].scrollIntoView(false);", element)
    # Then scroll down a bit further (it's still considered to be not in view)
    driver.execute_script(f"window.scrollBy(0, {overscroll_px});")
    driver.execute_script("arguments[0].click();", element)
    # element.click()
    print("success")


def wait_scroll_and_ctrl_click_element(
    driver: WebDriver, by: By, selector: str, overscroll_px=200
):
    element = driver.find_element(by, selector)
    # Scroll to the element
    driver.execute_script("arguments[0].scrollIntoView(false);", element)
    # Then scroll a bit up to make sure the element is in the clear view (not obscurred by footer)
    driver.execute_script(f"window.scrollBy(0, {overscroll_px});")
    ActionChains(driver).key_down(Keys.CONTROL).click(element).key_up(
        Keys.CONTROL
    ).perform()


def wait_for_element_to_be_clickable(
    driver: WebDriver,
    by: By,
    selector: str,
    element_not_found_message="",
    valid_exceptions=(TimeoutException),
    wait_time=implicit_wait_time,
) -> bool:
    """Return True is the element is found, False if it is not.
    NOTE: If it is not found, this function takes the full implicit_wait_time to execute.
    """
    return _wait_for_element(
        driver,
        by,
        selector,
        element_not_found_message,
        valid_exceptions,
        EC.element_to_be_clickable,
        wait_time=wait_time,
    )


def wait_for_element_to_be_visible(
    driver: WebDriver,
    by: By,
    selector: str,
    element_not_found_message="",
    valid_exceptions=(TimeoutException),
    wait_time=implicit_wait_time,
) -> bool:
    return _wait_for_element(
        driver,
        by,
        selector,
        element_not_found_message,
        valid_exceptions,
        EC.visibility_of_element_located,
        wait_time=wait_time,
    )


def element_exists(
    driver: WebDriver,
    by: By,
    selector: str,
    element_not_found_message: str,
) -> bool:
    """Private module function. Return True is the element is found, False if it is not.
    NOTE: If it is not found, this function takes the full implicit_wait_time to execute.
    """
    try:
        driver.find_element(by, selector)
    except Exception as e:
        baton_log.warning(e.msg)
        if len(element_not_found_message) > 0:
            baton_log.warning(element_not_found_message)
        return False
    return True


def _wait_for_element(
    driver: WebDriver,
    by: By,
    selector: str,
    element_not_found_message: str,
    valid_exceptions: list,
    expected_condition: Callable,
    wait_time=implicit_wait_time,
) -> bool:
    """Private module function. Return True is the element is found, False if it is not.
    NOTE: If it is not found, this function takes the full implicit_wait_time to execute.
    """
    try:
        WebDriverWait(driver, wait_time).until(
            expected_condition((by, selector)),
            f"Timed out waiting for {selector}, for {wait_time} seconds.",
        )
    except valid_exceptions as e:
        baton_log.warning(e.msg)
        if len(element_not_found_message) > 0:
            baton_log.info(element_not_found_message)
        return False
    return True
