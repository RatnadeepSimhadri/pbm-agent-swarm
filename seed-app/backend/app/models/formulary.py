from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Formulary(Base):
    __tablename__ = "formularies"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    effective_date: Mapped[date] = mapped_column(Date)

    plan: Mapped["Plan"] = relationship(back_populates="formulary")
    drugs: Mapped[list["FormularyDrug"]] = relationship(back_populates="formulary")


class FormularyDrug(Base):
    __tablename__ = "formulary_drugs"

    id: Mapped[int] = mapped_column(primary_key=True)
    formulary_id: Mapped[int] = mapped_column(ForeignKey("formularies.id"))
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"))
    tier: Mapped[int] = mapped_column(Integer)
    copay_amount: Mapped[float] = mapped_column(Float)
    prior_auth_required: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    step_therapy_required: Mapped[bool] = mapped_column(Boolean, default=False)

    formulary: Mapped["Formulary"] = relationship(back_populates="drugs")
    drug: Mapped["Drug"] = relationship(back_populates="formulary_entries")
