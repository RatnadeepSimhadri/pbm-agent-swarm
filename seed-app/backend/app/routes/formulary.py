from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.database import get_db
from app.schemas.formulary import FormularyDrugResponse, FormularyResponse
from app.services.formulary_service import get_formulary_by_plan

router = APIRouter(prefix="/api/formulary", tags=["formulary"])


@router.get("/{plan_id}", response_model=FormularyResponse)
def get_plan_formulary(
    plan_id: int,
    db: Session = Depends(get_db),
    _member=Depends(get_current_member),
):
    formulary = get_formulary_by_plan(db, plan_id)
    if not formulary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulary not found for this plan",
        )
    return FormularyResponse(
        id=formulary.id,
        plan_id=formulary.plan_id,
        name=formulary.name,
        effective_date=formulary.effective_date,
        drugs=[
            FormularyDrugResponse(
                id=fd.id,
                drug_id=fd.drug_id,
                drug_name=fd.drug.name,
                generic_name=fd.drug.generic_name,
                brand_name=fd.drug.brand_name,
                tier=fd.tier,
                copay_amount=fd.copay_amount,
                prior_auth_required=fd.prior_auth_required,
                quantity_limit=fd.quantity_limit,
                step_therapy_required=fd.step_therapy_required,
            )
            for fd in formulary.drugs
        ],
    )
