from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
import json

from ...models import Alert, Bin, BinReport, CollectionEvent, GeneratedReport, NotificationLog, Route, RouteStop, Truck, User
from ...utils.bin_logic import update_bin_fill_level
from ...utils.geo import Point, haversine_km
from ...utils.routing import CandidateBin, build_greedy_route, split_routes_round_robin, urgency_score
from ...utils.security import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@login_required
@role_required("admin")
def admin_home():
    today = date.today()
    start_day = today - timedelta(days=6)

    # KPIs
    total_collections = CollectionEvent.query.count()
    active_drivers = User.query.filter(User.role.in_(["worker", "collector"])).count()
    vehicles = Truck.query.count()
    waste_collected_proxy = (
        db.session.query(func.coalesce(func.sum(CollectionEvent.before_fill_level), 0))
        .scalar()
        or 0
    )

    # Collections per day (last 7 days)
    start_dt = datetime(start_day.year, start_day.month, start_day.day, tzinfo=timezone.utc)
    rows = (
        db.session.query(func.date(CollectionEvent.collected_at).label("d"), func.count(CollectionEvent.id))
        .filter(CollectionEvent.collected_at >= start_dt)
        .group_by(func.date(CollectionEvent.collected_at))
        .all()
    )
    by_day = {r[0]: int(r[1]) for r in rows}
    labels = [(start_day + timedelta(days=i)).isoformat() for i in range(7)]
    series = [by_day.get(lbl, 0) for lbl in labels]

    # Status breakdown (using route stops)
    collected_stops = RouteStop.query.filter_by(status="collected").count()
    pending_stops = RouteStop.query.filter_by(status="pending").count()
    skipped_stops = RouteStop.query.filter_by(status="skipped").count()

    urgent_alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).limit(6).all()

    # Top drivers (last 30 days)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    top_driver_rows = (
        db.session.query(CollectionEvent.collector_id, func.count(CollectionEvent.id).label("c"))
        .filter(CollectionEvent.collector_id.isnot(None))
        .filter(CollectionEvent.collected_at >= since)
        .group_by(CollectionEvent.collector_id)
        .order_by(func.count(CollectionEvent.id).desc())
        .limit(5)
        .all()
    )
    top_driver_ids = [r[0] for r in top_driver_rows]
    users_by_id = {u.id: u for u in User.query.filter(User.id.in_(top_driver_ids)).all()} if top_driver_ids else {}
    top_drivers = [
        {"name": (users_by_id.get(r[0]).username if users_by_id.get(r[0]) else "Unknown"), "count": int(r[1])}
        for r in top_driver_rows
    ]

    return render_template(
        "admin/home.html",
        kpis={
            "total_collections": total_collections,
            "active_drivers": active_drivers,
            "vehicles": vehicles,
            "waste_collected_proxy": int(waste_collected_proxy),
        },
        charts={
            "collections_labels": labels,
            "collections_series": series,
            "stops_breakdown": {"collected": collected_stops, "pending": pending_stops, "skipped": skipped_stops},
        },
        today_str=today.strftime("%b %d, %Y"),
        urgent_alerts=urgent_alerts,
        top_drivers=top_drivers,
    )


# ---------------------------
# Bins CRUD
# ---------------------------


@bp.get("/bins")
@login_required
@role_required("admin")
def bins():
    bins_list = Bin.query.order_by(Bin.bin_code.asc()).all()
    return render_template("admin/bins.html", bins=bins_list)


@bp.get("/bins/new")
@login_required
@role_required("admin")
def bin_create():
    return render_template("admin/bin_form.html", mode="create", bin=None)


@bp.post("/bins/new")
@login_required
@role_required("admin")
def bin_create_post():
    bin_code = (request.form.get("bin_code") or "").strip().upper()
    location_name = (request.form.get("location_name") or "").strip()
    area = (request.form.get("area") or "").strip() or None
    waste_type = (request.form.get("waste_type") or "General").strip()
    latitude = float(request.form.get("latitude") or "0")
    longitude = float(request.form.get("longitude") or "0")
    fill_level = int(request.form.get("fill_level") or "0")

    if not bin_code or not location_name:
        flash("Bin ID and location are required.", "danger")
        return redirect(url_for("admin.bin_create"))
    if Bin.query.filter_by(bin_code=bin_code).first():
        flash("Bin ID already exists.", "danger")
        return redirect(url_for("admin.bin_create"))

    b = Bin(
        bin_code=bin_code,
        location_name=location_name,
        area=area,
        waste_type=waste_type,
        latitude=latitude,
        longitude=longitude,
    )
    db.session.add(b)
    db.session.flush()
    update_bin_fill_level(b, fill_level, source="manual")
    db.session.commit()

    flash("Bin created.", "success")
    return redirect(url_for("public.bins"))


@bp.get("/bins/<int:bin_id>/edit")
@login_required
@role_required("admin")
def bin_edit(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))
    return render_template("admin/bin_form.html", mode="edit", bin=b)


@bp.post("/bins/<int:bin_id>/edit")
@login_required
@role_required("admin")
def bin_edit_post(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))

    b.location_name = (request.form.get("location_name") or "").strip() or b.location_name
    b.area = (request.form.get("area") or "").strip() or None
    b.waste_type = (request.form.get("waste_type") or b.waste_type).strip()
    b.latitude = float(request.form.get("latitude") or b.latitude)
    b.longitude = float(request.form.get("longitude") or b.longitude)

    db.session.commit()
    flash("Bin updated.", "success")
    return redirect(url_for("public.bins"))


@bp.get("/bins/<int:bin_id>/delete")
@login_required
@role_required("admin")
def bin_delete(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))
    db.session.delete(b)
    db.session.commit()
    flash("Bin deleted.", "info")
    return redirect(url_for("public.bins"))


@bp.get("/bins/<int:bin_id>/update-level")
@login_required
@role_required("admin", "worker")
def bin_update_level(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))
    return render_template("admin/bin_update_level.html", b=b)


@bp.post("/bins/<int:bin_id>/update-level")
@login_required
@role_required("admin", "worker")
def bin_update_level_post(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))

    fill_level = int(request.form.get("fill_level") or b.fill_level)
    source = "manual"
    update_bin_fill_level(b, fill_level, source=source)
    db.session.commit()
    flash(f"{b.bin_code} updated to {b.fill_level}% ({b.status}).", "success")
    return redirect(url_for("public.bins"))


# ---------------------------
# Community/User Reports
# ---------------------------


@bp.get("/user-reports")
@login_required
@role_required("admin")
def user_reports():
    status = (request.args.get("status") or "").strip() or None

    q = BinReport.query
    if status:
        q = q.filter(BinReport.status == status)

    reports = q.order_by(BinReport.created_at.desc()).limit(200).all()
    drivers = (
        User.query.filter(User.role.in_(["worker", "collector"]))
        .filter_by(is_active=True)
        .order_by(User.username.asc())
        .all()
    )

    return render_template(
        "admin/user_reports.html",
        reports=reports,
        drivers=drivers,
        filters={"status": status or ""},
    )


@bp.post("/user-reports/<int:report_id>/assign")
@login_required
@role_required("admin")
def user_reports_assign(report_id: int):
    r = db.session.get(BinReport, report_id)
    if not r or not r.bin:
        flash("Report not found.", "danger")
        return redirect(url_for("admin.user_reports"))

    driver_id = int(request.form.get("driver_id") or "0")
    driver = db.session.get(User, driver_id)
    if not driver or not driver.is_worker or not driver.is_active:
        flash("Please choose a valid active driver.", "danger")
        return redirect(url_for("admin.user_reports"))

    today = date.today()

    route = (
        Route.query.filter_by(driver_id=driver.id, date_for=today)
        .filter(Route.status.in_(["planned", "in_progress"]))
        .order_by(Route.created_at.desc())
        .first()
    )
    if not route:
        # Create a simple manual route for the driver for today.
        base = f"MAN-{today.strftime('%Y%m%d')}-{driver.id}"
        existing = Route.query.filter(Route.route_code.like(f"{base}%")).count()
        route_code = f"{base}-{existing + 1:02d}"
        route = Route(route_code=route_code, date_for=today, algorithm="Manual Assignment", status="planned")
        route.driver_id = driver.id
        route.created_by_id = current_user.id
        db.session.add(route)
        db.session.flush()

    last_seq = (
        db.session.query(func.coalesce(func.max(RouteStop.seq), 0))
        .filter(RouteStop.route_id == route.id)
        .scalar()
        or 0
    )

    # Avoid duplicate pending stops for the same bin on this route.
    existing_stop = (
        RouteStop.query.filter_by(route_id=route.id, bin_id=r.bin_id)
        .filter(RouteStop.status.in_(["pending", "collected"]))
        .first()
    )
    if not existing_stop:
        db.session.add(RouteStop(route_id=route.id, seq=int(last_seq) + 1, bin_id=r.bin_id, status="pending"))

    r.status = "reviewed"
    r.reviewed_at = datetime.now(timezone.utc)

    db.session.add(
        NotificationLog(
            alert_id=None,
            channel="system",
            recipient=driver.username,
            message=f"New assignment: collect bin {r.bin.bin_code} ({r.bin.location_name}).",
        )
    )

    db.session.commit()
    flash(f"Sent {r.bin.bin_code} to driver {driver.username}.", "success")
    return redirect(url_for("admin.user_reports"))


# ---------------------------
# Users CRUD (Admin)
# ---------------------------


@bp.get("/users")
@login_required
@role_required("admin")
def users():
    users_list = User.query.order_by(User.role.asc(), User.username.asc()).all()
    return render_template("admin/users.html", users=users_list)


@bp.get("/users/new")
@login_required
@role_required("admin")
def user_create():
    return render_template("admin/user_form.html", mode="create", u=None)


@bp.post("/users/new")
@login_required
@role_required("admin")
def user_create_post():
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip() or None
    first_name = (request.form.get("first_name") or "").strip() or None
    last_name = (request.form.get("last_name") or "").strip() or None
    phone_number = (request.form.get("phone_number") or "").strip() or None
    employee_id = (request.form.get("employee_id") or "").strip() or None
    role = (request.form.get("role") or "user").strip()
    password = request.form.get("password") or ""

    if not username or not password:
        flash("Username and password are required.", "danger")
        return redirect(url_for("admin.user_create"))
    if not first_name or not last_name:
        flash("First name and surname are required.", "danger")
        return redirect(url_for("admin.user_create"))
    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for("admin.user_create"))
    if not phone_number:
        flash("Phone number is required.", "danger")
        return redirect(url_for("admin.user_create"))
    if role not in ("admin", "worker", "user"):
        flash("Invalid role.", "danger")
        return redirect(url_for("admin.user_create"))
    if role in ("admin", "worker") and not employee_id:
        flash("Employee ID is required for worker/admin accounts.", "danger")
        return redirect(url_for("admin.user_create"))
    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "danger")
        return redirect(url_for("admin.user_create"))
    if email and User.query.filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("admin.user_create"))
    if employee_id and User.query.filter_by(employee_id=employee_id).first():
        flash("Employee ID already exists.", "danger")
        return redirect(url_for("admin.user_create"))

    u = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        employee_id=employee_id,
        role=role,
        is_active=True,
    )
    u.set_password(password)
    db.session.add(u)
    db.session.commit()

    flash("User created.", "success")
    return redirect(url_for("admin.users"))


@bp.get("/users/<int:user_id>/toggle")
@login_required
@role_required("admin")
def user_toggle(user_id: int):
    u = db.session.get(User, user_id)
    if not u:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))
    if u.role == "admin" and u.is_active:
        # Basic safety: don't disable the only active admin.
        active_admins = User.query.filter_by(role="admin", is_active=True).count()
        if active_admins <= 1:
            flash("Cannot disable the last active admin.", "danger")
            return redirect(url_for("admin.users"))

    u.is_active = not u.is_active
    db.session.commit()
    flash("User updated.", "info")
    return redirect(url_for("admin.users"))


# ---------------------------
# Trucks CRUD
# ---------------------------


@bp.get("/trucks")
@login_required
@role_required("admin")
def trucks():
    trucks_list = Truck.query.order_by(Truck.status.asc(), Truck.name.asc()).all()
    collectors = User.query.filter_by(role="worker", is_active=True).order_by(User.username.asc()).all()
    return render_template("admin/trucks.html", trucks=trucks_list, collectors=collectors)


@bp.post("/trucks/new")
@login_required
@role_required("admin")
def truck_create_post():
    name = (request.form.get("name") or "").strip()
    plate_no = (request.form.get("plate_no") or "").strip().upper()
    driver_id = request.form.get("driver_id")
    status = (request.form.get("status") or "active").strip()

    if not name or not plate_no:
        flash("Truck name and plate number are required.", "danger")
        return redirect(url_for("admin.trucks"))
    if Truck.query.filter_by(plate_no=plate_no).first():
        flash("Plate number already exists.", "danger")
        return redirect(url_for("admin.trucks"))

    t = Truck(name=name, plate_no=plate_no, status=status)
    if driver_id:
        t.driver_id = int(driver_id)
    db.session.add(t)
    db.session.commit()
    flash("Truck created.", "success")
    return redirect(url_for("admin.trucks"))


@bp.get("/trucks/<int:truck_id>/delete")
@login_required
@role_required("admin")
def truck_delete(truck_id: int):
    t = db.session.get(Truck, truck_id)
    if not t:
        flash("Truck not found.", "danger")
        return redirect(url_for("admin.trucks"))
    db.session.delete(t)
    db.session.commit()
    flash("Truck deleted.", "info")
    return redirect(url_for("admin.trucks"))


@bp.post("/trucks/<int:truck_id>/assign")
@login_required
@role_required("admin")
def truck_assign(truck_id: int):
    t = db.session.get(Truck, truck_id)
    if not t:
        flash("Truck not found.", "danger")
        return redirect(url_for("admin.trucks"))
    driver_id = request.form.get("driver_id") or None
    t.driver_id = int(driver_id) if driver_id else None
    t.status = (request.form.get("status") or t.status).strip()
    db.session.commit()
    flash("Truck updated.", "success")
    return redirect(url_for("admin.trucks"))


# ---------------------------
# Alerts
# ---------------------------


@bp.get("/alerts")
@login_required
@role_required("admin")
def alerts():
    active = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).all()
    history = Alert.query.filter_by(is_active=False).order_by(Alert.created_at.desc()).limit(50).all()
    return render_template("admin/alerts.html", active=active, history=history)


@bp.get("/notifications")
@login_required
@role_required("admin")
def notifications():
    logs = NotificationLog.query.order_by(NotificationLog.created_at.desc()).limit(100).all()
    return render_template("admin/notifications.html", logs=logs)


@bp.get("/alerts/<int:alert_id>/resolve")
@login_required
@role_required("admin")
def alert_resolve(alert_id: int):
    a = db.session.get(Alert, alert_id)
    if not a:
        flash("Alert not found.", "danger")
        return redirect(url_for("admin.alerts"))
    a.is_active = False
    a.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Alert resolved.", "success")
    return redirect(url_for("admin.alerts"))


# ---------------------------
# Route optimization
# ---------------------------


@bp.get("/routes")
@login_required
@role_required("admin")
def routes_list():
    routes = Route.query.order_by(Route.created_at.desc()).limit(30).all()
    return render_template("admin/routes.html", routes=routes)


@bp.get("/routes/new")
@login_required
@role_required("admin")
def routes_new():
    trucks = Truck.query.filter_by(status="active").order_by(Truck.name.asc()).all()
    drivers = (
        User.query.filter(User.role.in_(["worker", "collector"]))
        .filter_by(is_active=True)
        .order_by(User.username.asc())
        .all()
    )
    return render_template("admin/routes_new.html", trucks=trucks, drivers=drivers)


@bp.post("/routes/new")
@login_required
@role_required("admin")
def routes_new_post():
    threshold = int(request.form.get("threshold") or "70")
    num_trucks = int(request.form.get("num_trucks") or "1")
    driver_id = int(request.form.get("driver_id") or "0")

    all_active_trucks = Truck.query.filter_by(status="active").order_by(Truck.name.asc()).all()

    if driver_id:
        all_active_trucks = [t for t in all_active_trucks if t.driver_id == driver_id]

    selected_trucks = all_active_trucks[: max(1, min(num_trucks, len(all_active_trucks)))]
    if not selected_trucks:
        flash("No active trucks available for that driver." if driver_id else "No active trucks available.", "danger")
        return redirect(url_for("admin.routes_new"))

    # Choose bins for pickup.
    candidates = (
        Bin.query.filter(Bin.fill_level >= threshold)
        .order_by(Bin.fill_level.desc())
        .all()
    )
    if not candidates:
        flash("No bins meet the pickup threshold.", "info")
        return redirect(url_for("admin.routes_new"))

    depot = Point(lat=current_app.config["DEPOT_LAT"], lon=current_app.config["DEPOT_LON"])
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

    # Prioritize: highest urgency first.
    candidate_bins.sort(key=lambda x: urgency_score(x.fill_level, x.status), reverse=True)
    bucketed = split_routes_round_robin(candidate_bins, len(selected_trucks))

    created_routes: list[Route] = []
    today = date.today()

    for idx, truck in enumerate(selected_trucks):
        bins_for_truck = bucketed[idx]
        if not bins_for_truck:
            continue

        ordered, total_km = build_greedy_route(depot, bins_for_truck)
        code = f"RT-{today.strftime('%Y%m%d')}-{truck.id:02d}-{int(datetime.now().timestamp())%10000:04d}"
        r = Route(
            route_code=code,
            date_for=today,
            algorithm="Greedy Nearest-Neighbor (Urgency Weighted)",
            status="planned",
            created_by_id=current_user.id,
            truck_id=truck.id,
            driver_id=truck.driver_id,
            total_distance_km=total_km,
        )
        db.session.add(r)
        db.session.flush()

        prev = depot
        for s, cb in enumerate(ordered, start=1):
            dist = haversine_km(prev, cb.point)
            db.session.add(
                RouteStop(route_id=r.id, seq=s, bin_id=cb.id, distance_from_prev_km=round(dist, 3))
            )
            prev = cb.point

        created_routes.append(r)

    db.session.commit()
    flash(f"Generated {len(created_routes)} route(s) using greedy optimization.", "success")
    return redirect(url_for("admin.routes_list"))


@bp.get("/routes/<int:route_id>")
@login_required
@role_required("admin")
def route_detail(route_id: int):
    r = db.session.get(Route, route_id)
    if not r:
        flash("Route not found.", "danger")
        return redirect(url_for("admin.routes_list"))
    stops = RouteStop.query.filter_by(route_id=r.id).order_by(RouteStop.seq.asc()).all()
    depot = {"lat": current_app.config["DEPOT_LAT"], "lon": current_app.config["DEPOT_LON"]}
    stops_points = [
        {
            "seq": s.seq,
            "bin_code": s.bin.bin_code,
            "lat": s.bin.latitude,
            "lon": s.bin.longitude,
            "status": s.bin.status,
            "fill_level": s.bin.fill_level,
        }
        for s in stops
    ]
    return render_template("admin/route_detail.html", r=r, stops=stops, depot=depot, stops_points=stops_points)


@bp.get("/routes/<int:route_id>/start")
@login_required
@role_required("admin")
def route_start(route_id: int):
    r = db.session.get(Route, route_id)
    if not r:
        flash("Route not found.", "danger")
        return redirect(url_for("admin.routes_list"))
    r.status = "in_progress"
    db.session.commit()
    flash("Route set to in progress.", "success")
    return redirect(url_for("admin.route_detail", route_id=r.id))


@bp.get("/routes/<int:route_id>/complete")
@login_required
@role_required("admin")
def route_complete(route_id: int):
    r = db.session.get(Route, route_id)
    if not r:
        flash("Route not found.", "danger")
        return redirect(url_for("admin.routes_list"))
    r.status = "completed"
    db.session.commit()
    flash("Route marked completed.", "info")
    return redirect(url_for("admin.route_detail", route_id=r.id))


# ---------------------------
# IoT simulation
# ---------------------------


@bp.get("/simulate")
@login_required
@role_required("admin")
def simulate_get():
    return render_template("admin/simulate.html")


@bp.post("/simulate")
@login_required
@role_required("admin")
def simulate_post():
    import random

    mode = (request.form.get("mode") or "random-increase").strip()
    iterations = int(request.form.get("iterations") or "1")
    iterations = max(1, min(50, iterations))

    bins = Bin.query.all()
    if not bins:
        flash("No bins to simulate.", "info")
        return redirect(url_for("admin.simulate_get"))

    for _ in range(iterations):
        for b in bins:
            if mode == "random-increase":
                delta = random.randint(0, 22)
                new_level = min(100, b.fill_level + delta)
            elif mode == "random-walk":
                delta = random.randint(-10, 20)
                new_level = max(0, min(100, b.fill_level + delta))
            elif mode == "spike-hotspots":
                # Simulate city hotspots: some bins increase fast, most increase slow.
                delta = random.randint(20, 35) if random.random() < 0.15 else random.randint(0, 10)
                new_level = min(100, b.fill_level + delta)
            else:
                new_level = b.fill_level
            update_bin_fill_level(b, new_level, source="sim")

    db.session.commit()
    flash(f"Simulated {iterations} sensor tick(s) for {len(bins)} bins.", "success")
    return redirect(url_for("public.dashboard"))


# ---------------------------
# Reports & Analytics
# ---------------------------


@bp.get("/reports")
@login_required
@role_required("admin")
def reports():
    # Simple analytics computed from stored events/readings.
    from sqlalchemy import case, func

    # Daily collection count (last 7 days)
    day_col = func.date(CollectionEvent.collected_at).label("day")
    daily = (
        db.session.query(day_col, func.count(CollectionEvent.id))
        .group_by(day_col)
        .order_by(day_col.desc())
        .limit(7)
        .all()
    )

    # Most collected bins (top 10)
    top_bins = (
        db.session.query(Bin.bin_code, func.count(CollectionEvent.id).label("cnt"))
        .join(CollectionEvent, CollectionEvent.bin_id == Bin.id)
        .group_by(Bin.bin_code)
        .order_by(func.count(CollectionEvent.id).desc())
        .limit(10)
        .all()
    )

    # Areas generating most waste (by collections)
    top_areas = (
        db.session.query(Bin.area, func.count(CollectionEvent.id).label("cnt"))
        .join(CollectionEvent, CollectionEvent.bin_id == Bin.id)
        .group_by(Bin.area)
        .order_by(func.count(CollectionEvent.id).desc())
        .limit(10)
        .all()
    )

    # Route efficiency summary (last 10 routes)
    route_summary = (
        db.session.query(
            Route.route_code,
            Route.status,
            Route.total_distance_km,
            func.count(RouteStop.id).label("stops"),
            func.sum(case((RouteStop.status == "collected", 1), else_=0)).label("collected"),
        )
        .outerjoin(RouteStop, RouteStop.route_id == Route.id)
        .group_by(Route.id)
        .order_by(Route.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/reports.html",
        daily=daily,
        top_bins=top_bins,
        top_areas=top_areas,
        route_summary=route_summary,
    )


@bp.get("/analytics")
@login_required
@role_required("admin")
def analytics():
    """
    Analytics dashboard with charts (Chart.js).
    Uses simple aggregations that are explainable for an academic project.
    """

    from datetime import date, timedelta

    from sqlalchemy import func

    # KPI tiles
    kpis = {
        "total_bins": Bin.query.count(),
        "active_alerts": Alert.query.filter_by(is_active=True).count(),
        "routes_total": Route.query.count(),
        "collections_total": CollectionEvent.query.count(),
    }

    # Bins by waste type
    bins_by_waste = (
        db.session.query(Bin.waste_type, func.count(Bin.id).label("cnt"))
        .group_by(Bin.waste_type)
        .order_by(func.count(Bin.id).desc())
        .all()
    )

    # Bins by area
    bins_by_area = (
        db.session.query(Bin.area, func.count(Bin.id).label("cnt"))
        .group_by(Bin.area)
        .order_by(func.count(Bin.id).desc())
        .all()
    )

    # Alerts per day (last 14 days)
    end_day = date.today()
    start_day = end_day - timedelta(days=13)
    alert_day_col = func.date(Alert.created_at).label("day")
    alerts_daily = (
        db.session.query(alert_day_col, func.count(Alert.id).label("cnt"))
        .filter(alert_day_col >= start_day)
        .filter(alert_day_col <= end_day)
        .group_by(alert_day_col)
        .order_by(alert_day_col.asc())
        .all()
    )

    # Route efficiency (last 12 routes): distance vs stops
    routes_eff = (
        db.session.query(
            Route.route_code,
            Route.total_distance_km,
            func.count(RouteStop.id).label("stops"),
        )
        .outerjoin(RouteStop, RouteStop.route_id == Route.id)
        .group_by(Route.id)
        .order_by(Route.created_at.desc())
        .limit(12)
        .all()
    )

    data = {
        "bins_by_waste": [{"label": wt or "Unknown", "value": int(cnt)} for wt, cnt in bins_by_waste],
        "bins_by_area": [{"label": area or "Unknown", "value": int(cnt)} for area, cnt in bins_by_area],
        "alerts_daily": [{"day": str(d), "count": int(c)} for d, c in alerts_daily],
        "routes_eff": [
            {"route": code, "km": float(km or 0.0), "stops": int(stops or 0)}
            for code, km, stops in routes_eff
        ],
    }

    return render_template("admin/analytics.html", kpis=kpis, data=data, start_day=start_day, end_day=end_day)


@bp.get("/reports/saved")
@login_required
@role_required("admin")
def saved_reports():
    items = GeneratedReport.query.order_by(GeneratedReport.created_at.desc()).limit(30).all()
    return render_template("admin/reports_saved.html", items=items)


def _build_report_snapshot(period_start: date, period_end: date) -> dict:
    from sqlalchemy import func

    totals = {
        "total_bins": Bin.query.count(),
        "active_alerts": Alert.query.filter_by(is_active=True).count(),
        "full_bins": Bin.query.filter_by(status="Full").count(),
        "overflow_bins": Bin.query.filter_by(status="Overflow").count(),
    }

    col_day = func.date(CollectionEvent.collected_at).label("day")
    collections = (
        db.session.query(col_day, func.count(CollectionEvent.id).label("cnt"))
        .filter(col_day >= period_start)
        .filter(col_day <= period_end)
        .group_by(col_day)
        .order_by(col_day.asc())
        .all()
    )

    top_bins = (
        db.session.query(Bin.bin_code, func.count(CollectionEvent.id).label("cnt"))
        .join(CollectionEvent, CollectionEvent.bin_id == Bin.id)
        .filter(func.date(CollectionEvent.collected_at) >= period_start)
        .filter(func.date(CollectionEvent.collected_at) <= period_end)
        .group_by(Bin.bin_code)
        .order_by(func.count(CollectionEvent.id).desc())
        .limit(10)
        .all()
    )

    top_areas = (
        db.session.query(Bin.area, func.count(CollectionEvent.id).label("cnt"))
        .join(CollectionEvent, CollectionEvent.bin_id == Bin.id)
        .filter(func.date(CollectionEvent.collected_at) >= period_start)
        .filter(func.date(CollectionEvent.collected_at) <= period_end)
        .group_by(Bin.area)
        .order_by(func.count(CollectionEvent.id).desc())
        .limit(10)
        .all()
    )

    return {
        "period_start": str(period_start),
        "period_end": str(period_end),
        "totals": totals,
        "collections_by_day": [{"day": str(d), "count": int(c)} for d, c in collections],
        "top_bins": [{"bin_code": code, "count": int(cnt)} for code, cnt in top_bins],
        "top_areas": [{"area": area or "Unknown", "count": int(cnt)} for area, cnt in top_areas],
    }


@bp.post("/reports/saved/generate")
@login_required
@role_required("admin")
def saved_reports_generate():
    report_type = (request.form.get("report_type") or "weekly").strip()
    today = date.today()
    if report_type == "daily":
        period_start = today
        period_end = today
        title = f"Daily Waste Report ({today})"
    else:
        period_end = today
        period_start = date.fromordinal(today.toordinal() - 6)
        title = f"Weekly Waste Report ({period_start} to {period_end})"
        report_type = "weekly"

    snapshot = _build_report_snapshot(period_start, period_end)
    item = GeneratedReport(
        title=title,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        content_json=json.dumps(snapshot, indent=2),
        created_by_id=current_user.id,
    )
    db.session.add(item)
    db.session.commit()
    flash("Report generated and saved.", "success")
    return redirect(url_for("admin.saved_reports"))


@bp.get("/reports/saved/<int:report_id>")
@login_required
@role_required("admin")
def saved_report_detail(report_id: int):
    item = db.session.get(GeneratedReport, report_id)
    if not item:
        flash("Report not found.", "danger")
        return redirect(url_for("admin.saved_reports"))
    payload = json.loads(item.content_json)
    return render_template("admin/report_detail.html", item=item, payload=payload)


@bp.get("/reports/saved/<int:report_id>/delete")
@login_required
@role_required("admin")
def saved_report_delete(report_id: int):
    item = db.session.get(GeneratedReport, report_id)
    if not item:
        flash("Report not found.", "danger")
        return redirect(url_for("admin.saved_reports"))
    db.session.delete(item)
    db.session.commit()
    flash("Report deleted.", "info")
    return redirect(url_for("admin.saved_reports"))
