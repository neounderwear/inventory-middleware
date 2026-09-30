from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from ..database import get_db
from ..models import MasterProduct, PurchaseOrder, POItem

router = APIRouter(prefix="/api/po", tags=["Purchase Orders"])

# --- Schemas ---

class POListResponse(BaseModel):
    id: UUID
    nomor_po: str
    entitas_toko: str
    tanggal_dibuat: datetime
    status: str
    item_count: int

    class Config:
        from_attributes = True

class POItemDetail(BaseModel):
    id: UUID
    sku: str
    nama_produk: str
    stok_sisa_toko: int
    stok_sisa_gudang: int
    qty_sistem: int
    qty_request: int
    qty_fulfilled: int

class PODetailResponse(BaseModel):
    id: UUID
    nomor_po: str
    entitas_toko: str
    tanggal_dibuat: datetime
    status: str
    items: List[POItemDetail]

class POItemUpdateRequest(BaseModel):
    sku: str
    qty_request: int

class POUpdateItemsRequest(BaseModel):
    items: List[POItemUpdateRequest]

class POItemFulfillRequest(BaseModel):
    sku: str
    qty_fulfilled: int

class POFulfillRequest(BaseModel):
    items: List[POItemFulfillRequest]

# --- Endpoints ---

@router.get("/", response_model=List[POListResponse])
def list_pos(db: Session = Depends(get_db)):
    pos = db.query(
        PurchaseOrder.id,
        PurchaseOrder.nomor_po,
        PurchaseOrder.entitas_toko,
        PurchaseOrder.tanggal_dibuat,
        PurchaseOrder.status,
        func.count(POItem.id).label("item_count")
    ).outerjoin(POItem, PurchaseOrder.id == POItem.po_id) \
     .group_by(PurchaseOrder.id).all()
    
    return [
        POListResponse(
            id=po.id,
            nomor_po=po.nomor_po,
            entitas_toko=po.entitas_toko,
            tanggal_dibuat=po.tanggal_dibuat,
            status=po.status,
            item_count=po.item_count
        ) for po in pos
    ]

@router.get("/{po_id}", response_model=PODetailResponse)
def get_po_details(po_id: UUID, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    items_query = db.query(POItem, MasterProduct.nama_produk)\
                    .outerjoin(MasterProduct, POItem.sku == MasterProduct.sku)\
                    .filter(POItem.po_id == po_id).all()
    
    item_details = []
    for item, nama_produk in items_query:
        item_details.append(POItemDetail(
            id=item.id,
            sku=item.sku,
            nama_produk=nama_produk if nama_produk else "Unknown",
            stok_sisa_toko=item.stok_sisa_toko,
            stok_sisa_gudang=item.stok_sisa_gudang,
            qty_sistem=item.qty_sistem,
            qty_request=item.qty_request,
            qty_fulfilled=item.qty_fulfilled
        ))
        
    return PODetailResponse(
        id=po.id,
        nomor_po=po.nomor_po,
        entitas_toko=po.entitas_toko,
        tanggal_dibuat=po.tanggal_dibuat,
        status=po.status,
        items=item_details
    )

@router.put("/{po_id}/items", response_model=dict)
def update_po_items(po_id: UUID, request: POUpdateItemsRequest, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
        
    if po.status != "DRAFT":
        raise HTTPException(status_code=400, detail=f"Cannot confirm PO in {po.status} status. Must be DRAFT.")
    
    # Build a dict of incoming items keyed by SKU
    request_dict = {item.sku: item.qty_request for item in request.items}
    incoming_skus = set(request_dict.keys())
    
    # Fetch all existing PO items from the database
    existing_items = db.query(POItem).filter(POItem.po_id == po_id).all()
    existing_skus = {item.sku for item in existing_items}
    
    # 1. Delete items that are in DB but NOT in the incoming array (user deleted them)
    skus_to_delete = existing_skus - incoming_skus
    if skus_to_delete:
        db.query(POItem).filter(
            POItem.po_id == po_id,
            POItem.sku.in_(skus_to_delete)
        ).delete(synchronize_session="fetch")
    
    # 2. Update qty_request for items that exist in BOTH DB and incoming array
    skus_to_update = existing_skus & incoming_skus
    for item in existing_items:
        if item.sku in skus_to_update:
            item.qty_request = request_dict[item.sku]
    
    # 3. Insert new items that are in incoming array but NOT in DB (manually added)
    skus_to_insert = incoming_skus - existing_skus
    not_found_skus = []
    for sku in skus_to_insert:
        # Look up the SKU in master_products
        master = db.query(MasterProduct).filter(MasterProduct.sku == sku).first()
        if not master:
            not_found_skus.append(sku)
            continue
        
        new_item = POItem(
            po_id=po_id,
            sku=sku,
            stok_sisa_toko=0,
            stok_sisa_gudang=0,
            qty_sistem=0,
            qty_request=request_dict[sku],
            qty_fulfilled=0,
        )
        db.add(new_item)
    
    # Update the PO status
    po.status = "CONFIRMED_BY_STORE"
    db.commit()
    
    result = {"message": "PO items synced and status changed to CONFIRMED_BY_STORE"}
    if not_found_skus:
        result["warnings"] = f"SKUs not found in master_products (skipped): {', '.join(not_found_skus)}"
    
    return result

@router.put("/{po_id}/fulfill", response_model=dict)
def fulfill_po(po_id: UUID, request: POFulfillRequest, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
        
    if po.status != "CONFIRMED_BY_STORE":
        raise HTTPException(status_code=400, detail=f"Cannot fulfill PO in {po.status} status. Must be CONFIRMED_BY_STORE.")
        
    request_dict = {item.sku: item.qty_fulfilled for item in request.items}
    
    po_items = db.query(POItem).filter(POItem.po_id == po_id).all()
    for item in po_items:
        if item.sku in request_dict:
            item.qty_fulfilled = request_dict[item.sku]
            
    po.status = "COMPLETED_BY_GUDANG"
    db.commit()
    
    return {"message": "PO fulfilled and status changed to COMPLETED_BY_GUDANG"}
