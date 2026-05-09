from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.drug import Drug
from app.models.formulary import Formulary, FormularyDrug
from app.models.member import Member

TIER_NAMES = {
    1: "Preferred Generic",
    2: "Non-Preferred Generic",
    3: "Preferred Brand",
    4: "Specialty",
}


def estimate_cost(db: Session, member_id: int, drug_name: str) -> dict:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {"results": [], "member_plan": "", "total_results": 0}

    plan = member.plan
    formulary = db.query(Formulary).filter(Formulary.plan_id == plan.id).first()
    if not formulary:
        return {"results": [], "member_plan": plan.name, "total_results": 0}

    search = f"%{drug_name}%"
    entries = (
        db.query(FormularyDrug)
        .join(Drug, FormularyDrug.drug_id == Drug.id)
        .filter(
            FormularyDrug.formulary_id == formulary.id,
            or_(
                Drug.name.ilike(search),
                Drug.generic_name.ilike(search),
                Drug.brand_name.ilike(search),
            ),
        )
        .options(joinedload(FormularyDrug.drug))
        .all()
    )

    results = []
    for entry in entries:
        results.append({
            "drug_id": entry.drug.id,
            "drug_name": entry.drug.name,
            "generic_name": entry.drug.generic_name,
            "brand_name": entry.drug.brand_name,
            "strength": entry.drug.strength,
            "form": entry.drug.form,
            "tier": entry.tier,
            "tier_name": TIER_NAMES.get(entry.tier, f"Tier {entry.tier}"),
            "copay_amount": entry.copay_amount,
            "prior_auth_required": entry.prior_auth_required,
            "step_therapy_required": entry.step_therapy_required,
            "quantity_limit": entry.quantity_limit,
        })

    return {
        "results": results,
        "member_plan": plan.name,
        "total_results": len(results),
    }
