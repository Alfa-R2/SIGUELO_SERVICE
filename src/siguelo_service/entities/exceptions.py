ERROR_SELECTORS: tuple[str, ...] = (
    'p:text(" Su búsqueda no ha obtenido resultados. ")',
    'p:has-text("Su búsqueda no ha obtenido resultados")',
    'p:has-text("Existe un título o publicidad que ha generado una nueva TIVe posterior a la consultada")',
    'p:has-text("No se encontró coincidencia")',
    'td:has-text("Ha ocurrido un error al intentar obtener")',
    'td:has-text("No sé encontró información solicitada")',
    'p:text(" El registro se encontro en el CM , pero la imagen no existe o esta mal quemada ")',
    'div#swal2-content td:has-text("Visualización restringida, en el marco de lo establecido en el Artículo 46 del Reglamento de Inscripciones de los Registros de Testamentos y de Sucesiones Intestadas")',
)


class SigueloException(Exception): ...


class UnknownDownloadException(SigueloException): ...


class UnknownRegistryOfficeException(SigueloException): ...


class AnoyingAdException(SigueloException): ...


class GatewayTimeoutError(Exception):
    """Siguelo Server is down, wait a little longer before try again."""


class TooManyRequestsError(Exception):
    """Too many requests today - wait until tomorrow 0:00 AM."""


class MainException(Exception): ...


class FreezeSearchException(MainException):
    """Raised when the search process is frozen, which may occur due to various reasons such as server issues, network problems, or unexpected errors during the search operation. This exception indicates that the search process cannot proceed further and may require intervention or troubleshooting to resolve the underlying issue."""


class CaptchaOrTitleNumberInvalidException(MainException):
    """Raised when the captcha or title number provided during the search process is invalid, indicating that the input does not meet the required criteria or format. This exception suggests that the user should verify and correct the captcha or title number before attempting the search again."""


class NoResultsFoundException(MainException):
    """Raised when no results are found for the given search parameters, indicating that the search query did not match any records in the database. This exception suggests that the user should review and adjust the search parameters to increase the chances of finding relevant results."""
