from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SystemMetadata

router = APIRouter(prefix="/api/metadata", tags=["System Metadata"])

TIMESTAMP_KEYS = ["last_master_sync", "last_gpd_sync", "last_rjm_sync", "last_7b_sync", "last_jagoan_sync"]


def touch_timestamp(db: Session, key: str) -> None:
    """Set the given metadata key to the current UTC time (does NOT commit)."""
    row = db.query(SystemMetadata).filter(SystemMetadata.key == key).first()
    now = datetime.utcnow()
    if row:
        row.updated_at = now
    else:
        db.add(SystemMetadata(key=key, updated_at=now))


@router.get("/timestamps")
def get_timestamps(db: Session = Depends(get_db)) -> Dict[str, Optional[str]]:
    rows = db.query(SystemMetadata).filter(SystemMetadata.key.in_(TIMESTAMP_KEYS)).all()
    found = {r.key: r.updated_at for r in rows}
    # Return ISO-8601 UTC strings (suffix 'Z') so the frontend can localise to WIB
    return {
        key: (found[key].isoformat() + "Z") if found.get(key) else None
        for key in TIMESTAMP_KEYS
    }
