from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from io import BytesIO

from ..database import get_db
from ..models import MasterProduct
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


def _apply_brand_override(db: Session, stock_updates: dict, override_stock: dict, target_brands: List[str]) -> int:
    """Override stock_updates with override_stock for every SKU whose brand is in target_brands.
    SKUs of those brands missing from the override file are set to 0. Returns number of overridden SKUs."""
    if not target_brands:
        return 0
    brands_lower = [b.strip().lower() for b in target_brands]
    exclusive_products = db.query(MasterProduct).filter(
        func.lower(func.trim(MasterProduct.brand)).in_(brands_lower)
    ).all()
    for prod in exclusive_products:
        stock_updates[prod.sku] = override_stock.get(prod.sku, 0)
    return len(exclusive_products)


@router.post("/sync-gudang-stock")
async def sync_gudang_stock(
    file: UploadFile = File(...), 
    file_rjm: Optional[UploadFile] = File(None),
    file_7b: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Sync warehouse stock from Olsera export file (sisa_stok_gpd.xlsx), 
    with optional overrides for brands exclusive to RJM (file_rjm) or 7B (file_7b).
    """
    try:
        # 1. Process main GPD file
        stock_updates = await _read_stock_file(file, "Main (GPD)")
        warnings: List[str] = []
        overridden_rjm = 0
        overridden_7b = 0

        # 2. RJM override (exclusive brands)
        if file_rjm:
            rjm_stock = await _read_stock_file(file_rjm, "RJM")
            overridden_rjm = _apply_brand_override(db, stock_updates, rjm_stock, TARGET_BRANDS_RJM)

        # 3. 7B override (exclusive brands)
        if file_7b:
            stock_7b = await _read_stock_file(file_7b, "7B")
            if not TARGET_BRANDS_7B:
                warnings.append("File 7B diterima, tetapi daftar brand eksklusif 7B (TARGET_BRANDS_7B) masih kosong — tidak ada override.")
            overridden_7b = _apply_brand_override(db, stock_updates, stock_7b, TARGET_BRANDS_7B)

        # 4. Update Database
        all_products = db.query(MasterProduct).all()
        updated = 0
        not_found = 0
        
        for prod in all_products:
            if prod.sku in stock_updates:
                prod.stok_aktual_gudang = stock_updates[prod.sku]
                updated += 1
            else:
                prod.stok_aktual_gudang = 0
                not_found += 1

        # 5. Record sync timestamps
        touch_timestamp(db, "last_gpd_sync")
        if file_rjm:
            touch_timestamp(db, "last_rjm_sync")
        if file_7b:
            touch_timestamp(db, "last_7b_sync")
                
        db.commit()
        
        return {
            "message": "Warehouse stock synced successfully",
            "updated": updated,
            "not_found": not_found,
            "overridden_rjm": overridden_rjm,
            "overridden_7b": overridden_7b,
            "warnings": warnings,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error syncing warehouse stock: {str(e)}")
