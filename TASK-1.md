# Role & Objective

You are an Expert Vue 3 & Vite Developer debugging a production Mixed Content error. The app is deployed behind an Nginx reverse proxy on `https://inventory.underwear.my.id`. Nginx routes `/` to the Vite frontend and `/api` to the FastAPI backend.
Currently, the frontend is forcefully making API calls to `http://...` (insecure), which is being blocked by the browser.

# Task: Project-Wide Inspection & Refactoring to Relative Paths

I need you to scan the entire `frontend` directory and fix how API base URLs are constructed. Since Nginx handles the routing, we must switch to **Relative Paths** to permanently eliminate Mixed Content and CORS issues.

## Step-by-Step Instructions

1. **Search for Hardcoded URLs:**
   Scan all `.ts`, `.js`, and `.vue` files inside `frontend/src/` (especially `src/api`, `src/stores/fulfillmentStore.ts`, or wherever `axios`/`fetch` instances are defined). Look for any string containing `http://`, `localhost`, or `http://inventory.underwear.my.id`.

2. **Refactor Axios/Fetch Configuration:**
   Modify the base API configuration. Remove the reliance on `import.meta.env.VITE_API_URL` if it contains absolute URLs.
   Set the base URL simply to `'/api'`.

   *Example if using Axios:*

   ```typescript
   import axios from 'axios';
   const apiClient = axios.create({
     baseURL: '/api', // <-- This forces the browser to use the current protocol (HTTPS) and host
     headers: { 'Content-Type': 'application/json' }
   });
   ```

Example if using Fetch in a store:
Change fetch('http://.../api/po/') to fetch('/api/po/').

1. Check Environment Variables:
    If the codebase heavily relies on .env, update the .env or .env.production file to set:
    VITE_API_URL=/api

2. Apply Changes:
    Execute the code modifications. Ensure all stores (like the one fetching Confirmed POs) now correctly use the relative path so the browser automatically prepends <https://inventory.underwear.my.id> to the requests.
