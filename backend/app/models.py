from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .database import Base

class MasterProduct(Base):
    __tablename__ = "master_products"
    
    sku = Column(String, primary_key=True, index=True)
    nama_produk = Column(String, nullable=False)
    kategori = Column(String)
    brand = Column(String)
    buffer_jagoan = Column(Integer, default=0)
    buffer_rjm = Column(Integer, default=0)
    # NOTE: New column — run ALTER TABLE master_products ADD COLUMN stok_aktual_gudang INTEGER DEFAULT 0;
    # or drop/recreate the DB to apply this change.
    stok_aktual_gudang = Column(Integer, default=0)

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nomor_po = Column(String, unique=True, index=True)
    entitas_toko = Column(String, nullable=False) # 'JAGOAN' atau 'RJM'
    tanggal_dibuat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="DRAFT") # DRAFT, CONFIRMED_BY_STORE, COMPLETED_BY_GUDANG
    
    items = relationship("POItem", back_populates="po")

class POItem(Base):
    __tablename__ = "po_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    sku = Column(String, ForeignKey("master_products.sku"))
    
    stok_sisa_toko = Column(Integer, default=0)
    stok_sisa_gudang = Column(Integer, default=0)
    qty_sistem = Column(Integer, default=0)
    qty_request = Column(Integer, default=0)
    qty_fulfilled = Column(Integer, default=0)
    
    po = relationship("PurchaseOrder", back_populates="items")