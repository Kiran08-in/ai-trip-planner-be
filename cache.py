from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal
from models import CacheEntry


def get_cached(key):
    try:
        with SessionLocal() as db:
            row = db.get(CacheEntry, key)
            if row is None:
                return None
            if row.expires_at <= datetime.now(timezone.utc):
                return None
            return row.value["data"]
    except SQLAlchemyError as e:
        print("cache read error:", repr(e))
        return None


def set_cached(key, data, ttl_hours):
    try:
        expires = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        stmt = insert(CacheEntry).values(
            key=key, value={"data": data}, expires_at=expires
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={"value": stmt.excluded.value, "expires_at": stmt.excluded.expires_at},
        )
        with SessionLocal() as db:
            db.execute(stmt)
            db.commit()
    except SQLAlchemyError as e:
        print("cache write error:", repr(e))