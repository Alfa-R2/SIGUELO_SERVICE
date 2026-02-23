from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from patchright.sync_api import (
    BrowserContext,
    ElementHandle,
    Locator,
    Page,
    TimeoutError,
)

from siguelo_service.applications.get_download_error import GetDownloadError
from siguelo_service.entities.types import RESTRISTED_DOWNLOAD_TD_MSG
from siguelo_service.models.dataclasses import CurrentSearch, ResourceDownloadResult
from siguelo_service.scripts import DOWNLOAD_PDF_SCRIPT

from .validators import (
    _listar_asientos_response_validator,
    asiento_tive_popup_response_validator,
)


@dataclass
class GetAsientosTivesCommand:
    browser_context: BrowserContext
    page: Page
    download_dir: Path
    current_search: CurrentSearch


class GetAsientosTives:

    @classmethod
    def _download_asiento_from_row(
        cls, command: GetAsientosTivesCommand, row: ElementHandle
    ) -> ResourceDownloadResult | None:
        tds: list[ElementHandle] = row.query_selector_all("td")
        number: ElementHandle = tds[0]
        download_button_cell: ElementHandle = tds[2]

        number_text: str | None = number.text_content()

        download_path: Path = (
            command.download_dir
            / f'ASIENTO_{number_text.strip() if number_text else "0"}.pdf'
        )
        download_result: ResourceDownloadResult = ResourceDownloadResult(
            error=False,
            error_message=None,
            path=download_path,
            resource_type="ASIENTO",
        )

        if not (download_button := download_button_cell.query_selector("button")):
            return None

        default_timeout: int = 30_000
        expect_page_timeout: int = 2 * default_timeout
        try:
            try:
                # NOTE: Here some download may NOT EXISTS
                with command.browser_context.expect_page(
                    timeout=expect_page_timeout
                ) as event_info:

                    with command.page.expect_response(
                        _listar_asientos_response_validator
                    ):
                        download_button.click()
                        not_found_46: str = (
                            "Visualización restringida, en el marco de lo establecido en el Artículo 46 del Reglamento de Inscripciones de los Registros de Testamentos y de Sucesiones Intestadas"
                        )
                        # TODO: wait for "div#swal2-content td" with not_found_46 text or wait for page to exists.

            except TimeoutError as e:
                restricted = command.page.locator(
                    "div#swal2-content td", has_text=RESTRISTED_DOWNLOAD_TD_MSG
                )
                if restricted.is_visible():
                    raise TimeoutError("Restricted download") from e
                raise

            new_page = event_info.value

            with new_page.expect_download() as download_info:
                new_page.evaluate(DOWNLOAD_PDF_SCRIPT)

            download_info.value.save_as(download_path)

            new_page.close()

        except TimeoutError as e:
            logger.exception("Download Asiento From Row Exception.")
            download_result.error = True
            download_result.error_message = GetDownloadError.execute(page=command.page)

        return download_result

    @classmethod
    def _download_tive_from_row(
        cls,
        command: GetAsientosTivesCommand,
        row: ElementHandle,
    ) -> ResourceDownloadResult | None:
        tds: list[ElementHandle] = row.query_selector_all("td")
        number: ElementHandle = tds[0]
        numero_placa_cell: ElementHandle = tds[3]
        download_button_cell: ElementHandle = tds[4]

        numero_placa_text: str | None = numero_placa_cell.text_content()
        assert numero_placa_text is not None

        number_text: str | None = number.text_content()
        assert number_text is not None

        download_path = (
            command.download_dir / f"TIVE_{numero_placa_text}_{number_text}.pdf"
        )
        download_result = ResourceDownloadResult(
            error=False, error_message=None, path=download_path, resource_type="TIVE"
        )

        if not (download_button := download_button_cell.query_selector("button")):
            return None

        try:
            download_button.click()

            modal = command.page.wait_for_selector(
                '//p[text()="Ingrese el número de "]/parent::div/parent::div'
            )
            assert modal

            placa_input = command.page.wait_for_selector(
                "//html/body/div[3]/div/div[2]/input[1]"
            )
            assert placa_input
            placa_input.type(numero_placa_text.strip())

            siguiente_button = command.page.query_selector(
                "//html/body/div[3]/div/div[3]/button[2]"
            )
            assert siguiente_button
            siguiente_button.click()

            # Segunda parte
            codigo_tive_input = command.page.wait_for_selector(
                "//html/body/div[3]/div/div[2]/input[1]"
            )
            assert codigo_tive_input
            codigo_tive_input.type(command.current_search.codigo_tive or "")

            siguiente_button = command.page.query_selector(
                "//html/body/div[3]/div/div[3]/button[2]"
            )
            assert siguiente_button

            try:
                with command.page.expect_download() as download_info:
                    siguiente_button.click()

            except TimeoutError as e:
                raise
            download_info.value.save_as(download_path)

        except TimeoutError as e:
            logger.exception("Download Tive From Row Exception.")
            download_result.error = True
            download_result.error_message = GetDownloadError.execute(page=command.page)

        return download_result

    @classmethod
    def execute(
        cls, command: GetAsientosTivesCommand
    ) -> tuple[ResourceDownloadResult, ...]:
        """Descarga asientos y/o TIVEs."""

        asiento_tive_button: Locator = command.page.locator(
            "span", has_text="Acceder al asiento de inscripción y TIVE"
        )
        with command.page.expect_response(asiento_tive_popup_response_validator):
            asiento_tive_button.click()
        command.page.wait_for_timeout(1000)

        modal_element: ElementHandle | None = command.page.wait_for_selector(
            "div[id^='cdk-overlay']"
        )
        assert modal_element is not None

        tbody_element: ElementHandle | None = modal_element.query_selector("tbody")
        assert tbody_element is not None

        downloads: list[ResourceDownloadResult] = list()
        rows: list[ElementHandle] = tbody_element.query_selector_all("tr")
        for row in rows:
            tds: list[ElementHandle] = row.query_selector_all("td")

            if len(tds) >= 3:
                if file := cls._download_asiento_from_row(command, row):
                    downloads.append(file)

            if (
                len(tds) >= 5
                and command.current_search
                and command.current_search.codigo_tive
            ):
                if file := cls._download_tive_from_row(command, row):
                    downloads.append(file)

        close_button: ElementHandle | None = command.page.query_selector(
            '//mat-icon[text()="close"]'
        )
        assert close_button

        close_button.click()

        return tuple(downloads)
