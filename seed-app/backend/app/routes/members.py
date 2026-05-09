from fastapi import APIRouter, Depends

from app.auth import get_current_member
from app.models.member import Member
from app.schemas.member import MemberWithPlanResponse, PlanSummary

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("/me", response_model=MemberWithPlanResponse)
def get_current_member_profile(member: Member = Depends(get_current_member)):
    return MemberWithPlanResponse(
        id=member.id,
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        date_of_birth=member.date_of_birth,
        plan_id=member.plan_id,
        full_name=member.full_name,
        plan=PlanSummary.model_validate(member.plan),
    )
