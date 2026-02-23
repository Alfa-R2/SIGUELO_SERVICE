from patchright.sync_api import Response

from siguelo_service.entities.types import ValidatorURL


def asiento_tive_popup_response_validator(response: Response) -> bool:
    request = response.request
    return (
        request.url == ValidatorURL.LISTAR_PARTIDAS_URL.value
        and request.method == "POST"
    )


def _listar_asientos_response_validator(response: Response) -> bool:
    request = response.request
    ASENTO_URLS = (
        ValidatorURL.LISTAR_ASIENTOS_URL.value,
        ValidatorURL.LISTAR_ASIENTOS_SARP_URL.value,
        ValidatorURL.LISTAR_ASIENTOS_MINERIA_URL.value,
    )
    return request.url in ASENTO_URLS and request.method == "POST"


def _anotacion_response_validator(response: Response) -> bool:
    request = response.request
    ANOTACION_URLS = (
        ValidatorURL.ANOTACION_URL.value,
        ValidatorURL.ANOTACION_URL_SARP.value,
    )
    return request.url in ANOTACION_URLS and request.method == "POST"
