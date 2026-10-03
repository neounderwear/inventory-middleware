from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine, Base
from .routers import master, ingestion, po, export, metadata

Base.metadata.create_all(bind=engine)

# Lightweight idempotent migrations: create_all() does not add new columns to
# existing tables, so add them here (PostgreSQL supports ADD COLUMN IF NOT EXISTS).
_MIGRATIONS = [
    "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS tujuan_po VARCHAR DEFAULT 'CV GPD'",
    "ALTER TABLE master_products ADD COLUMN IF NOT EXISTS supplier VARCHAR",
    "ALTER TABLE master_products ADD COLUMN IF NOT EXISTS varian VARCHAR",
    "ALTER TABLE master_products ADD COLUMN IF NOT EXISTS harga_beli INTEGER DEFAULT 0",
]
try:
    with engine.begin() as conn:
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))
except Exception as e:
    print(f"Migration warning: {e}")

app = FastAPI(title="Inventory Middleware API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Ganti dengan URL spesifik saat production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Register routers
app.include_router(master.router)
app.include_router(ingestion.router)
app.include_router(po.router)
app.include_router(export.router)
app.include_router(metadata.router)

@app.get("/")
def read_root():
    return {"message": "API Gudang-Toko Middleware Aktif"}

import asyncio
from datetime import datetime, timedelta
from .database import SessionLocal
from .models import PurchaseOrder, POItem

async def cleanup_old_pos():
    while True:
        try:
            db = SessionLocal()
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            # Find old POs
            old_pos = db.query(PurchaseOrder.id).filter(PurchaseOrder.created_at < twenty_four_hours_ago).all()
            old_po_ids = [po.id for po in old_pos]
            
            if old_po_ids:
                # Delete items first to prevent constraint errors
                db.query(POItem).filter(POItem.po_id.in_(old_po_ids)).delete(synchronize_session=False)
                # Delete the POs
                db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(old_po_ids)).delete(synchronize_session=False)
                db.commit()
                
            db.close()
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(3600) # Run every hour

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_pos())