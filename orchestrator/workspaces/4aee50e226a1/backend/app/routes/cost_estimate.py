from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.database import get_db
from app.models.member import Member
from app.schemas.cost_estimate import CostEstimateResponse
from app.services.cost_estimate_service import estimate_cost

router = APIRouter(prefix="/api/cost-estimate", tags=["cost-estimate"])


@router.get("", response_model=CostEstimateResponse)
def get_cost_estimate(
    drug_name: str = Query(..., description="Drug name to search"),
    db: Session = Depends(get_db),
    member: Member = Depends(get_current_member),
):
    result = estimate_cost(db, member.id, drug_name)
    return CostEstimateResponse(**result)
