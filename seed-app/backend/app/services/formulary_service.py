from sqlalchemy.orm import Session, joinedload

from app.models.formulary import Formulary, FormularyDrug


def get_formulary_by_plan(db: Session, plan_id: int) -> Formulary | None:
    return (
        db.query(Formulary)
        .options(joinedload(Formulary.drugs).joinedload(FormularyDrug.drug))
        .filter(Formulary.plan_id == plan_id)
        .first()
    )
