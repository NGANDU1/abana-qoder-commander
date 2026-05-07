from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Bin, BinReport, CollectionEvent, NotificationLog, Route, RouteStop, User
from ...utils.bin_logic import update_bin_fill_level
from ...utils.security import role_required

bp = Blueprint("collector", __name__, url_prefix="/collector")


@bp.get("/my-route")
@login_required
@role_required("worker")
def my_route():
    r = (
        Route.query.filter_by(driver_id=current_user.id)
        .filter(Route.status.in_(["planned", "in_progress"]))
        .order_by(Route.created_at.desc())
        .first()
    )
    if not r:
        return render_template("collector/no_route.html")
    stops = RouteStop.query.filter_by(route_id=r.id).order_by(RouteStop.seq.asc()).all()

    total_stops = len(stops)
    collected_count = sum(1 for s in stops if s.status == "collected")
    pending_count = sum(1 for s in stops if s.status == "pending")
    progress_pct = int(round((collected_count / total_stops) * 100)) if total_stops else 0
    next_stop = next((s for s in stops if s.status == "pending"), None)

    stops_points = [
        {
            "seq": s.seq,
            "bin_code": s.bin.bin_code,
            "lat": s.bin.latitude,
            "lon": s.bin.longitude,
            "status": s.status,
            "fill_level": s.bin.fill_level,
            "bin_status": s.bin.status,
        }
        for s in stops
    ]
    return render_template(
        "collector/my_route.html",
        r=r,
        stops=stops,
        stops_points=stops_points,
        summary={
            "total_stops": total_stops,
            "collected": collected_count,
            "pending": pending_count,
            "progress_pct": progress_pct,
        },
        next_stop=next_stop,
    )


@bp.get("/stops/<int:stop_id>/collect")
@login_required
@role_required("worker")
def collect_stop(stop_id: int):
    stop = db.session.get(RouteStop, stop_id)
    if not stop or not stop.route:
        flash("Stop not found.", "danger")
        return redirect(url_for("collector.my_route"))
    if stop.route.driver_id != current_user.id:
        flash("This stop is not assigned to you.", "danger")
        return redirect(url_for("collector.my_route"))

    if stop.status == "collected":
        flash("Stop already collected.", "info")
        return redirect(url_for("collector.my_route"))

    b = db.session.get(Bin, stop.bin_id)
    before = b.fill_level

    stop.status = "collected"
    stop.collected_at = datetime.now(timezone.utc)
    now = stop.collected_at

    # When collected, bin is emptied.
    update_bin_fill_level(b, 0, source="manual")
    db.session.add(
        CollectionEvent(
            bin_id=b.id,
            route_id=stop.route_id,
            collector_id=current_user.id,
            before_fill_level=before,
            notes="Emptied during collection.",
        )
    )

    # Notify users who reported this bin.
    reporter_rows = (
        BinReport.query.filter_by(bin_id=b.id)
        .filter(BinReport.reporter_id.isnot(None))
        .with_entities(BinReport.reporter_id)
        .distinct()
        .all()
    )
    reporter_ids = [r[0] for r in reporter_rows if r and r[0]]
    if reporter_ids:
        reporters = User.query.filter(User.id.in_(reporter_ids)).all()

        # Mark open reports for this bin as completed.
        BinReport.query.filter_by(bin_id=b.id, status="open").update(
            {"status": "completed", "reviewed_at": now},
            synchronize_session=False,
        )

        for u in reporters:
            db.session.add(
                NotificationLog(
                    alert_id=None,
                    channel="system",
                    recipient=u.username,
                    message=f"Completed: Your request for bin {b.bin_code} has been collected.",
                )
            )

    # If all stops done -> complete route.
    remaining = RouteStop.query.filter_by(route_id=stop.route_id, status="pending").count()
    if remaining == 0:
        stop.route.status = "completed"

    db.session.commit()
    flash(f"Collected {b.bin_code}.", "success")
    return redirect(url_for("collector.my_route"))
