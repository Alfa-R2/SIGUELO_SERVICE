from pathlib import Path

from loguru import logger
from patchright.sync_api import Locator, TimeoutError

from siguelo_service.applications.get_download_error import GetDownloadError
from siguelo_service.applications.helpers import download_from_new_tab
from siguelo_service.entities.types import ATTACHABLE_ESQUELAS
from siguelo_service.models.dataclasses import (
    PagoDetalleSeguimiento,
    ResourceDownloadResult,
)

from .command import GetInfoCommand


class GetExtraInfo:
    @classmethod
    def __get_pago(cls, command: GetInfoCommand) -> PagoDetalleSeguimiento | None:
        pago: PagoDetalleSeguimiento | None = None
        popup_link: Locator = command.data.all()[-1].locator("a")
        assert popup_link != None

        popup_link.click()

        pago_content: Locator = command.page.locator('//*[@id="swal2-content"]')
        pago_content.wait_for()

        if not pago_content.locator("table tbody").is_visible():
            error_msg = pago_content.locator("p").text_content()
            logger.error(f"Error getting pago data: {error_msg}")
        else:
            pago_tbody = pago_content.locator("table tbody")
            assert pago_tbody != None

            pago_cells = pago_tbody.locator("tr").first.locator("td")
            args = pago_cells.all_inner_texts()
            pago = PagoDetalleSeguimiento(*args)

        command.page.keyboard.press("Escape")
        pago_content.wait_for(state="detached", timeout=5000)
        return pago

    @classmethod
    def __get_esquela_resource(
        cls, command: GetInfoCommand, file_path: Path
    ) -> ResourceDownloadResult:
        download_link = command.data.all()[-1].locator("a")
        assert download_link != None

        with download_from_new_tab(
            page=command.page,
            download_path=file_path,
            type="ESQUELA",
        ) as download_result:

            download_link.click()

        return download_result

    @classmethod
    def __get_certificado_resource(
        cls, command: GetInfoCommand, file_path: Path
    ) -> ResourceDownloadResult:

        download_result: ResourceDownloadResult = ResourceDownloadResult(
            error=False, error_message=None, path=None, resource_type="ANOTACION"
        )

        try:
            if not file_path.exists():
                download_link: Locator = command.data.all()[-1].locator("a")
                assert download_link != None

                download_link.click()

                selectors_joined = ", ".join(
                    [
                        'p:has-text("Certificado, que tiene un tiempo 90 dias calendarios para su visualizacion y descarga.")',
                        'h2:text("Ingrese su Código de Verificación")',
                        'p:has-text("Estimado Ciudadano , se ha generado nuevo certificado por aclaración, el cual podrá descargar en la")',
                    ]
                )

                content: str = command.page.locator(selectors_joined).inner_text()

                if "90 dias calendarios para su visualizacion y descarga." in content:
                    download_result.error = True
                    download_result.error_message = "Certificado, que tiene un tiempo 90 dias calendarios para su visualizacion y descarga."
                    return download_result

                if "se ha generado nuevo certificado por aclaración" in content:
                    download_result.error_message = content
                    download_result.path = None
                    return download_result

                modal: Locator = command.page.locator(
                    '//h2[text()="Ingrese su Código de Verificación"]/../..'
                )
                code_input: Locator = modal.locator('input[type="text"]')
                aceptar_button: Locator = modal.locator('button:text("Aceptar")')
                assert (tive := command.codigo_tive)
                code_input.fill(tive)

                with command.page.expect_download() as download_info:
                    aceptar_button.click()

                download = download_info.value
                download.save_as(file_path)

            download_result.path = file_path

        except TimeoutError:
            download_result.error = True
            download_result.error_message = GetDownloadError.execute(page=command.page)

        finally:
            return download_result

    @classmethod
    def execute(
        cls,
        command: GetInfoCommand,
        state: str,
        datetime: str,
    ) -> PagoDetalleSeguimiento | ResourceDownloadResult | None:
        DOC_TIMESTAMP: str = (
            datetime.replace("/", "").replace(":", "").strip().replace(" ", "_")
        )
        attachments = tuple(command.data.locator("a span").all_inner_texts())
        cleaned_attachments = tuple(a.split("\xa0", 1)[-1].strip() for a in attachments)
        attachments_set = frozenset(cleaned_attachments)

        is_popup: bool = "Ver Pago" in cleaned_attachments
        is_new_tab: frozenset[str] = attachments_set & ATTACHABLE_ESQUELAS
        is_certificado: bool = any("Ver Certificado" in a for a in cleaned_attachments)

        if is_popup:
            return cls.__get_pago(command)

        if is_new_tab:
            return cls.__get_esquela_resource(
                command,
                command.download_dir
                / f"ESQUELA_{state}_{DOC_TIMESTAMP}_{command.title_number}.pdf",
            )

        if is_certificado:
            return cls.__get_certificado_resource(
                command,
                command.download_dir
                / f"CERTIFICADO_{state}_{DOC_TIMESTAMP}_{command.title_number}.pdf",
            )

        return None
