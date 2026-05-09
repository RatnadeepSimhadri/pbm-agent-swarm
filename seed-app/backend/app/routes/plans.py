from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.database import get_db
from app.schemas.plan import FormularySummary, PlanDetailResponse
from app.services.plan_service import get_plan_with_formulary

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("/{plan_id}", response_model=PlanDetailResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _member=Depends(get_current_member),
):
    plan = get_plan_with_formulary(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    formulary_summary = None
    if plan.formulary:
        formulary_summary = FormularySummary(
            id=plan.formulary.id,
            name=plan.formulary.name,
            effective_date=plan.formulary.effective_date,
            drug_count=len(plan.formulary.drugs),
        )

    return PlanDetailResponse(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        formulary=formulary_summary,
    )
