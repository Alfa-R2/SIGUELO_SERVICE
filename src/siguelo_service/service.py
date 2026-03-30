from pathlib import Path
from typing import Generator, Literal

from loguru import logger
from patchright.sync_api import BrowserContext, Locator, Page, TimeoutError
from retry import retry

from siguelo_service.applications.get_info.from_row_publicidad import (
    GetInfoFromRowPublicidad,
)
from siguelo_service.applications.get_monto_devolucion import GetMontoDevolucion
from siguelo_service.applications.search_titulo import SearchTitulo
from siguelo_service.applications.take_screenshot import TakeScreenshot

from .applications.get_data.get_anotacion import GetAnotacion, GetAnotacionCommand
from .applications.get_data.get_asientos_tives import (
    GetAsientosTives,
    GetAsientosTivesCommand,
)
from .applications.get_data.get_numeros_partida import GetNumerosPartida
from .applications.get_info.from_row import GetInfoCommand, GetInfoFromRow
from .entities.exceptions import TooManyRequestsError
from .entities.siguelo_entities import (
    DetalleSeguimientoRecord,
    SigueloSearchResult,
    TitleStateResult,
)
from .helpers import wait_until_request_rate_is_renewed
from .models.dataclasses import CurrentSearch, ResourceDownloadResult


class Siguelo:
    ESQUELAS = frozenset({"tacha", "liquidación", "observación"})
    ATTACHABLE_ESQUELAS = frozenset(f"Esquela de {e}" for e in ESQUELAS)

    HOME_URL = "https://sigueloplus.sunarp.gob.pe/siguelo/"

    CONSULTA_URL = "https://tracking-sunarp-production.apps.paas.sunarp.gob.pe/tracking/api/consultaTitulo"

    LISTAR_ESQUELA_URL = "https://esquela-sunarp-production.apps.paas.sunarp.gob.pe/esquela/oficina/api/listarEsquela"

    def __init__(self, browser_context: BrowserContext) -> None:
        self.browser_context = browser_context
        self.page = self.browser_context.new_page()

    def __repr__(self):
        return f"Siguelo(browser_context={self.browser_context})"

    @property
    def _terminos_condiciones_is_accepted(self) -> bool:
        return self._terminos_condiciones == "1"

    @property
    def _terminos_condiciones(self) -> str | None:
        return self.page.evaluate('() => sessionStorage.getItem("termCondi");')

    def _go_to_datos_titulo(self) -> None:
        datos_titulo_link = self.page.query_selector(
            'a[href="/siguelo/titulo"], a[href="/siguelo/publicidad"]'
        )
        assert datos_titulo_link is not None
        datos_titulo_link.click()
        self.page.wait_for_selector(
            'span:text("Datos del título consultado"), h1:text("SEGUIMIENTO DE PUBLICIDAD")'
        )

    @retry(exceptions=TimeoutError, tries=3)
    def _go_to_home(self) -> None:
        self.page.goto(self.HOME_URL)

    def _go_to_detalle_seguimiento(self) -> None:
        page: Page = self.page

        details_a: Locator = page.locator('a[href^="/siguelo/seguimiento"]')
        first_details_a: Locator = details_a.first
        first_details_a.click()

        elements: tuple[str, ...] = (
            'h1:has-text("DETALLE SEGUIMIENTO DE TÍTULO N°")',
            'p:has-text("Su búsqueda no ha obtenido resultados.")',
            'h1:has-text("DETALLE SEGUIMIENTO DE PUBLICIDAD N°")',
        )
        selector: str = ", ".join(elements)
        element: Locator = page.locator(selector)
        first_element: Locator = element.first
        text: str = first_element.inner_text()
        error_msg: str = "Su búsqueda no ha obtenido resultados."
        if error_msg in text:
            raise Exception(error_msg)
        return None

    def _paginate_detalle_seguimiento(self, pages: int) -> None:
        for _ in range(pages - 1):
            siguiente_link = self.page.query_selector('//a[text()=" Siguiente "]')
            assert siguiente_link is not None
            siguiente_link.click()
            self.page.wait_for_timeout(500)

    def _paginate_detalle_seguimiento_iter(self) -> Generator[int, None, None]:
        page_number = 1
        yield page_number

        while True:
            if not (next_link := self.page.query_selector('//a[text()=" Siguiente "]')):
                break

            classes = next_link.get_attribute("class")
            if classes and "disabled" in classes:
                break

            next_link.click()
            self.page.wait_for_timeout(500)

            page_number += 1
            yield page_number

    def _get_detalle_seguimiento(
        self, download_dir: Path, codigo_tive: str, current_search: CurrentSearch
    ) -> tuple[DetalleSeguimientoRecord, ...]:
        page = self.page
        self._go_to_detalle_seguimiento()

        detalle_records = list()
        for _ in self._paginate_detalle_seguimiento_iter():
            rows = page.locator("div#gridDiv table tbody tr").all()
            for row in rows:
                command: GetInfoCommand = GetInfoCommand(
                    browser_context=self.browser_context,
                    data=row.locator("td"),
                    page=self.page,
                    download_dir=download_dir,
                    title_number=current_search.numero_titulo,
                    codigo_tive=codigo_tive,
                )

                result: DetalleSeguimientoRecord = (
                    GetInfoFromRowPublicidad.execute(command)
                    if current_search.tipo == "publicidad"
                    else GetInfoFromRow.execute(command)
                )

                detalle_records.append(result)

        self._go_to_datos_titulo()
        return tuple(detalle_records)

    def __search_titulo(
        self, current_search: CurrentSearch, wait_for_requests: bool, timeout: float
    ) -> None:
        """
        Raises:
            - AnoyingAdException: If an unexpected advertisement appears during the search process, which may interfere with the normal flow of the application.
            - UnknownRegistryOfficeException: If the specified registry office is not recognized or cannot be found during the search process.
        """
        if not self.page.is_closed():
            self.page.close()

        self.page = self.browser_context.new_page()

        try:
            self._go_to_home()
            SearchTitulo.execute(self.page, current_search, timeout)
        except TooManyRequestsError:
            if wait_for_requests:
                logger.warning("Rate limit reach waiting util tomorrow.")
                wait_until_request_rate_is_renewed()
                return self.__search_titulo(current_search, wait_for_requests, timeout)

            raise

    def find(
        self,
        tipo: Literal["titulo", "publicidad"],
        oficina_registral: str,
        anio_titulo: str,
        numero_titulo: str,
        download_dir: Path,
        screenshot_dir: Path | None = None,
        codigo_tive: str | None = None,
        wait_for_requests: bool = True,
        timeout: float = 300_000,
    ) -> SigueloSearchResult | None:
        result: SigueloSearchResult | None = None
        asientos_tives: tuple[ResourceDownloadResult, ...] = tuple()
        anotacion: ResourceDownloadResult | None = None
        detalle_seguimiento: tuple[DetalleSeguimientoRecord, ...] = tuple()

        current_search = CurrentSearch(
            tipo=tipo.lower(),  # type: ignore
            oficina_registral=oficina_registral,
            anio_titulo=anio_titulo,
            numero_titulo=numero_titulo,
            codigo_tive=codigo_tive,
        )

        self.__search_titulo(current_search, wait_for_requests, timeout)

        try:
            monto_devolucion: str = GetMontoDevolucion.execute(self.page)
            numeros_de_partida: list[str] = list(GetNumerosPartida.execute(self.page))

            if self.page.locator(
                "a", has_text="Acceder al asiento de inscripción y TIVE"
            ).is_visible():
                asientos_tives = GetAsientosTives.execute(
                    GetAsientosTivesCommand(
                        browser_context=self.browser_context,
                        page=self.page,
                        current_search=current_search,
                        download_dir=download_dir,
                    )
                )

            if self.page.locator('a:has-text("Ver anotación")').is_visible():
                anotacion = GetAnotacion.execute(
                    GetAnotacionCommand(
                        browser_context=self.browser_context,
                        page=self.page,
                        download_path=download_dir
                        / f"ANOTACION_{current_search.numero_titulo}.pdf",
                    )
                )

            detalle_seguimiento = self._get_detalle_seguimiento(
                download_dir, codigo_tive if codigo_tive else "", current_search
            )

            result = SigueloSearchResult(
                monto_devolucion,
                asientos_tives,
                anotacion,
                detalle_seguimiento,
                numeros_de_partida,
            )

            if screenshot_dir:
                TakeScreenshot.execute(
                    page=self.page,
                    current_search=current_search,
                    screenshot_dir=screenshot_dir,
                )

        except Exception:
            logger.exception(f"Error find - Siguelo.")

        return result

    def get_title_state(
        self,
        tipo: Literal["titulo", "publicidad"],
        oficina_registral: str,
        anio_titulo: str,
        numero_titulo: str,
        screenshot_dir: Path | None = None,
        wait_for_requests: bool = True,
        timeout: float = 300_000,
    ) -> TitleStateResult:

        current_search = CurrentSearch(
            tipo=tipo.lower(),  # type: ignore
            oficina_registral=oficina_registral,
            anio_titulo=anio_titulo,
            numero_titulo=numero_titulo,
            codigo_tive=None,
        )
        self.__search_titulo(current_search, wait_for_requests, timeout)

        try:
            estado_titulo_element = (
                self.page.locator("#estadoActual")
                if tipo == "titulo"
                else self.page.locator(
                    "label:has-text('Calificación') + #lugarPresentacion"
                )
            )
            estado_titulo_element.wait_for(state="visible", timeout=5000)
            estado_registral = estado_titulo_element.input_value().strip()
            screenshot_path: Path | None = (
                TakeScreenshot.execute(
                    page=self.page,
                    current_search=current_search,
                    screenshot_dir=screenshot_dir,
                )
                if screenshot_dir
                else None
            )

            return TitleStateResult(
                estado_registral=estado_registral, screenshot_path=screenshot_path
            )

        except Exception:
            logger.exception(f"Error get_title_state - Siguelo.")
            return TitleStateResult(estado_registral=None, screenshot_path=None)
