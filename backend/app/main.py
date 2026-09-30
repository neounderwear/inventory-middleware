from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import master, ingestion, po, export

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory Middleware API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Ganti dengan URL spesifik saat production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(master.router)
app.include_router(ingestion.router)
app.include_router(po.router)
app.include_router(export.router)

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