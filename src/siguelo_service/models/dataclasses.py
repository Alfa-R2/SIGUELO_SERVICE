from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator

SUNARP_CREATION_YEAR: PositiveInt = 1994
MIN_REGISTRY_OFFICE_LENGTH: PositiveInt = 3


@dataclass
class PagoDetalleSeguimiento:
    lugar: str
    recibo: str
    fecha_hora_recibo: str
    _monto: str

    @property
    def monto(self) -> str:
        if self._monto.startswith("."):
            return f"0{self._monto}"

        return self._monto


@dataclass
class ResourceDownloadResult:
    error: bool = False
    error_message: str | None = None
    path: Path | None = None
    resource_type: str | None = None


class CurrentSearch(BaseModel):
    model_config = ConfigDict(str_to_upper=True)

    tipo: Literal["titulo", "publicidad"]
    oficina_registral: str
    anio_titulo: str
    numero_titulo: str = Field(..., pattern=r"^[0-9]\d*$")
    codigo_tive: str | None = None

    @field_validator("oficina_registral")
    @classmethod
    def validate_oficina_registral(cls, value: str) -> str:
        fixed_value = (
            value.strip()
            .upper()
            .replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
        )
        if len(fixed_value) < MIN_REGISTRY_OFFICE_LENGTH:
            raise ValueError(
                f"Registry office must be at least {MIN_REGISTRY_OFFICE_LENGTH} characters long."
            )
        return fixed_value

    @field_validator("anio_titulo")
    @classmethod
    def validate_anio_titulo(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Title year must be a number.")
        year = int(value)
        if year < SUNARP_CREATION_YEAR:
            raise ValueError(
                f"Title year must be greater than or equal to {SUNARP_CREATION_YEAR}."
            )
        return value
