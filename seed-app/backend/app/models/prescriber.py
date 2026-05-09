from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Prescriber(Base):
    __tablename__ = "prescribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    npi: Mapped[str] = mapped_column(String(10), unique=True)
    specialty: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))

    @property
    def full_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"
