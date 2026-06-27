from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from backend.models.database import Base


class Device(Base):
    """Device model — provisional implementation by Covenant per the Phase 2
    contract (DATABASE_SCHEMA.md §8), since ENJ had not yet shipped the real
    model at time of writing. Please review/replace on merge if your
    implementation differs."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"<Device id={self.id} user_id={self.user_id} device_name={self.device_name!r} is_active={self.is_active}>"