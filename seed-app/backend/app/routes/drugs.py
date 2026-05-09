from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.database import get_db
from app.schemas.drug import DrugListResponse, DrugResponse
from app.services.drug_service import get_drug, list_drugs, search_drugs

router = APIRouter(prefix="/api/drugs", tags=["drugs"])


@router.get("", response_model=DrugListResponse)
def get_drugs(
    q: str | None = Query(None, description="Search query for drug name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _member=Depends(get_current_member),
):
    if q:
        drugs, total = search_drugs(db, q, skip, limit)
    else:
        drugs, total = list_drugs(db, skip, limit)
    return DrugListResponse(
        drugs=[DrugResponse.model_validate(d) for d in drugs],
        total=total,
    )


@router.get("/{drug_id}", response_model=DrugResponse)
def get_drug_detail(
    drug_id: int,
    db: Session = Depends(get_db),
    _member=Depends(get_current_member),
):
    drug = get_drug(db, drug_id)
    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")
    return DrugResponse.model_validate(drug)
