from pydantic import BaseModel, ConfigDict, Field, PositiveInt

SUNARP_CREATION_YEAR: PositiveInt = 1994
MIN_REGISTRY_OFFICE_LENGTH: PositiveInt = 3


class Title(BaseModel):
    model_config = ConfigDict(str_to_upper=True)

    registry_office: str = Field(..., min_length=MIN_REGISTRY_OFFICE_LENGTH)
    year: PositiveInt = Field(..., ge=SUNARP_CREATION_YEAR)
    number: PositiveInt
