# Role & Context

You are an Expert Python Backend Engineer specializing in FastAPI, Pandas, SQLAlchemy, and PostgreSQL.
We are building an "Inventory Middleware" system to bridge physical stores (Jagoan, RJM) and a Main Warehouse (Gudang). The system ingests Excel exports from an ERP (Olsera), processes logic based on buffer stocks, manages Purchase Orders (PO), and generates formatted CSV/Excel files for re-import and reseller updates.

# Tech Stack

- FastAPI (REST API)
- Pandas & OpenPyXL (Data processing & Excel/CSV generation)
- SQLAlchemy 2.0 (ORM) & PostgreSQL (Database)
- Pydantic (Schema validation)

# Database Schema (Already Defined in models.py)

We have 3 main tables:

1. `master_products`: sku (PK), nama_produk, kategori, brand, buffer_jagoan, buffer_rjm, is_reseller_item (bool).
2. `purchase_orders`: id (UUID), nomor_po, entitas_toko (str), tanggal_dibuat, status (DRAFT, CONFIRMED_BY_STORE, COMPLETED_BY_GUDANG).
3. `po_items`: id, po_id (FK), sku (FK), stok_sisa_toko, stok_sisa_gudang, qty_sistem, qty_request, qty_fulfilled.

# Your Tasks (Execute Phase by Phase)

Please write the complete production-ready Python code for the following phases. Organize the code into a `routers/` directory for modularity.

## Phase 1: Master Data API & Setup (`routers/master.py`)

1. Create CRUD endpoints for `master_products`.
2. Add an endpoint `POST /api/master/upload` that accepts an Excel file to bulk insert/update the master products. Use Pandas to read columns: `SKU`, `Nama Produk`, `Kategori`, `Brand`, `Buffer Jagoan`, `Buffer RJM`, `Is Reseller`.

## Phase 2: Ingestion & Draft PO Generation (`routers/ingestion.py`)

1. Create an endpoint `POST /api/po/generate-draft`. It must accept 2 files via `UploadFile`:
   - `file_gudang` (sisa_stok_gpd.xlsx)
   - `file_toko` (sisa_stok_{toko}.xlsx)
   - `entitas_toko` (form data: "JAGOAN" or "RJM")
2. Using Pandas:
   - Read both files. Assume the columns contain 'SKU' and 'Sisa Stok'.
   - Fetch `master_products` from the DB.
   - For the specific `entitas_toko`, calculate: `qty_sistem = buffer_toko - sisa_stok_toko`.
   - Filter logic: ONLY keep items where `qty_sistem > 0` AND `sisa_stok_gudang > 0`.
3. Create a new `PurchaseOrder` (Status: DRAFT) and insert the filtered items into `po_items` (setting `qty_request` = `qty_sistem`). Return the PO ID.

## Phase 3: PO Management (`routers/po.py`)

1. `GET /api/po`: List all POs with their statuses.
2. `GET /api/po/{po_id}`: Get PO details including joined item data (sku, nama_produk, qty_request, qty_fulfilled).
3. `PUT /api/po/{po_id}/items`: Endpoint for Store Staff to update `qty_request` of specific items and change status to `CONFIRMED_BY_STORE`.
4. `PUT /api/po/{po_id}/fulfill`: Endpoint for Warehouse Staff (Gamification UI). Accepts an array of items to update `qty_fulfilled` and changes PO status to `COMPLETED_BY_GUDANG`.

## Phase 4: Export Engine (`routers/export.py`)

1. `GET /api/export/olsera/{po_id}`:
   - Fetches a completed PO.
   - Generates 2 DataFrames:
     a. `olsera_sales_import_template.csv`: Format for Gudang to deduct stock (Out).
     b. `olsera_order_item_import_template.csv`: Format for Toko to receive stock (In).
   - Use `qty_fulfilled` as the final quantity. Return as a ZIP file or JSON with base64/download links.
2. `POST /api/export/update-stock`:
   - Accepts `sisa_stok_gpd.xlsx` and a JSON payload of filters (hidden_brands, hide_zero_stock).
   - Queries `master_products` where `is_reseller_item == True`.
   - Merges data and filters out excluded brands/categories.
   - Uses `openpyxl` or `xlsxwriter` to generate an exact styled replica of "UPDATE STOCK CV GPD 28-9-2026.xlsx" (yellow headers, bold text, specific column widths).
   - Returns the styled `.xlsx` file via `FileResponse`.

# Rules

- Use Dependency Injection `Depends(get_db)` for all database sessions.
- Keep Pandas data manipulation clean, dropping NA values safely.
- Use `try-except` blocks for file processing to handle wrong formats gracefully. Provide clear error messages in `HTTPException`.
