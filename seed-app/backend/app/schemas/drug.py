from pydantic import BaseModel, ConfigDict


class DrugResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ndc_code: str
    generic_name: str | None
    brand_name: str | None
    strength: str
    form: str
    manufacturer: str
    description: str | None


class DrugListResponse(BaseModel):
    drugs: list[DrugResponse]
    total: int
