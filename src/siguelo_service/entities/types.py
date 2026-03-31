from enum import Enum

ESQUELAS = frozenset({"tacha", "liquidación", "observación"})
ATTACHABLE_ESQUELAS = frozenset(f"Esquela de {e}" for e in ESQUELAS)


class ValidatorURL(Enum):
    API_URL = "https://api-gateway.sunarp.gob.pe:9443/sunarp/siguelo"
    ASIENTO_INSCRIPCION_URL = f"{API_URL}/asientoinscripcion"
    CONSULTA_URL_V2 = f"{API_URL}/siguelo-tracking/tracking/api/consultaTitulo"
    CONSULTA_URL_PUBLICIDAD = f"{API_URL}/siguelo-publ/publicidad/consultaPublicidad"

    LISTAR_PARTIDAS_URL = f"{ASIENTO_INSCRIPCION_URL}/listarPartidas"
    LISTAR_ASIENTOS_URL = f"{ASIENTO_INSCRIPCION_URL}/listarAsientos"
    LISTAR_ASIENTOS_SARP_URL = f"{ASIENTO_INSCRIPCION_URL}/asientosSarp"
    LISTAR_ASIENTOS_MINERIA_URL = f"{ASIENTO_INSCRIPCION_URL}/asientosMineria"

    ANOTACION_URL = "https://anotaci-sir-sunarp-production.apps.paas.sunarp.gob.pe/anotacions/sir/anotacionSir"
    ANOTACION_URL_SARP = "https://anotaci-sarp-sunarp-production.apps.paas.sunarp.gob.pe/anotacions/sarp/anotacionSarp"
