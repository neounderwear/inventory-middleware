from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from io import BytesIO

from ..database import get_db
from ..models import MasterProduct, EntityStock
from .metadata import touch_timestamp

router = APIRouter(prefix="/api/master", tags=["Master Products"])

# Brands whose stock is managed exclusively at RJM (file_rjm overrides GPD stock)
TARGET_BRANDS_RJM = ['crocodile', 'crocodile kids', 'gtman', 'gtman kids']
# Brands whose stock is managed exclusively at 7B (file_7b overrides GPD stock).
# TODO: populate with the real 7B-exclusive brand names (lowercase), e.g. ['brand_a', 'brand_b']
TARGET_BRANDS_7B: List[str] = []

@router.get("/brands", response_model=List[str])
def list_brands(db: Session = Depends(get_db)):
    """Return a distinct, alphabetically sorted list of all brands."""
    brands = db.query(MasterProduct.brand).distinct().order_by(MasterProduct.brand).all()
    return [b[0] for b in brands if b[0]]

class MasterProductBase(BaseModel):
    sku: str
    nama_produk: str
    kategori: Optional[str] = None
    brand: Optional[str] = None
    buffer_jagoan: int = 0
    buffer_rjm: int = 0

class MasterProductCreate(MasterProductBase):
    pass

class MasterProductUpdate(BaseModel):
    nama_produk: Optional[str] = None
    kategori: Optional[str] = None
    brand: Optional[str] = None
    buffer_jagoan: Optional[int] = None
    buffer_rjm: Optional[int] = None

class MasterProductSchema(MasterProductBase):
    class Config:
        from_attributes = True

@router.get("/", response_model=List[MasterProductSchema])
def list_products(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(MasterProduct)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                MasterProduct.sku.ilike(search_term),
                MasterProduct.nama_produk.ilike(search_term)
            )
        )
    return query.all()

@router.get("/{sku}", response_model=MasterProductSchema)
def get_product(sku: str, db: Session = Depends(get_db)):
    product = db.query(MasterProduct).filter(MasterProduct.sku == sku).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=MasterProductSchema)
def create_product(product: MasterProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(MasterProduct).filter(MasterProduct.sku == product.sku).first()
    if db_product:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    new_product = MasterProduct(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.put("/{sku}", response_model=MasterProductSchema)
def update_product(sku: str, product_update: MasterProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(MasterProduct).filter(MasterProduct.sku == sku).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{sku}")
def delete_product(sku: str, db: Session = Depends(get_db)):
    db_product = db.query(MasterProduct).filter(MasterProduct.sku == sku).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.post("/upload")
async def upload_master_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
    
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        required_cols = ['SKU', 'Nama Produk']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        # Drop rows with missing essential data
        df = df.dropna(subset=required_cols)
        
        col_mapping = {
            'SKU': 'sku',
            'Nama Produk': 'nama_produk',
            'Kategori': 'kategori',
            'Brand': 'brand',
            'Buffer Jagoan': 'buffer_jagoan',
            'Buffer RJM': 'buffer_rjm',
            'Supplier': 'supplier',
            'Varian': 'varian',
            'Varian Produk': 'varian',
            'Harga Beli': 'harga_beli'
        }
        
        rename_dict = {k: v for k, v in col_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        # Safe replacement for NaN values
        df = df.where(pd.notnull(df), None)
        
        records = df.to_dict('records')
        
        inserted = 0
        updated = 0
        
        for record in records:
            sku = str(record['sku']).strip()
            if not sku:
                continue
                
            db_product = db.query(MasterProduct).filter(MasterProduct.sku == sku).first()
            if db_product:
                # Update existing
                for k, v in record.items():
                    if hasattr(db_product, k) and k != 'sku':
                        if v is not None:
                            if k in ['buffer_jagoan', 'buffer_rjm', 'harga_beli']:
                                try:
                                    v = int(float(v))
                                except ValueError:
                                    v = 0
                            setattr(db_product, k, v)
                updated += 1
            else:
                # Insert new
                new_data = {}
                for k, v in record.items():
                    if k in ['buffer_jagoan', 'buffer_rjm', 'harga_beli'] and v is not None:
                        try:
                            v = int(float(v))
                        except ValueError:
                            v = 0
                    new_data[k] = v
                
                new_product = MasterProduct(**new_data)
                db.add(new_product)
                inserted += 1
                
        touch_timestamp(db, "last_master_sync")
        db.commit()
        
        return {
            "message": "Upload processed successfully",
            "inserted": inserted,
            "updated": updated
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

async def _read_stock_file(upload: UploadFile, label: str) -> dict:
    """Read an Olsera stock export and return a {sku: stock} dict."""
    if not upload.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail=f"{label} file must be an Excel file (.xlsx, .xls)")
    contents = await upload.read()
    df = pd.read_excel(BytesIO(contents))
    df.columns = df.columns.str.lower().str.strip()
    if 'sku' not in df.columns or 'stock' not in df.columns:
        raise ValueError(f"{label} file missing required columns: 'sku' or 'stock'")
    df = df.dropna(subset=['sku'])
    df['sku'] = df['sku'].astype(str).str.strip()
    df['stock'] = pd.to_numeric(df['stock'], errors='coerce').fillna(0).astype(int)
    return dict(zip(df['sku'], df['stock']))



from ..models import EntityStock

@router.post("/sync-stock/{entity}")
async def sync_entity_stock(
    entity: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    entity = entity.upper()
    if entity not in ["GPD", "RJM", "7B", "JAGOAN", "GUDANG", "CV GPD", "CV RJM"]:
        raise HTTPException(status_code=400, detail="Invalid entity")
    if entity == "GUDANG" or entity == "CV GPD":
        entity = "GPD"  # alias
    if entity == "CV RJM":
        entity = "RJM"

    try:
        stock_updates = await _read_stock_file(file, entity)
        
        # Fetch valid SKUs from master_products
        valid_skus_query = db.query(MasterProduct.sku).all()
        valid_skus = {row[0] for row in valid_skus_query}

        # Filter incoming stock updates to only those existing in master
        stock_updates = {sku: stock for sku, stock in stock_updates.items() if sku in valid_skus}
        
        # Delete existing records for this entity to prevent duplicate/append
        db.query(EntityStock).filter(EntityStock.entity == entity).delete()

        # Insert new records
        new_stocks = []
        for sku, stock in stock_updates.items():
            new_stocks.append(EntityStock(entity=entity, sku=sku, stock=stock))
        
        db.bulk_save_objects(new_stocks)

        # Update timestamp
        touch_timestamp(db, f"last_{entity.lower()}_sync")
        db.commit()

        return {
            "message": f"{entity} stock synced successfully",
            "inserted": len(new_stocks),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error syncing stock: {str(e)}")
