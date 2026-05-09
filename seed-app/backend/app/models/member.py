from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))

    plan: Mapped["Plan"] = relationship(back_populates="members")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
