from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    ndc_code: Mapped[str] = mapped_column(String(20), unique=True)
    generic_name: Mapped[str | None] = mapped_column(String(200))
    brand_name: Mapped[str | None] = mapped_column(String(200))
    strength: Mapped[str] = mapped_column(String(50))
    form: Mapped[str] = mapped_column(String(50))
    manufacturer: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    formulary_entries: Mapped[list["FormularyDrug"]] = relationship(back_populates="drug")
