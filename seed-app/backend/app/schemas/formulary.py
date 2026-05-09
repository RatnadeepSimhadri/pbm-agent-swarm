from datetime import date

from pydantic import BaseModel, ConfigDict


class FormularyDrugResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drug_id: int
    drug_name: str
    generic_name: str | None
    brand_name: str | None
    tier: int
    copay_amount: float
    prior_auth_required: bool
    quantity_limit: int | None
    step_therapy_required: bool


class FormularyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    name: str
    effective_date: date
    drugs: list[FormularyDrugResponse]


class TierSummary(BaseModel):
    tier: int
    tier_name: str
    copay_amount: float
    drug_count: int
