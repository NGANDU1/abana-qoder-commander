from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, render_template, request
from flask_login import current_user, login_required

from ...models import Alert, Bin, BinReport, NotificationLog, Truck
from ...utils.security import role_required

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.get("/")
@login_required
@role_required("user")
def home():
    today = date.today()

    total_reports = BinReport.query.filter_by(reporter_id=current_user.id).count()
    open_reports = BinReport.query.filter_by(reporter_id=current_user.id, status="open").count()
    reviewed_reports = BinReport.query.filter_by(reporter_id=current_user.id, status="reviewed").count()

    recent_reports = (
        BinReport.query.filter_by(reporter_id=current_user.id)
        .order_by(BinReport.created_at.desc())
        .limit(6)
        .all()
    )

    active_alerts = Alert.query.filter_by(is_active=True).count()

    # Simple prototype reward points: 10 per report.
    reward_points = total_reports * 10

    return render_template(
        "user/home.html",
        today_str=today.strftime("%b %d, %Y"),
        stats={
            "total_reports": total_reports,
            "open_reports": open_reports,
            "reviewed_reports": reviewed_reports,
            "active_alerts": active_alerts,
            "reward_points": reward_points,
        },
        recent_reports=recent_reports,
    )


@bp.get("/bins")
@login_required
@role_required("user")
def bins():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    waste_type = (request.args.get("waste_type") or "").strip()
    area = (request.args.get("area") or "").strip()

    query = Bin.query
    if q:
        like = f"%{q}%"
        query = query.filter((Bin.bin_code.ilike(like)) | (Bin.location_name.ilike(like)))
    if status:
        query = query.filter(Bin.status == status)
    if waste_type:
        query = query.filter(Bin.waste_type == waste_type)
    if area:
        query = query.filter(Bin.area == area)

    bins_list = query.order_by(Bin.status.desc(), Bin.fill_level.desc()).all()
    areas = [r[0] for r in Bin.query.with_entities(Bin.area).distinct().order_by(Bin.area).all() if r[0]]
    waste_types = [r[0] for r in Bin.query.with_entities(Bin.waste_type).distinct().order_by(Bin.waste_type).all() if r[0]]

    return render_template(
        "user/bins.html",
        bins=bins_list,
        filters={"q": q, "status": status, "waste_type": waste_type, "area": area},
        areas=areas,
        waste_types=waste_types,
    )


@bp.get("/map")
@login_required
@role_required("user")
def map_view():
    depot = {"lat": current_app.config["DEPOT_LAT"], "lon": current_app.config["DEPOT_LON"]}
    bins_list = Bin.query.order_by(Bin.fill_level.desc()).all()
    bins_data = [
        {
            "id": b.id,
            "bin_code": b.bin_code,
            "location_name": b.location_name,
            "area": b.area,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "waste_type": b.waste_type,
            "fill_level": b.fill_level,
            "status": b.status,
        }
        for b in bins_list
    ]

    active_collectors = (
        Truck.query.filter_by(status="active")
        .filter(Truck.driver_id.isnot(None))
        .count()
    )

    return render_template(
        "user/map.html",
        depot=depot,
        bins=bins_data,
        active_collectors=active_collectors,
    )


@bp.get("/notifications")
@login_required
@role_required("user")
def notifications():
    recipients = {current_user.username}
    if current_user.email:
        recipients.add(current_user.email)

    logs = (
        NotificationLog.query.filter(NotificationLog.alert_id.is_(None))
        .filter(NotificationLog.recipient.in_(sorted(recipients)))
        .filter(NotificationLog.message.ilike("%has been collected%"))
        .order_by(NotificationLog.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template("user/notifications.html", logs=logs)
