from siguelo_service.entities.siguelo_entities import DetalleSeguimientoRecord

from .command import GetInfoCommand
from .get_extra_info import GetExtraInfo

PHRASES: tuple[str, ...] = (
    "Esquela de tacha",
    "Esquela de liquidación",
    "Esquela de observación",
    "Ver Esquela",  # CONCLUSODEOFICIO
)


class GetInfoFromRowPublicidad:

    @staticmethod
    def execute(command: GetInfoCommand) -> DetalleSeguimientoRecord:
        _secuencia, etapa, _evento, status, _datetime, ver = (
            command.data.all_inner_texts()
        )
        is_liquidado: bool = (
            any(phrase in ver for phrase in PHRASES) and "Esquela de liquidación" in ver
        )

        estado_registral: str = (
            "LIQUIDADO" if is_liquidado else status.split()[-1].strip()
        )
        secuence: str = _secuencia.zfill(3)
        evento: str = _evento.replace("AREA : ", "").strip()
        datetime: str = _datetime.replace("FECHA OPERACIÓN :", "").strip().split()[0]

        return DetalleSeguimientoRecord(
            secuence,
            etapa,
            evento,
            estado_registral,
            datetime,
            "",
            GetExtraInfo.execute(command, estado_registral, datetime),
        )
