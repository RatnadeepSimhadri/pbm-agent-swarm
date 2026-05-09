from sqlalchemy.orm import Session, joinedload

from app.models.formulary import Formulary
from app.models.plan import Plan


def get_plan(db: Session, plan_id: int) -> Plan | None:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_plan_with_formulary(db: Session, plan_id: int) -> Plan | None:
    return (
        db.query(Plan)
        .options(joinedload(Plan.formulary).joinedload(Formulary.drugs))
        .filter(Plan.id == plan_id)
        .first()
    )
