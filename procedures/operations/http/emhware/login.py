from operations.http.rpa import (
    wait_and_get_element,
    wait_and_send_keys_to_element,
    wait_and_click_element,
    wait_and_hit_enter,
    wait_and_select_element_from_dropdown,
    wait_for_element_to_be_clickable,
    wait_for_element_to_be_visible,
    dismiss_alert,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def login(driver: WebDriver, username: str, password: str):
    driver.get("https://choicesforyouth.emhware.ca/login.php")
    wait_and_send_keys_to_element(
        driver=driver,
        by=By.XPATH,
        selector="//td[contains(@class, 'loginField')]//input[contains(@class, 'string')]",
        text=username,
    )
    wait_and_click_element(
        driver=driver,
        by=By.XPATH,
        selector="//td[contains(@class, 'loginField')]//input[not(@class)]",
    )
    wait_and_send_keys_to_element(
        driver=driver, by=By.ID, selector="idInputPwd", text=password
    )
    wait_and_click_element(driver=driver, by=By.ID, selector="idDivLoginBtn")
