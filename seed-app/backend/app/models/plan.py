from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)

    members: Mapped[list["Member"]] = relationship(back_populates="plan")
    formulary: Mapped["Formulary | None"] = relationship(back_populates="plan", uselist=False)
