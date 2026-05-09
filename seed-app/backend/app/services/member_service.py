from sqlalchemy.orm import Session, joinedload

from app.models.member import Member


def get_member_by_id(db: Session, member_id: int) -> Member | None:
    return (
        db.query(Member)
        .options(joinedload(Member.plan))
        .filter(Member.id == member_id)
        .first()
    )


def get_member_by_email(db: Session, email: str) -> Member | None:
    return (
        db.query(Member)
        .options(joinedload(Member.plan))
        .filter(Member.email == email)
        .first()
    )
