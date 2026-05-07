from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # admin|worker|user (legacy: collector|public)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    trucks = db.relationship("Truck", back_populates="driver", lazy="dynamic")
    created_routes = db.relationship("Route", foreign_keys="Route.created_by_id", lazy="dynamic")

    @property
    def is_admin(self) -> bool:
        return self.canonical_role == "admin"

    @property
    def is_worker(self) -> bool:
        return self.canonical_role == "worker"

    @property
    def is_user(self) -> bool:
        return self.canonical_role == "user"

    # Backwards-compatible alias used throughout the prototype
    @property
    def is_collector(self) -> bool:
        return self.is_worker

    @property
    def canonical_role(self) -> str:
        """
        Normalize legacy role names to the new signup roles.
        - collector -> worker
        - public -> user
        """

        if self.role == "collector":
            return "worker"
        if self.role == "public":
            return "user"
        return self.role

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


class Truck(db.Model):
    __tablename__ = "trucks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    plate_no = db.Column(db.String(30), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")  # active|inactive
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)

    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    driver = db.relationship("User", back_populates="trucks")

    routes = db.relationship("Route", back_populates="truck", lazy="dynamic")


class Bin(db.Model):
    __tablename__ = "bins"

    id = db.Column(db.Integer, primary_key=True)
    bin_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    location_name = db.Column(db.String(140), nullable=False)
    area = db.Column(db.String(80), nullable=True, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    waste_type = db.Column(db.String(30), nullable=False, default="General")
    fill_level = db.Column(db.Integer, nullable=False, default=0)  # 0..100
    status = db.Column(db.String(20), nullable=False, default="Empty")  # Empty|Moderate|Full|Overflow
    last_updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    readings = db.relationship("SensorReading", back_populates="bin", lazy="dynamic", cascade="all, delete-orphan")
    alerts = db.relationship("Alert", back_populates="bin", lazy="dynamic", cascade="all, delete-orphan")


class SensorReading(db.Model):
    __tablename__ = "sensor_readings"

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False, index=True)
    fill_level = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(20), nullable=False, default="sim")  # sim|manual|api
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    bin = db.relationship("Bin", back_populates="readings")


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False, index=True)
    level = db.Column(db.String(20), nullable=False)  # Full|Overflow
    message = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    bin = db.relationship("Bin", back_populates="alerts")


class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(db.Integer, primary_key=True)
    route_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    date_for = db.Column(db.Date, nullable=False)

    algorithm = db.Column(db.String(50), nullable=False, default="Greedy Nearest-Neighbor (Urgency Weighted)")
    status = db.Column(db.String(20), nullable=False, default="planned")  # planned|in_progress|completed
    total_distance_km = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    truck_id = db.Column(db.Integer, db.ForeignKey("trucks.id"), nullable=True)
    truck = db.relationship("Truck", back_populates="routes")

    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    driver = db.relationship("User", foreign_keys=[driver_id])

    stops = db.relationship("RouteStop", back_populates="route", order_by="RouteStop.seq", cascade="all, delete-orphan")


class RouteStop(db.Model):
    __tablename__ = "route_stops"

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False, index=True)
    seq = db.Column(db.Integer, nullable=False)

    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False)
    bin = db.relationship("Bin")

    distance_from_prev_km = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|collected|skipped
    collected_at = db.Column(db.DateTime(timezone=True), nullable=True)

    route = db.relationship("Route", back_populates="stops")


class CollectionEvent(db.Model):
    __tablename__ = "collection_events"

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False, index=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=True, index=True)
    collector_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    before_fill_level = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    collected_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    bin = db.relationship("Bin")
    route = db.relationship("Route")
    collector = db.relationship("User")


class NotificationLog(db.Model):
    __tablename__ = "notification_logs"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=True, index=True)
    channel = db.Column(db.String(20), nullable=False)  # sms|email|system
    recipient = db.Column(db.String(120), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    alert = db.relationship("Alert")


class GeneratedReport(db.Model):
    __tablename__ = "generated_reports"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    report_type = db.Column(db.String(30), nullable=False)  # daily|weekly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    content_json = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_by = db.relationship("User", foreign_keys=[created_by_id])


class BinReport(db.Model):
    """
    Public user reports (community feedback). Admin can review and act.
    """

    __tablename__ = "bin_reports"

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    reported_level = db.Column(db.Integer, nullable=True)  # optional: user's estimate 0..100
    message = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")  # open|reviewed|dismissed

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    bin = db.relationship("Bin")
    reporter = db.relationship("User")


class Collection(db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    waste_type = db.Column(db.String(30), nullable=False, default="General")
    estimated_weight = db.Column(db.Float, nullable=True)
    actual_weight = db.Column(db.Float, nullable=True)
    pickup_address = db.Column(db.String(255), nullable=True)
    preferred_date = db.Column(db.Date, nullable=True)
    preferred_time = db.Column(db.String(20), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|assigned|in_progress|completed|cancelled
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    bin = db.relationship("Bin")
    user = db.relationship("User", foreign_keys=[user_id])
    driver = db.relationship("User", foreign_keys=[driver_id])


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), nullable=False, default="card")  # card|paypal|mobile|bank
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|completed|failed
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    user = db.relationship("User")
