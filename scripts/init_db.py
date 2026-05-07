"""
Initialize the database and insert realistic sample data for demos/testing.

Usage:
  python scripts/init_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import random

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from datetime import date

from app.models import Bin, Route, RouteStop, Truck, User
from app.utils.bin_logic import update_bin_fill_level
from app.utils.geo import Point, haversine_km
from app.utils.routing import CandidateBin, build_greedy_route, split_routes_round_robin, urgency_score


def seed_users() -> dict[str, User]:
    admin = User(
        username="admin@123",
        email="admin@city.gov",
        first_name="System",
        last_name="Admin",
        phone_number="+44 0000 000000",
        employee_id="ADM-001",
        role="admin",
        is_active=True,
    )
    admin.set_password("admin123")

    driver1 = User(
        username="driver1",
        email="driver1@city.gov",
        first_name="Driver",
        last_name="One",
        phone_number="+44 0000 000001",
        employee_id="WRK-001",
        role="worker",
        is_active=True,
    )
    driver1.set_password("Driver123!")

    driver2 = User(
        username="driver2",
        email="driver2@city.gov",
        first_name="Driver",
        last_name="Two",
        phone_number="+44 0000 000002",
        employee_id="WRK-002",
        role="worker",
        is_active=True,
    )
    driver2.set_password("Driver123!")

    citizen = User(
        username="citizen",
        email="citizen@example.com",
        first_name="Public",
        last_name="User",
        phone_number="+44 0000 000003",
        role="user",
        is_active=True,
    )
    citizen.set_password("Public123!")

    db.session.add_all([admin, driver1, driver2, citizen])
    db.session.flush()
    return {"admin": admin, "driver1": driver1, "driver2": driver2, "citizen": citizen}


def seed_trucks(users: dict[str, User]) -> list[Truck]:
    t1 = Truck(name="Truck A", plate_no="SWM-001", status="active", driver_id=users["driver1"].id)
    t2 = Truck(name="Truck B", plate_no="SWM-002", status="active", driver_id=users["driver2"].id)
    db.session.add_all([t1, t2])
    db.session.flush()
    return [t1, t2]


def seed_bins() -> list[Bin]:
    """
    Coordinates are around London for a consistent demo.
    """

    bins = [
        ("BIN-001", "Oxford Street (near station)", "Central", 51.5152, -0.1419, "General", 82),
        ("BIN-002", "Soho Square", "Central", 51.5154, -0.1311, "Plastic", 55),
        ("BIN-003", "Trafalgar Square", "Central", 51.5080, -0.1281, "General", 91),
        ("BIN-004", "King's Cross (main entrance)", "North", 51.5308, -0.1238, "General", 77),
        ("BIN-005", "Camden Market", "North", 51.5410, -0.1420, "Organic", 63),
        ("BIN-006", "Shoreditch High Street", "East", 51.5246, -0.0785, "Plastic", 88),
        ("BIN-007", "Canary Wharf (plaza)", "East", 51.5054, -0.0235, "General", 46),
        ("BIN-008", "London Bridge (south side)", "South", 51.5055, -0.0865, "General", 94),
        ("BIN-009", "Brixton (market road)", "South", 51.4613, -0.1166, "Organic", 58),
        ("BIN-010", "Hammersmith Broadway", "West", 51.4920, -0.2243, "General", 73),
        ("BIN-011", "Notting Hill Gate", "West", 51.5091, -0.1960, "Glass", 38),
        ("BIN-012", "Greenwich Park (main gate)", "East", 51.4769, 0.0005, "Paper", 67),
    ]

    out: list[Bin] = []
    for code, loc, area, lat, lon, wt, initial in bins:
        b = Bin(
            bin_code=code,
            location_name=loc,
            area=area,
            latitude=lat,
            longitude=lon,
            waste_type=wt,
        )
        db.session.add(b)
        db.session.flush()
        update_bin_fill_level(b, initial, source="sim")
        out.append(b)

    # Add a few extra bins with randomized fill (for filtering/reporting variety)
    extra_areas = ["Central", "North", "East", "South", "West"]
    extra_waste = ["General", "Plastic", "Organic", "Paper", "Glass", "Metal"]
    for i in range(13, 21):
        lat = 51.50 + random.uniform(-0.06, 0.06)
        lon = -0.12 + random.uniform(-0.10, 0.10)
        b = Bin(
            bin_code=f"BIN-{i:03d}",
            location_name=f"Smart Bin Point {i}",
            area=random.choice(extra_areas),
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            waste_type=random.choice(extra_waste),
        )
        db.session.add(b)
        db.session.flush()
        update_bin_fill_level(b, random.randint(5, 98), source="sim")
        out.append(b)

    return out


def seed_routes(admin_user: User, trucks: list[Truck], threshold: int, depot: Point) -> None:
    """
    Create example optimized routes so the system has route data immediately after initialization.
    """

    candidates = Bin.query.filter(Bin.fill_level >= threshold).order_by(Bin.fill_level.desc()).all()
    if not candidates or not trucks:
        return

    candidate_bins = [
        CandidateBin(
            id=b.id,
            code=b.bin_code,
            point=Point(b.latitude, b.longitude),
            fill_level=b.fill_level,
            status=b.status,
        )
        for b in candidates
    ]
    candidate_bins.sort(key=lambda x: urgency_score(x.fill_level, x.status), reverse=True)
    buckets = split_routes_round_robin(candidate_bins, len(trucks))

    today = date.today()
    for idx, truck in enumerate(trucks):
        bucket = buckets[idx]
        if not bucket:
            continue
        ordered, total_km = build_greedy_route(depot, bucket)
        code = f"RT-{today.strftime('%Y%m%d')}-{truck.id:02d}-SEED"
        r = Route(
            route_code=code,
            date_for=today,
            algorithm="Greedy Nearest-Neighbor (Urgency Weighted)",
            status="planned",
            total_distance_km=total_km,
            created_by_id=admin_user.id,
            truck_id=truck.id,
            driver_id=truck.driver_id,
        )
        db.session.add(r)
        db.session.flush()

        prev = depot
        for seq, cb in enumerate(ordered, start=1):
            dist = haversine_km(prev, cb.point)
            db.session.add(RouteStop(route_id=r.id, seq=seq, bin_id=cb.id, distance_from_prev_km=round(dist, 3)))
            prev = cb.point


def main() -> None:
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        users = seed_users()
        trucks = seed_trucks(users)
        seed_bins()
        depot = Point(lat=app.config["DEPOT_LAT"], lon=app.config["DEPOT_LON"])
        seed_routes(users["admin"], trucks, threshold=70, depot=depot)
        db.session.commit()

    print("Database initialized with sample data.")
    print("Sample logins:")
    print("  admin@123 / admin123")
    print("  driver1 / Driver123!")
    print("  driver2 / Driver123!")
    print("  citizen / Public123!")


if __name__ == "__main__":
    main()
