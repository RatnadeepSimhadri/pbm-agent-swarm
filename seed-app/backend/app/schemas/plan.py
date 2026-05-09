from datetime import date

from pydantic import BaseModel, ConfigDict


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str


class PlanDetailResponse(PlanResponse):
    formulary: "FormularySummary | None" = None


class FormularySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    effective_date: date
    drug_count: int
