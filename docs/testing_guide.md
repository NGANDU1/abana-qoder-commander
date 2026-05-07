# Testing Guide (Manual)

## A) Smoke Test
1. Run `python scripts/init_db.py`
2. Run `python run.py`
3. Open `http://127.0.0.1:5000`
4. Note: UI templates are served from the `frontend/` folder (assets at `/frontend/...`).

## B) Authentication & Roles
1. Login as `admin` / `Admin123!`
2. Confirm you can open:
   - Admin → Users / Trucks / Alerts / Routes / Reports
3. Logout and login as `driver1` / `Driver123!`
4. Confirm you can open:
   - Bins (and update level)
   - My Route

## C) Bin Monitoring + Alerts
1. Login as admin
2. Go to Admin → Simulate IoT → Run simulation
3. Verify:
   - Some bins become Full/Overflow
   - Alerts appear in Admin → Alerts and Dashboard

## D) Route Optimization
1. Login as admin
2. Go to Admin → Generate routes
3. Use threshold `70` and `2` trucks
4. Verify:
   - Routes are created (Admin → Routes)
   - Route details show ordered stops and a polyline map

## E) Collector Workflow
1. Login as `driver1`
2. Open My Route
3. Click Collect on a stop
4. Verify:
   - Bin fill level becomes 0%
   - Alerts for that bin are resolved
   - Route stop becomes collected
   - Route auto-completes when all stops are collected

## F) Reports (Analytics + Saved Reports)
1. Login as admin
2. Go to Admin → Reports
3. Generate a few collection events (collect some stops)
4. Confirm tables populate
5. Go to Saved reports → Generate & Save
6. View the saved report, then delete it (CRUD)
