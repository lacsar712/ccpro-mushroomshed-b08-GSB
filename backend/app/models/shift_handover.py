from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShiftHandover(Base):
    __tablename__ = "shift_handovers"
    __table_args__ = (
        UniqueConstraint("shed_id", "work_date", name="uq_handover_shed_workdate"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shed_id: Mapped[int] = mapped_column(ForeignKey("sheds.id"), nullable=False, index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    phrase: Mapped[str] = mapped_column(String(64), nullable=False)
    handed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    taken_by: Mapped[str] = mapped_column(String(64), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    shed: Mapped["Shed"] = relationship("Shed", back_populates="shift_handovers")
