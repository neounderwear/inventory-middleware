import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import io

from ..database import get_db
from ..models import MasterProduct, PurchaseOrder, POItem, EntityStock

router = APIRouter(prefix="/api/po", tags=["PO Ingestion"])

TUJUAN_PO_OPTIONS = ["CV GPD", "CV RJM", "7B"]

@router.post("/generate-draft")
async def generate_draft(
    entitas_toko: str = Form(...),
    selected_brands: Optional[str] = Form(None),
    tujuan_po: str = Form("CV GPD"),
    db: Session = Depends(get_db)
):
    if entitas_toko.upper() == "7B":
        raise HTTPException(status_code=400, detail="7B cannot generate POs.")

    if entitas_toko not in ["JAGOAN", "RJM", "GUDANG"]:
        raise HTTPException(status_code=400, detail="entitas_toko must be 'JAGOAN', 'RJM', or 'GUDANG'")

    tujuan_po = (tujuan_po or "").strip().upper()
    if tujuan_po not in TUJUAN_PO_OPTIONS:
        raise HTTPException(status_code=400, detail=f"tujuan_po must be one of: {', '.join(TUJUAN_PO_OPTIONS)}")

    # Fetch toko stock from DB
    toko_entity = "GPD" if entitas_toko == "GUDANG" else entitas_toko
    toko_stocks = db.query(EntityStock).filter(EntityStock.entity == toko_entity).all()
    
    df_toko = pd.DataFrame([{'sku': str(s.sku), 'stok_toko': s.stock} for s in toko_stocks])
    if df_toko.empty:
        df_toko = pd.DataFrame(columns=['sku', 'stok_toko'])


    # Fetch master products
    master_products = db.query(MasterProduct).all()
    if not master_products:
        raise HTTPException(status_code=404, detail="No master products found in database")

    # Fetch destination stock
    target_entity_map = {"CV GPD": "GPD", "CV RJM": "RJM", "7B": "7B"}
    target_entity = target_entity_map.get(tujuan_po, "GPD")
    dest_stocks = db.query(EntityStock).filter(EntityStock.entity == target_entity).all()
    stock_map = {s.sku: s.stock for s in dest_stocks}

    df_master = pd.DataFrame([{
        'sku': p.sku,
        'nama_produk': p.nama_produk or '',
        'brand': p.brand or '',
        'buffer_jagoan': p.buffer_jagoan,
        'buffer_rjm': p.buffer_rjm,
        'stok_tujuan': stock_map.get(p.sku, 0)
    } for p in master_products])

    # Merge with toko stock
    df_merged = df_master.merge(df_toko[['sku', 'stok_toko']], on='sku', how='left')

    # After merging, ensure column names are consistent
    df_merged.columns = df_merged.columns.str.lower().str.strip()
    
    if 'brand' in df_merged.columns:
        df_merged['brand'] = df_merged['brand'].astype(str).str.strip()

    # Fill NaNs in stock with 0
    df_merged['stok_toko'] = df_merged['stok_toko'].fillna(0)

    # Calculate qty_sistem based on entitas_toko
    if entitas_toko == "JAGOAN":
        df_merged['qty_sistem'] = df_merged['buffer_jagoan'] - df_merged['stok_toko']
    elif entitas_toko == "RJM":
        df_merged['qty_sistem'] = df_merged['buffer_rjm'] - df_merged['stok_toko']
    elif entitas_toko == "GUDANG":
        df_merged['qty_sistem'] = 0  # Assuming Gudang doesn't use standard PO buffer calculation

    # Only order if system suggests a quantity > 0 AND Gudang has actual stock
    df_filtered = df_merged[(df_merged['qty_sistem'] > 0) & (df_merged['stok_tujuan'] > 0)].copy()

    # Apply optional filters from the frontend
    if selected_brands:
        import json
        try:
            parsed = json.loads(selected_brands)
            if not isinstance(parsed, list):
                parsed = [str(selected_brands)]
        except json.JSONDecodeError:
            parsed = selected_brands.split(',')
            
        allowed_brands = [str(b).strip().lower() for b in parsed if str(b).strip()]
        df_filtered = df_filtered[df_filtered['brand'].str.lower().isin(allowed_brands)]

    if df_filtered.empty:
        raise HTTPException(status_code=400, detail="No items to draft after applying filters.")

    # Generate PO Number: PO-{ENTITAS}-{YYYYMMDD}-{sequence}
    now = datetime.utcnow()
    today_str = now.strftime("%Y%m%d")
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    po_count_today = db.query(PurchaseOrder).filter(
        PurchaseOrder.entitas_toko == entitas_toko,
        PurchaseOrder.tanggal_dibuat >= today_start
    ).count()
    
    sequence = f"{(po_count_today + 1):03d}"
    nomor_po = f"PO-{entitas_toko}-{today_str}-{sequence}"

    # Create new DRAFT PurchaseOrder
    new_po = PurchaseOrder(
        nomor_po=nomor_po,
        entitas_toko=entitas_toko,
        tujuan_po=tujuan_po,
        status="DRAFT",
        tanggal_dibuat=now
    )
    db.add(new_po)
    db.commit()
    db.refresh(new_po)

    # Sort by brand then product name for logical ordering
    df_filtered = df_filtered.sort_values(by=['brand', 'nama_produk'], ascending=[True, True])

    # Insert PO Items
    po_items_to_insert = []
    for _, row in df_filtered.iterrows():
        item = POItem(
            po_id=new_po.id,
            sku=row['sku'],
            stok_sisa_toko=int(row['stok_toko']),
            stok_sisa_gudang=int(row['stok_tujuan']),
            qty_sistem=int(row['qty_sistem']),
            qty_request=int(row['qty_sistem']),
            qty_fulfilled=0
        )
        po_items_to_insert.append(item)
    
    if po_items_to_insert:
        db.bulk_save_objects(po_items_to_insert)
        db.commit()

    return {
        "po_id": str(new_po.id),
        "nomor_po": new_po.nomor_po,
        "tujuan_po": new_po.tujuan_po,
        "item_count": len(po_items_to_insert)
    }
