# System Architecture

## Components
- **Web UI (Bootstrap + Jinja):** dashboards, bin monitoring, map views, admin forms.
- **Flask Backend:** authentication, CRUD APIs, route optimization, reporting.
- **Database (MySQL/SQLite):** persistent store for bins, readings, routes, alerts, events.
- **IoT Simulation:** generates sensor readings to emulate real bins.

## Diagram
```mermaid
flowchart LR
  U["User/Collector/Admin"] -->|Browser| UI["Flask Templates (Bootstrap)"]
  UI --> API["Flask Controllers (Blueprints)"]
  API --> BL["Business Logic<br/>(Thresholds, Alerts, Optimizer)"]
  BL --> DB["Database<br/>(MySQL/SQLite)"]
  SIM["IoT Simulator"] --> BL
  EXT["(Optional) IoT Devices / MQTT"] -. future .-> BL
  MAP["(Optional) Map Tiles / OSM"] -. internet .-> UI
```

## Notes
- The prototype uses **Haversine distance** for simplicity and explainability.
- Real deployments should use **road-network distances** and include **truck capacity** and **time windows**.

