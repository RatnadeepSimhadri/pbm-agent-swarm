from datetime import date

from pydantic import BaseModel, ConfigDict


class MemberBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    date_of_birth: date


class MemberResponse(MemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    full_name: str


class MemberWithPlanResponse(MemberResponse):
    plan: "PlanSummary"


class PlanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
