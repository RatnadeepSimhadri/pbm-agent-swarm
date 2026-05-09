from pydantic import BaseModel, ConfigDict


class CostEstimateResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drug_id: int
    drug_name: str
    generic_name: str | None
    brand_name: str | None
    strength: str
    form: str
    tier: int
    tier_name: str
    copay_amount: float
    prior_auth_required: bool
    step_therapy_required: bool
    quantity_limit: int | None


class CostEstimateResponse(BaseModel):
    results: list[CostEstimateResult]
    member_plan: str
    total_results: int
