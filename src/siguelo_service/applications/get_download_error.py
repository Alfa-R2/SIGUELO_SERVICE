from patchright.sync_api import Locator, Page

from siguelo_service.entities.exceptions import (
    ERROR_SELECTORS,
    UnknownDownloadException,
)


class GetDownloadError:

    @classmethod
    def execute(cls, page: Page) -> str:
        """
        raises:
            - UnknownDownloadException: If no known error message is found in the page.
        """

        elem: Locator = page.locator(", ".join(ERROR_SELECTORS))
        if elem.count():
            msg: str = elem.text_content() or ""
            page.mouse.click(1, 1)  # Cierra el popup
            return msg

        body: Locator = page.locator("html > body")
        body_content = body.text_content()
        if body_content and "No sé encontró el Código ingresado" in body_content:
            return "No sé encontró el Código ingresado"

        raise UnknownDownloadException(f"No known description: {body_content}")
