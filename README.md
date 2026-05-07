# Smart Waste Management System (Academic Prototype)

Project title: **Design and Development of a Smart Waste Management System for Monitoring Bin Usage and Optimizing Collection Routes**

This is a complete working prototype that includes:
- Dashboard (bin totals, status breakdown, urgent alerts)
- Smart bin monitoring (fill levels + automatic status thresholds)
- Bin detail page (trend chart + mini map + alert history)
- Map module (Leaflet + OSM tiles; falls back gracefully if offline)
- Route optimization (greedy nearest-neighbor with urgency weighting)
- Alerts & notification history (simulated)
- Reports & analytics (collections summary, hotspots, route efficiency)
- Roles: **Admin**, **Worker (Driver/Collector)**, and **User (Reporter)**

## Recommended stack
- Backend: **Python Flask**
- Frontend: **Bootstrap + Jinja templates**
- Database: **MySQL** (supported via `DATABASE_URL`) or **SQLite** for quick local testing

## Frontend folder integration
- The project uses the `frontend/` folder as the primary UI template location.
- Flask is configured to load Jinja templates from `frontend/` first, and to serve its assets at `/frontend/...`.

## 1) Setup (SQLite quick start)
1. Open PowerShell in this folder: `smart-waste-management`
2. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Create `.env` from `.env.example` (optional; defaults to SQLite):
   - `Copy-Item .env.example .env`
5. Initialize DB with sample data:
   - `python scripts/init_db.py`
6. Run the app:
   - `python run.py`
7. Open:
   - Landing page: `http://127.0.0.1:5000`
   - Dashboard: `http://127.0.0.1:5000/dashboard`

### Sample accounts
- Admin: `admin@123` / `admin123`
- Worker: `driver1` / `Driver123!`
- Worker: `driver2` / `Driver123!`
- User: `citizen` / `Public123!`

## Key pages
- Landing: `/`
- Dashboard: `/dashboard`
- Bin list: `/bins`
- Bin detail: `/bins/<id>`
- Report a bin (public users): `/bins/<id>/report`
- Admin analytics (charts): `/admin/analytics`

## Roles (3 parts)
- **Admin**: manages bins, trucks, routes, alerts, analytics, reports, and runs IoT simulation.
- **Worker (Driver/Collector)**: views assigned route and marks bins as collected (emptied).
- **User (Reporter)**: reports bins that appear full/overflowing (community feedback).

## How we simulate IoT data
- Admin UI: `Admin → Simulate IoT` generates sensor readings and updates bin fill levels/status automatically.
- API (optional): POST to `/api/sensor/update` with JSON `{ "bin_code": "BIN-001", "fill_level": 82 }`.
- Simulation creates `sensor_readings` rows and triggers `alerts` + `notification_logs` when thresholds are hit.

## 2) Setup (MySQL)
1. Create a MySQL database named `smart_waste`
2. Update `.env`:
   - `DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/smart_waste`
3. Create tables:
   - Either run the SQL in `schema/mysql_schema.sql`
   - Or run `python scripts/init_db.py` (uses SQLAlchemy `create_all`)

## 3) How modules work (brief)
- **Dashboard:** counts bins by status; lists active alerts.
- **Smart bin monitoring:** each update writes a `sensor_readings` row and updates `bins.status`.
- **Alerts:** when status becomes Full/Overflow, an active alert is created; when emptied, alerts are resolved.
- **Notifications:** each new alert creates simulated `system`, `email`, and `sms` notification log entries.
- **Route optimization:** admin generates routes from bins above a threshold; bins are split across trucks and ordered by greedy heuristic.
- **Collector flow:** collector opens `My Route` and clicks **Collect** to empty a bin and record a collection event.
- **Reports:** analytics are computed live; reports can also be generated and saved (CRUD) under Saved reports.

## 4) Key folders
- `app/` Flask app (blueprints, models, templates, static)
- `scripts/` database initializer and sample seed
- `schema/` MySQL schema
- `docs/` academic write-up support + diagrams

## 5) Testing
See `docs/testing_guide.md`.
