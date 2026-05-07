from __future__ import annotations

from datetime import datetime, timezone

from ..extensions import db
from ..models import Alert, Bin, NotificationLog, SensorReading, User


def status_from_fill_level(fill_level: int) -> str:
    """
    Thresholds (simple & explainable for academic demo):
    - 0..24   => Empty
    - 25..69  => Moderate
    - 70..89  => Full
    - 90..100 => Overflow
    """

    level = max(0, min(100, int(fill_level)))
    if level < 25:
        return "Empty"
    if level < 70:
        return "Moderate"
    if level < 90:
        return "Full"
    return "Overflow"


def _active_alert_for(bin_id: int, level: str) -> Alert | None:
    return Alert.query.filter_by(bin_id=bin_id, level=level, is_active=True).order_by(Alert.created_at.desc()).first()


def update_bin_fill_level(bin_obj: Bin, fill_level: int, source: str = "manual") -> None:
    """
    Single place to apply updates so status, readings, and alerts stay consistent.
    """

    fill_level = max(0, min(100, int(fill_level)))
    new_status = status_from_fill_level(fill_level)

    bin_obj.fill_level = fill_level
    bin_obj.status = new_status
    bin_obj.last_updated_at = datetime.now(timezone.utc)

    db.session.add(
        SensorReading(
            bin_id=bin_obj.id,
            fill_level=fill_level,
            status=new_status,
            source=source,
        )
    )

    # Alerts: create/keep active for Full & Overflow, otherwise resolve.
    if new_status in ("Full", "Overflow"):
        level = new_status
        if not _active_alert_for(bin_obj.id, level):
            msg = f"Bin {bin_obj.bin_code} is {new_status} ({fill_level}%). Urgent pickup required."
            alert = Alert(bin_id=bin_obj.id, level=level, message=msg, is_active=True)
            db.session.add(alert)
            db.session.flush()  # ensure alert.id exists for notification logs

            admin_email = (
                User.query.filter_by(role="admin", is_active=True)
                .with_entities(User.email)
                .order_by(User.id.asc())
                .first()
            )
            db.session.add(
                NotificationLog(
                    alert_id=alert.id,
                    channel="system",
                    recipient=None,
                    message=msg,
                )
            )
            db.session.add(
                NotificationLog(
                    alert_id=alert.id,
                    channel="email",
                    recipient=admin_email[0] if admin_email and admin_email[0] else "admin@city.gov",
                    message=msg,
                )
            )
            db.session.add(
                NotificationLog(
                    alert_id=alert.id,
                    channel="sms",
                    recipient="+0000000000",
                    message=msg,
                )
            )
    else:
        # Resolve any active alerts for this bin.
        active_alerts = Alert.query.filter_by(bin_id=bin_obj.id, is_active=True).all()
        now = datetime.now(timezone.utc)
        for a in active_alerts:
            a.is_active = False
            a.resolved_at = now

