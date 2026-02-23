from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class PagoDetalleSeguimiento:
    lugar: str
    recibo: str
    fecha_hora_recibo: str
    monto: str


@dataclass
class ResourceDownloadResult:
    error: bool = False
    error_message: str | None = None
    path: Path | None = None
    resource_type: str | None = None


@dataclass
class CurrentSearch:
    tipo: Literal["titulo", "publicidad"]
    oficina_registral: str
    anio_titulo: str
    numero_titulo: str
    codigo_tive: str | None = None
