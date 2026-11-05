from datetime import datetime
from sqlalchemy import String, DateTime, func,Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class CacheEntry(Base):
    __tablename__ = "cache_entries"

    key: Mapped[str] = mapped_column(String(300), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination: Mapped[str] = mapped_column(String(300))
    days: Mapped[int]
    budget: Mapped[int]
    plan: Mapped[list] = mapped_column(JSONB)
    cost: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class TipChunk(Base):
    __tablename__ = "tip_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    section: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(300))
    embedding: Mapped[list] = mapped_column(JSONB)