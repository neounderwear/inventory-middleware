# Role & Context

You are an Expert Frontend Engineer specializing in Vue 3 (Composition API <script setup>), TypeScript, Tailwind CSS v4, and Pinia.
We have successfully built a FastAPI backend for an "Inventory Middleware" system. Now, we need to build the frontend. The UI/UX strictly follows a "Neo-Brutalism" aesthetic (high-contrast colors, thick borders, sharp solid shadows).

# Tech Stack & Libraries

- Vue 3 + Vite
- TypeScript
- Tailwind CSS v4 (using `@theme` for brutalism tokens)
- Pinia (State Management)
- Vue Router (Routing)
- Axios or native Fetch for API calls

# Design System (Neo-Brutalism)

- Colors: White background, solid bright accents (yellow-300, cyan-300, pink-300).
- Borders: 3px or 4px solid black (`border-black border-[3px]`).
- Shadows: Solid sharp drop shadows (`shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]`).
- Interactions: On `:active` or `:hover`, elements should translate (move) slightly to simulate physical pressing and remove/reduce the shadow.

# Your Tasks (Execute Phase by Phase)

Organize the code neatly into `src/views`, `src/components`, `src/stores`, and `src/router`.

## Phase 5: Core Layout & Store View (Toko PO Management)

1. **Setup & Routing (`router/index.ts`):**
   Create a basic layout with a top navigation bar (Neo-Brutalism style). Define routes: `/` (Home), `/toko` (Store PO), `/gudang` (Fulfillment), `/update-stock` (Reseller Stock).
2. **Store Dashboard (`views/TokoView.vue`):**
   - A form to upload 2 files (`sisa_stok_gpd.xlsx` and `sisa_stok_{toko}.xlsx`) and select `entitas_toko`. POST to `/api/po/generate-draft`.
   - After generation, fetch and display the Draft PO details (GET `/api/po/{po_id}`).
   - Render a data table displaying items. Allow users to edit the `qty_request` using an input field.
   - A massive "CONFIRM PO" button that PUTs to `/api/po/{po_id}/items` and updates the status to `CONFIRMED_BY_STORE`.

## Phase 6: Warehouse Gamification UI (Gudang Fulfillment)

Build a specialized mobile-first view in `views/GudangView.vue`.

1. **PO Selection:** Fetch POs where status is `CONFIRMED_BY_STORE`. User selects one to begin processing.
2. **Interactive Card Mode (The "Game"):**
   - Use Pinia (`stores/fulfillmentStore.ts`) to manage the current PO items array and the index of the currently displayed item.
   - Show ONE large product card at a time on the screen.
   - Display: Product Name, SKU, and `qty_request`.
   - Have a number input for `qty_fulfilled` (defaults to `qty_request`).
   - Provide 3 massive action buttons below the card:
     - 🟢 **READY (Match)**: Sets `qty_fulfilled = qty_request` and moves to the next card.
     - 🟡 **PARTIAL / UPDATE**: Confirms the manually edited `qty_fulfilled` input and moves to the next card.
     - 🔴 **KOSONG (Empty)**: Sets `qty_fulfilled = 0` and moves to the next card.
3. **Summary Screen:**
   - After the last card, show a "Recap" list: fulfilled (green), partial (yellow), empty (red).
   - "SUBMIT FULFILLMENT" button that PUTs the final array to `/api/po/{po_id}/fulfill`.
   - Upon success, display a download button hitting `GET /api/export/olsera/{po_id}` to download the Olsera ZIP files.

## Phase 7: Interactive Stock Update Generator

Build `views/UpdateStockView.vue` for the Warehouse to generate reseller lists.

1. **Upload & Preview:**
   - User uploads `sisa_stok_gpd.xlsx`.
   - Parse or send to backend to extract unique Brands and Categories.
   - Display a preview table of the inventory.
2. **Filter Controls (Top Panel):**
   - Checkbox: "Hide Zero Stock".
   - Multiselect/Checkboxes to hide specific Brands or Categories.
   - Action column in the table with an "Eye" icon to manually hide specific rows.
3. **Generate Action:**
   - Send the file + the applied filter configuration (hidden brands, hide zero stock flag) to `POST /api/export/update-stock`.
   - Trigger the download of the styled `.xlsx` file.

# Rules

- Build strictly using the Vue 3 `<script setup>` syntax.
- Ensure all API URLs use a configurable base URL from Vite env variables (`import.meta.env.VITE_API_URL`).
- Add basic loading states (e.g., "Processing...", "Uploading...") to the brutalist buttons.
- Keep the Gamification UI layout responsive but highly optimized for mobile portrait screens (large tap targets).
