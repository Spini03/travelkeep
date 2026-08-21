from sqlalchemy import Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ScrapeCache(Base):
    __tablename__ = "scrape_cache"

    url: Mapped[str] = mapped_column(Text, primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scraped_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
