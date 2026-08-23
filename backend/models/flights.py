import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from database import Base


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    itinerary_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("itineraries.itinerary_id", ondelete="CASCADE"), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    passengers: Mapped[JSON] = mapped_column(JSON, nullable=False)
    journeys: Mapped[JSON] = mapped_column(JSON, nullable=False)
    booking_options: Mapped[JSON] = mapped_column(JSON, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False, default="serpapi", server_default="serpapi")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
