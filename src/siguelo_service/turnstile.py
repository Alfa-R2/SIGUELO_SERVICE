from loguru import logger
from patchright.sync_api import Page

from .entities.exceptions import TooManyRequestsError


def wait_for_success(page: Page) -> None:
    timer_input_selector = "#txtReloj"
    alert_div_selector = "#swal2-content"
    error_code_td_selector = f"{alert_div_selector} tfoot td"
    loading_element_selectors = (error_code_td_selector, timer_input_selector)
    first_loading_element_selector = ", ".join(loading_element_selectors)
    first_loading_element = page.locator(first_loading_element_selector)
    first_loading_element.wait_for()

    timer_element = page.locator(timer_input_selector)
    if timer_element.is_visible():
        return None  # logger.info("Siguelo is loaded.")

    error_code_td = page.locator(error_code_td_selector)
    error_code_td_inner_text = error_code_td.inner_text()
    error_code = int(error_code_td_inner_text)

    if error_code == 429:
        raise TooManyRequestsError

    if error_code == 998:
        error_message_998 = "Captcha or title number is invalid."
        logger.warning(error_message_998)
        raise ValueError(error_message_998)

    if error_code == 2:
        error_message_2 = "No results found."
        logger.warning(error_message_2)
        raise ValueError(error_message_2)

    if error_code == 500:
        # NOTE: MSG MUST BE "Se produjo un inconveniente, por favor revise su conexión de internet."
        # TODO: This must be retried later.
        raise NotImplementedError("Not managed yet.")

    alert_div = page.locator(alert_div_selector)
    alert_div_inner_text = alert_div.inner_text()
    raise RuntimeError(f"Unknow ({error_code = }): {alert_div_inner_text = }.")
