from pathlib import Path
from typing import NamedTuple

from siguelo_service.models.dataclasses import (
    PagoDetalleSeguimiento,
    ResourceDownloadResult,
)


class DetalleSeguimientoRecord:
    def __init__(
        self,
        secuencia: str,
        etapa: str,
        area: str,
        estado_registral: str,
        fecha_hora: str,
        responsable: str,
        extra_info: PagoDetalleSeguimiento | ResourceDownloadResult | None = None,
    ) -> None:
        self.secuencia = secuencia
        self.etapa = etapa
        self.area = area
        self.estado_registral = estado_registral
        self.fecha_hora = fecha_hora
        self.responsable = responsable
        self.extra_info = extra_info

    @property
    def fecha(self) -> str:
        return self.fecha_hora.split(" ")[0]

    def __repr__(self) -> str:
        return (
            f'DetalleSeguimientoRecord(secuencia="{self.secuencia}", etapa="{self.etapa}", '
            f'area="{self.area}", estado_registral="{self.estado_registral}", '
            f'fecha_hora="{self.fecha_hora}", responsable="{self.responsable}", '
            f"extra_info={self.extra_info})"
        )


class SigueloSearchResult:
    def __init__(
        self,
        monto_devolucion: str,
        asientos_tives: tuple[ResourceDownloadResult, ...],
        anotacion: ResourceDownloadResult | None,
        detalle_seguimiento: tuple[DetalleSeguimientoRecord, ...],
        partidas: list[str],
    ) -> None:
        self.monto_devolucion = monto_devolucion
        self.asientos_tives = asientos_tives
        self.anotacion = anotacion
        self.detalle_seguimiento = detalle_seguimiento
        self.partidas = partidas

    @property
    def asientos(self) -> tuple[ResourceDownloadResult, ...]:
        return tuple(
            at
            for at in self.asientos_tives
            if at.path and at.path.stem.startswith("ASIENTO")
        )

    @property
    def tives(self) -> tuple[ResourceDownloadResult, ...]:
        return tuple(
            at
            for at in self.asientos_tives
            if at.path and at.path.stem.startswith("TIVE")
        )

    @property
    def download_errors(self) -> tuple[ResourceDownloadResult, ...]:
        return tuple(
            filter(
                lambda x: x and x.error,  # type: ignore
                [self.anotacion, *self.asientos_tives],
            )
        )

    def __repr__(self) -> str:
        return (
            f"SigueloSearchResult( "
            f'monto_devolucion="{self.monto_devolucion}", asientos_tives={self.asientos_tives}, '
            f"anotacion={self.anotacion}, detalle_seguimiento={self.detalle_seguimiento}, "
            f"partidas={self.partidas})"
        )


class TitleStateResult(NamedTuple):
    estado_registral: str | None
    screenshot_path: Path | None
