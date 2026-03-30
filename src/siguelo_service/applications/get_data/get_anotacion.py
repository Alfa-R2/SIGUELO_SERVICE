from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from patchright.sync_api import BrowserContext, Page, TimeoutError

from siguelo_service.applications.get_download_error import GetDownloadError
from siguelo_service.models.dataclasses import ResourceDownloadResult
from siguelo_service.scripts import DOWNLOAD_PDF_SCRIPT

from .validators import _anotacion_response_validator


@dataclass
class GetAnotacionCommand:
    browser_context: BrowserContext
    page: Page
    download_path: Path


class GetAnotacion:
    @classmethod
    def execute(cls, command: GetAnotacionCommand) -> ResourceDownloadResult | None:

        download_result: ResourceDownloadResult = ResourceDownloadResult(
            error=False,
            error_message=None,
            path=None,
            resource_type="ANOTACION",
        )

        if not (
            download_button := command.page.query_selector(
                'a:has-text("Ver anotación")'
            )
        ):
            return None

        try:
            with command.browser_context.expect_page() as new_page_info:
                with command.page.expect_response(_anotacion_response_validator):
                    download_button.click()

            new_page: Page = new_page_info.value

            with new_page.expect_download() as download_info:
                new_page.evaluate(DOWNLOAD_PDF_SCRIPT)

            download_info.value.save_as(command.download_path)

            new_page.close()

            download_result.path = command.download_path

        except TimeoutError as e:
            download_result.error = True
            download_result.error_message = GetDownloadError.execute(command.page)

        finally:
            return download_result
