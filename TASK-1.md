# Role & Context

You are an Expert Full-Stack Developer debugging a FastAPI + Vue 3 application. We have two distinct issues to fix: a redundant string in a CSV export, and a 404 Not Found error on a specific POST endpoint.

## Task 1: Remove Variant Suffix from Product Name (Backend)

In the endpoint that generates the "Pembelian" CSV (`Pembelian_Toko_{po_id}.csv`), the `product_name` currently includes the variant at the end (e.g., "Product Name - XXL"). Since we already map the variant to `product_variant_name`, we need to strip this suffix.
**Action:**
Before writing the DataFrame to CSV, clean the `product_name` column. If a product name ends with `" - {variant}"`, remove that exact suffix.
*Example Python logic:*
    ```python
    def clean_name(row):
        name = str(row['product_name'])
        variant = str(row['product_variant_name'])
        suffix = f" - {variant}"
        if variant and name.endswith(suffix):
            return name[:-len(suffix)]
        return name

    df['product_name'] = df.apply(clean_name, axis=1)
    ```

## Task 2: Fix 404 Not Found on "Update Stock" (Frontend & Backend)

The frontend triggers a 404 Not Found when clicking "GENERATE UPDATE STOCK" on both the TokoView and UpdateStockView. The console shows it is trying to reach /api/export/update-stock.
Action:

- Backend Verification: Locate the router responsible for this endpoint (e.g., @router.post("/update-stock/")). Ensure it is properly included in main.py (app.include_router(...)).
- Trailing Slash Fix: FastAPI issues a 307 Redirect if a route expects a trailing slash but doesn't get one. On POST requests, this redirect often converts to a GET request or gets blocked, resulting in a 404 or 405.
- Check the frontend API calls in TokoView.vue and UpdateStockView.vue (or their respective Pinia stores).
- Change the fetch/axios URL from `${API}/api/export/update-stock` to `${API}/api/export/update-stock/` (ensure the trailing slash is present).
