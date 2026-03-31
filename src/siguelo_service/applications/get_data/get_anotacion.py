from dataclasses import dataclass
from pathlib import Path

from patchright.sync_api import Page

from siguelo_service.applications.helpers import download_from_new_tab
from siguelo_service.models.dataclasses import ResourceDownloadResult

from .validators import _anotacion_response_validator


@dataclass
class GetAnotacionCommand:
    page: Page
    download_path: Path


class GetAnotacion:
    @classmethod
    def execute(cls, command: GetAnotacionCommand) -> ResourceDownloadResult | None:

        if not (
            download_button := command.page.query_selector(
                'a:has-text("Ver anotación")'
            )
        ):
            return None

        with download_from_new_tab(
            page=command.page,
            download_path=command.download_path,
            type="ANOTACION",
        ) as download_result:

            with command.page.expect_response(_anotacion_response_validator):
                download_button.click()

        return download_result
