from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.drug import Drug


def list_drugs(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[Drug], int]:
    total = db.query(Drug).count()
    drugs = db.query(Drug).offset(skip).limit(limit).all()
    return drugs, total


def search_drugs(db: Session, query: str, skip: int = 0, limit: int = 50) -> tuple[list[Drug], int]:
    search = f"%{query}%"
    base_query = db.query(Drug).filter(
        or_(
            Drug.name.ilike(search),
            Drug.generic_name.ilike(search),
            Drug.brand_name.ilike(search),
        )
    )
    total = base_query.count()
    drugs = base_query.offset(skip).limit(limit).all()
    return drugs, total


def get_drug(db: Session, drug_id: int) -> Drug | None:
    return db.query(Drug).filter(Drug.id == drug_id).first()
