from datetime import datetime
from pathlib import Path
from typing import Generator, Literal

from loguru import logger
from patchright.sync_api import BrowserContext, Locator, Page, TimeoutError
from retry import retry

from siguelo_service.applications.get_info.from_row_publicidad import (
    GetInfoFromRowPublicidad,
)

from .applications.get_data.get_anotacion import GetAnotacion, GetAnotacionCommand
from .applications.get_data.get_asientos_tives import (
    GetAsientosTives,
    GetAsientosTivesCommand,
)
from .applications.get_data.get_numeros_partida import GetNumerosPartida
from .applications.get_info.from_row import GetInfoCommand, GetInfoFromRow
from .entities.exceptions import (
    AnoyingAdException,
    TooManyRequestsError,
    UnknownRegistryOfficeException,
)
from .entities.siguelo_entities import DetalleSeguimientoRecord, SigueloSearchResult
from .helpers import wait_until_request_rate_is_renewed
from .models.dataclasses import CurrentSearch, ResourceDownloadResult
from .models.title import Title
from .turnstile import wait_for_success


class Siguelo:
    ESQUELAS = frozenset({"tacha", "liquidación", "observación"})
    ATTACHABLE_ESQUELAS = frozenset(f"Esquela de {e}" for e in ESQUELAS)

    HOME_URL = "https://sigueloplus.sunarp.gob.pe/siguelo/"

    CONSULTA_URL = "https://tracking-sunarp-production.apps.paas.sunarp.gob.pe/tracking/api/consultaTitulo"

    LISTAR_ESQUELA_URL = "https://esquela-sunarp-production.apps.paas.sunarp.gob.pe/esquela/oficina/api/listarEsquela"

    def __init__(
        self, browser_context: BrowserContext, ss_dir: Path | None = None
    ) -> None:
        self.ss_dir = ss_dir
        self.current_search = CurrentSearch("titulo", "", "", "")
        self.browser_context = browser_context
        self.page = self.browser_context.new_page()
        return None

    def __repr__(self):
        return f"Siguelo(browser_context={self.browser_context}, ss_dir={self.ss_dir})"

    @property
    def _terminos_condiciones_is_accepted(self) -> bool:
        return self._terminos_condiciones == "1"

    @property
    def _terminos_condiciones(self) -> str | None:
        return self.page.evaluate('() => sessionStorage.getItem("termCondi");')

    #####################################################
    # DATOS TITULO                                      #
    #####################################################
    def _go_to_datos_titulo(self) -> None:
        datos_titulo_link = self.page.query_selector(
            'a[href="/siguelo/titulo"], a[href="/siguelo/publicidad"]'
        )
        assert datos_titulo_link is not None
        datos_titulo_link.click()
        self.page.wait_for_selector(
            'span:text("Datos del título consultado"), h1:text("SEGUIMIENTO DE PUBLICIDAD")'
        )

    def _clear_ads(self) -> None:
        page = self.page

        page.wait_for_timeout(1_000)

        ad_img_selector = "img[alt='Publicidad']"
        ad_img = page.locator(ad_img_selector)
        if ad_img.is_visible():
            close_button = dict(x=1, y=1)
            page.mouse.click(close_button["x"], close_button["y"])

        page.wait_for_timeout(1_000)

        if ad_img.is_visible():
            raise AnoyingAdException(ad_img_selector)

        return None

    def _check_terms_and_conditions(self) -> None:
        accept_terms_and_conditions_button = self.page.locator(
            "button:text-is('Acepto')"
        )
        if accept_terms_and_conditions_button.is_visible():
            accept_terms_and_conditions_button.click()

    # @retry(exceptions=TimeoutError, tries=3)  # NOTE: Retries here may be expensive because of 2captcha dependency
    @retry(exceptions=TimeoutError, tries=1)
    def _go_to_home(self) -> None:
        page = self.page
        page.goto(self.HOME_URL)
        return None

    def find(
        self,
        tipo: Literal["titulo", "publicidad"],
        oficina_registral: str,
        anio_titulo: str,
        numero_titulo: str,
        download_dir: Path,
        codigo_tive: str | None = None,
    ) -> SigueloSearchResult | None:
        asientos_tives: tuple[ResourceDownloadResult, ...] = tuple()
        anotacion: ResourceDownloadResult | None = None

        title: Title = Title(
            registry_office=oficina_registral,
            year=int(anio_titulo),
            number=int(numero_titulo),
        )

        context = self.page.context
        self.page.close()
        self.page = context.new_page()

        # Just for turnstile
        # self.page.add_init_script(_OPEN_CLOSED_SHADOWS_SCRIPT)

        try:
            csa = (tipo, oficina_registral, anio_titulo, numero_titulo, codigo_tive)
            current_search = CurrentSearch(*csa)
            self.current_search = current_search
            self._go_to_home()
        except Exception as e:
            logger.exception(f"Error find - Siguelo.")

        try:
            self._clear_ads()
        except AnoyingAdException as e:
            raise e
        except Exception as e:
            logger.exception(f"Error find - Siguelo.")

        try:
            self._check_terms_and_conditions()
        except Exception as e:
            logger.exception(f"Error find - Siguelo.")

        try:
            self._fill_form(tipo, title)
        except UnknownRegistryOfficeException as e:
            raise

        iframe = self.page.frame_locator('iframe[id^="cf-chl-widget-"]')
        success_circle = iframe.locator("circle.success-circle")
        try:
            success_circle.wait_for()
        except TimeoutError:
            logger.info(f"Captcha not solved.")
            iframe.locator("html").click()
            success_circle.wait_for()
            logger.info(f"Captcha clicked.")

        try:
            self._send_form()
            page = self.page
            try:
                wait_for_success(page)
            except TooManyRequestsError as e:
                logger.warning("Rate limit reach waiting util tomorrow.")
                wait_until_request_rate_is_renewed()

                return self.find(
                    tipo,
                    oficina_registral,
                    anio_titulo,
                    numero_titulo,
                    download_dir,
                    codigo_tive,
                )

            monto_devolver_element = page.query_selector(".mostrarDevoMoney")
            assert monto_devolver_element

            monto_devolver_text = monto_devolver_element.text_content() or "S/0.00"
            monto_devolver_text = monto_devolver_text.replace("\xa0", "")
            monto_devolver_text = monto_devolver_text.strip().replace("S/", "")

            monto_devolucion = "0.00"
            if monto_devolver_text != "0.00":
                monto_devolucion = monto_devolver_text

            numeros_de_partida = list(GetNumerosPartida.execute(page))

            if page.locator(
                "a", has_text="Acceder al asiento de inscripción y TIVE"
            ).is_visible():
                asientos_tives = GetAsientosTives.execute(
                    GetAsientosTivesCommand(
                        browser_context=self.browser_context,
                        page=page,
                        current_search=self.current_search,
                        download_dir=download_dir,
                    )
                )

            if page.locator('a:has-text("Ver anotación")').is_visible():
                anotacion = GetAnotacion.execute(
                    GetAnotacionCommand(
                        browser_context=self.browser_context,
                        page=page,
                        download_dir=download_dir,
                    )
                )

            detalle_seguimiento: tuple[DetalleSeguimientoRecord, ...] = (
                self._get_detalle_seguimiento(
                    download_dir, codigo_tive if codigo_tive else ""
                )
            )

            result = SigueloSearchResult(
                monto_devolucion,
                asientos_tives,
                anotacion,
                detalle_seguimiento,
                numeros_de_partida,
            )

            if self.ss_dir:
                now = datetime.now()
                str_now = now.strftime("%d_%m_%Y__%H-%M-%S")
                cs_title = self.current_search.numero_titulo
                cs_title_year = self.current_search.anio_titulo
                ss_path = self.ss_dir / f"{cs_title}_{cs_title_year}__{str_now}.jpeg"
                try:
                    page.wait_for_timeout(250)
                    page.screenshot(type="jpeg", path=ss_path)
                except Exception as e:
                    logger.exception(f"ERROR!!!")

            return result

        except Exception as e:
            return logger.exception(f"Error find - Siguelo.")

    def _fill_form(self, tipo: Literal["titulo", "publicidad"], title: Title) -> None:
        page: Page = self.page

        # Tipo tramite
        tracking_types = dict(titulo=0, publicidad=1)
        tracking_type = tracking_types[tipo]
        tracking_type_radio = page.locator(
            f"input[type='radio'][name='optradio'][value='{tracking_type}']"
        )
        try:
            if not tracking_type_radio.is_checked():
                tracking_type_radio.check()
        except Exception as e:
            raise e

        if tipo == "publicidad":
            accept_buttton = page.locator('button:text("OK")')
            accept_buttton.click()

        registry_office_select = page.locator("#cboOficina")
        ros_option = registry_office_select.locator("option")
        ros_options = tuple(t.strip().upper() for t in ros_option.all_inner_texts())

        fixed_registry_office = (
            title.registry_office.strip()
            .upper()
            .replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
        )

        if fixed_registry_office not in ros_options:
            raise UnknownRegistryOfficeException(title.registry_office)
        try:
            registry_office_select.select_option(label=fixed_registry_office)
        except TimeoutError as e:
            raise

        title_year_input = page.locator("#cboAnio")
        title_year_input.select_option(value=str(title.year))

        title_number_input = page.locator('input[name="numeroTitulo"]')
        title_number_input.fill(str(title.number))

        return None

    def _send_form(self) -> None:
        page = self.page
        submit_button = page.locator("button:has-text('BUSCAR'):enabled")
        return submit_button.click()

    #####################################################
    # DETALLE SEGUIMIENTO                               #
    #####################################################
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
        self, download_dir: Path, codigo_tive: str
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
                    codigo_tive=codigo_tive,
                )

                result: DetalleSeguimientoRecord = (
                    GetInfoFromRowPublicidad.execute(command)
                    if self.current_search.tipo == "publicidad"
                    else GetInfoFromRow.execute(command)
                )

                detalle_records.append(result)

        self._go_to_datos_titulo()
        return tuple(detalle_records)
