ERROR_SELECTORS: tuple[str, ...] = (
    'p:text(" Su búsqueda no ha obtenido resultados. ")',
    'p:has-text("Su búsqueda no ha obtenido resultados")',
    'p:has-text("Existe un título o publicidad que ha generado una nueva TIVe posterior a la consultada")',
    'p:has-text("No se encontró coincidencia")',
    'td:has-text("Ha ocurrido un error al intentar obtener")',
    'td:has-text("No sé encontró información solicitada")',
    'p:text(" El registro se encontro en el CM , pero la imagen no existe o esta mal quemada ")',
    'p:text("Recuerde que la descarga de su Orden de Giro solo es por unica vez, mediante la plataforma Siguelo")',
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


class AddedRetry(MainException): ...
