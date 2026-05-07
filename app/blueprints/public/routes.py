from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Alert, Bin, BinReport, SensorReading, Truck
from ...utils.bin_logic import update_bin_fill_level
from ...utils.security import role_required

bp = Blueprint("public", __name__)


@bp.get("/")
def landing():
    return render_template("landing.html")


@bp.get("/features")
def features_page():
    # Waste guide/tips pages are not used in the dashboard flow.
    return redirect(url_for("public.landing"))


@bp.get("/contact")
def contact_page():
    return render_template("contact.html")


@bp.get("/dashboard")
@login_required
def dashboard():
    # Role-aware dashboards
    if current_user.is_admin:
        return redirect(url_for("admin.admin_home"))
    if current_user.is_worker:
        return redirect(url_for("collector.my_route"))
    if current_user.is_user:
        return redirect(url_for("user.home"))

    total_bins = Bin.query.count()
    empty_bins = Bin.query.filter_by(status="Empty").count()
    moderate_bins = Bin.query.filter_by(status="Moderate").count()
    full_bins = Bin.query.filter_by(status="Full").count()
    overflow_bins = Bin.query.filter_by(status="Overflow").count()

    active_collectors = (
        Truck.query.filter_by(status="active")
        .filter(Truck.driver_id.isnot(None))
        .count()
    )

    urgent_alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).limit(8).all()

    return render_template(
        "dashboard.html",
        stats={
            "total_bins": total_bins,
            "empty_bins": empty_bins,
            "moderate_bins": moderate_bins,
            "full_bins": full_bins,
            "overflow_bins": overflow_bins,
            "active_collectors": active_collectors,
        },
        urgent_alerts=urgent_alerts,
    )


@bp.get("/bins")
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

    # Keep internal templates under app/templates (avoid old frontend/bins.html)
    if current_user.is_authenticated and current_user.is_user:
        return redirect(url_for("user.bins", q=q, status=status, waste_type=waste_type, area=area))

    return render_template(
        "bins.html",
        bins=bins_list,
        filters={"q": q, "status": status, "waste_type": waste_type, "area": area},
        areas=areas,
        waste_types=waste_types,
    )


@bp.get("/bins/<int:bin_id>")
@login_required
def bin_detail(bin_id: int):
    b = Bin.query.get(bin_id)
    if not b:
        return render_template("errors/404.html"), 404

    readings = b.readings.order_by(SensorReading.recorded_at.desc()).limit(30).all()
    readings = list(reversed(readings))
    history = [{"t": r.recorded_at.strftime("%m-%d %H:%M"), "fill": r.fill_level} for r in readings]

    active_alerts = b.alerts.filter_by(is_active=True).order_by(Alert.created_at.desc()).all()
    recent_alerts = b.alerts.order_by(Alert.created_at.desc()).limit(10).all()

    tpl = "user/bin_detail.html" if (current_user.is_authenticated and current_user.is_user) else "bin_detail.html"
    return render_template(tpl, b=b, history=history, active_alerts=active_alerts, recent_alerts=recent_alerts)


@bp.get("/bins/<int:bin_id>/report")
@login_required
@role_required("user")
def report_bin_get(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))

    tpl = "user/report_bin.html" if current_user.is_user else "report_bin.html"
    return render_template(tpl, b=b)


@bp.post("/bins/<int:bin_id>/report")
@login_required
@role_required("user")
def report_bin_post(bin_id: int):
    b = db.session.get(Bin, bin_id)
    if not b:
        flash("Bin not found.", "danger")
        return redirect(url_for("public.bins"))

    reported_level_raw = (request.form.get("reported_level") or "").strip()
    message = (request.form.get("message") or "").strip() or None
    reported_level = None
    if reported_level_raw:
        try:
            reported_level = max(0, min(100, int(reported_level_raw)))
        except ValueError:
            flash("Reported level must be a number 0..100.", "danger")
            return redirect(url_for("public.report_bin_get", bin_id=b.id))

    r = BinReport(
        bin_id=b.id,
        reporter_id=current_user.id,
        reported_level=reported_level,
        message=message,
        status="open",
    )
    db.session.add(r)

    # If user provided a level estimate, reflect it immediately in the bin status
    # so severity colors/priority show up for admin + drivers.
    if reported_level is not None:
        update_bin_fill_level(b, reported_level, source="manual")
    db.session.commit()
    flash("Report submitted. Thank you for helping keep the city clean.", "success")
    return redirect(url_for("public.bin_detail", bin_id=b.id))


@bp.get("/map")
@login_required
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
    # Keep internal templates under app/templates (avoid old frontend/map.html)
    if current_user.is_authenticated and current_user.is_user:
        return redirect(url_for("user.map_view"))
    return render_template("map.html", depot=depot, bins=bins_data)
