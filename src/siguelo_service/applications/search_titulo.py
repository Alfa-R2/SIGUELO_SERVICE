from loguru import logger
from patchright.sync_api import Page
from patchright.sync_api import TimeoutError as PachrightTimeoutError

from siguelo_service.entities.exceptions import (
    AnoyingAdException,
    UnknownRegistryOfficeException,
)
from siguelo_service.models.dataclasses import CurrentSearch
from siguelo_service.turnstile import wait_for_success


class SearchTitulo:

    @classmethod
    def _clear_ads(cls, page: Page) -> None:
        """
        Raises:
            - AnoyingAdException: If an unexpected advertisement appears during the search process, which may interfere with the normal flow of the application.
        """
        page.wait_for_timeout(1_000)

        ad_img_selector = "img[alt='Publicidad']"
        ad_img = page.locator(ad_img_selector)
        if ad_img.is_visible():
            close_button = dict(x=1, y=1)
            page.mouse.click(close_button["x"], close_button["y"])

        page.wait_for_timeout(1_000)

        if ad_img.is_visible():
            raise AnoyingAdException(ad_img_selector)

    @classmethod
    def _check_terms_and_conditions(cls, page: Page) -> None:
        accept_terms_and_conditions_button = page.locator("button:text-is('Acepto')")
        if accept_terms_and_conditions_button.is_visible():
            accept_terms_and_conditions_button.click()

    @classmethod
    def _fill_form(cls, page: Page, current_search: CurrentSearch) -> None:
        """
        Raises:
            - UnknownRegistryOfficeException: If the specified registry office is not recognized or cannot be found during the search process.
            - TimeoutError: If the search process encounters a timeout, which may indicate issues with the website's responsiveness or connectivity problems.
        """
        # Tipo tramite
        tracking_types = dict(titulo=0, publicidad=1)
        tracking_type = tracking_types[current_search.tipo]
        tracking_type_radio = page.locator(
            f"input[type='radio'][name='optradio'][value='{tracking_type}']"
        )
        try:
            if not tracking_type_radio.is_checked():
                tracking_type_radio.check()
        except Exception as e:
            raise e

        if current_search.tipo == "publicidad":
            accept_buttton = page.locator('button:text("OK")')
            accept_buttton.click()

        registry_office_select = page.locator("#cboOficina")
        ros_option = registry_office_select.locator("option")
        ros_options = tuple(t.strip().upper() for t in ros_option.all_inner_texts())

        if current_search.oficina_registral not in ros_options:
            raise UnknownRegistryOfficeException(current_search.oficina_registral)
        try:
            registry_office_select.select_option(label=current_search.oficina_registral)
        except TimeoutError as e:
            raise e

        title_year_input = page.locator("#cboAnio")
        title_year_input.select_option(value=current_search.anio_titulo)

        title_number_input = page.locator('input[name="numeroTitulo"]')
        title_number_input.fill(current_search.numero_titulo)

    @classmethod
    def _send_form(cls, page: Page) -> None:
        submit_button = page.locator("button:has-text('BUSCAR'):enabled")
        return submit_button.click()

    @classmethod
    def execute(
        cls, page: Page, current_search: CurrentSearch, timeout: float = 30_000
    ) -> None:
        """
        Raises:
            - TooManyRequestsError: If the server responds with a 429 status code, indicating that the rate limit has been exceeded and the client should wait before making further requests.
            - CaptchaOrTitleNumberInvalidException: If the server responds with error code 998, indicating an invalid captcha or title number.
            - NoResultsFoundException: If the server responds with error code 2, indicating no results found.
            - NotImplementedError: If the server responds with a 500 status code, indicating an internal server error that is not currently managed by the application.
            - RuntimeError: If an unknown error code is received from the server, providing details about the error code and the corresponding message for debugging purposes.
            - FreezeSearchException: If a timeout occurs while waiting for the first loading element, indicating that the search process is frozen and cannot proceed further.
        """

        cls._clear_ads(page)
        cls._check_terms_and_conditions(page)
        cls._fill_form(page, current_search)

        iframe = page.frame_locator('iframe[id^="cf-chl-widget-"]')
        success_circle = iframe.locator("circle.success-circle")
        try:
            success_circle.wait_for()
        except PachrightTimeoutError:
            logger.info(f"Captcha not solved.")
            iframe.locator("html").click()
            success_circle.wait_for()
            logger.info(f"Captcha clicked.")

        cls._send_form(page)

        wait_for_success(page, timeout)
