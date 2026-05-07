from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from ...extensions import db
from ...models import Bin, BinReport, Collection, Alert, Payment, User
from ...utils.security import role_required

bp = Blueprint("api", __name__, url_prefix="/api")


# Bin endpoints
@bp.get("/bins")
def get_bins():
    """Get all bins with optional filters"""
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    waste_type = (request.args.get("waste_type") or "").strip()
    
    query = Bin.query
    if q:
        like = f"%{q}%"
        query = query.filter((Bin.bin_code.ilike(like)) | (Bin.location_name.ilike(like)))
    if status:
        query = query.filter(Bin.status == status)
    if waste_type:
        query = query.filter(Bin.waste_type == waste_type)
    
    bins = query.order_by(Bin.fill_level.desc()).all()
    return jsonify([
        {
            "id": b.id,
            "bin_code": b.bin_code,
            "location_name": b.location_name,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "waste_type": b.waste_type,
            "fill_level": b.fill_level,
            "status": b.status,
            "battery_level": b.battery_level,
            "weight": b.current_weight,
            "max_weight": b.max_weight,
        }
        for b in bins
    ])


@bp.get("/bins/<int:bin_id>")
def get_bin(bin_id: int):
    """Get single bin details"""
    b = db.session.get(Bin, bin_id)
    if not b:
        return jsonify({"ok": False, "error": "Bin not found"}), 404
    
    readings = b.readings.order_by(SensorReading.recorded_at.desc()).limit(30).all()
    readings = list(reversed(readings))
    
    return jsonify({
        "id": b.id,
        "bin_code": b.bin_code,
        "location_name": b.location_name,
        "area": b.area,
        "latitude": b.latitude,
        "longitude": b.longitude,
        "waste_type": b.waste_type,
        "fill_level": b.fill_level,
        "status": b.status,
        "battery_level": b.battery_level,
        "weight": b.current_weight,
        "max_weight": b.max_weight,
        "history": [{"t": r.recorded_at.strftime("%m-%d %H:%M"), "fill": r.fill_level} for r in readings]
    })


# Pickup requests
@bp.post("/pickups")
@login_required
@role_required("user")
def create_pickup():
    """Citizen creates a pickup request"""
    data = request.get_json(silent=True) or {}
    
    bin_id = data.get("bin_id")
    waste_type = data.get("waste_type")
    weight = data.get("weight")
    address = data.get("address")
    preferred_date = data.get("preferred_date")
    preferred_time = data.get("preferred_time")
    
    if not all([bin_id, waste_type, weight, address]):
        return jsonify({"ok": False, "error": "Missing required fields"}), 400
    
    from ...models import Collection
    pickup = Collection(
        bin_id=bin_id,
        user_id=current_user.id,
        waste_type=waste_type,
        estimated_weight=weight,
        pickup_address=address,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        status="pending",
    )
    db.session.add(pickup)
    db.session.commit()
    
    return jsonify({"ok": True, "pickup_id": pickup.id, "message": "Pickup request submitted"})


@bp.get("/my-pickups")
@login_required
@role_required("user")
def my_pickups():
    """Get citizen's pickup history"""
    from ...models import Collection
    pickups = Collection.query.filter_by(user_id=current_user.id).order_by(Collection.created_at.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "bin_code": p.bin.bin_code if p.bin else None,
            "location": p.pickup_address,
            "waste_type": p.waste_type,
            "weight": p.actual_weight or p.estimated_weight,
            "status": p.status,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for p in pickups
    ])


# Complaints
@bp.post("/complaints")
@login_required
@role_required("user")
def create_complaint():
    """Submit a complaint/report"""
    data = request.get_json(silent=True) or {}
    
    issue_type = data.get("issue_type")
    location = data.get("location")
    description = data.get("description")
    priority = data.get("priority", "medium")
    
    if not all([issue_type, location, description]):
        return jsonify({"ok": False, "error": "Missing required fields"}), 400
    
    from ...models import BinReport
    complaint = BinReport(
        bin_id=data.get("bin_id"),
        reporter_id=current_user.id,
        reported_level=data.get("reported_level"),
        message=description,
        status="open",
    )
    db.session.add(complaint)
    db.session.commit()
    
    return jsonify({"ok": True, "complaint_id": complaint.id, "message": "Complaint submitted"})


# Driver endpoints
@bp.get("/driver/pickups")
@login_required
@role_required("driver")
def driver_pickups():
    """Get assigned pickups for driver"""
    from ...models import Collection
    pickups = Collection.query.filter_by(driver_id=current_user.id, status="assigned").all()
    return jsonify([
        {
            "id": p.id,
            "bin_code": p.bin.bin_code if p.bin else None,
            "location": p.pickup_address or (p.bin.location_name if p.bin else None),
            "latitude": p.bin.latitude if p.bin else None,
            "longitude": p.bin.longitude if p.bin else None,
            "fill_level": p.bin.fill_level if p.bin else None,
            "waste_type": p.waste_type,
            "status": p.status,
        }
        for p in pickups
    ])


@bp.post("/driver/confirm-collection/<int:pickup_id>")
@login_required
@role_required("driver")
def confirm_collection(pickup_id: int):
    """Driver confirms waste collection"""
    from ...models import Collection
    pickup = Collection.query.filter_by(id=pickup_id, driver_id=current_user.id).first()
    if not pickup:
        return jsonify({"ok": False, "error": "Pickup not found"}), 404
    
    data = request.get_json(silent=True) or {}
    pickup.actual_weight = data.get("weight")
    pickup.status = "completed"
    pickup.completed_at = datetime.now(timezone.utc)
    
    if pickup.bin:
        pickup.bin.current_weight = 0
        pickup.bin.fill_level = 0
        pickup.bin.status = "Empty"
    
    db.session.commit()
    return jsonify({"ok": True, "message": "Collection confirmed"})


# Admin endpoints
@bp.get("/admin/stats")
@login_required
@role_required("admin")
def admin_stats():
    """Get admin dashboard stats"""
    total_bins = Bin.query.count()
    operational = Bin.query.filter(Bin.status.in_(["Empty", "Moderate"])).count()
    warning = Bin.query.filter(Bin.status == "Full").count()
    critical = Bin.query.filter(Bin.status == "Overflow").count()
    offline = Bin.query.filter(Bin.battery_level < 20).count()
    
    active_drivers = User.query.filter_by(role="driver", is_active=True).count()
    total_citizens = User.query.filter_by(role="user").count()
    
    return jsonify({
        "total_bins": total_bins,
        "operational": operational,
        "warning": warning,
        "critical": critical,
        "offline": offline,
        "active_drivers": active_drivers,
        "total_citizens": total_citizens,
    })


@bp.get("/admin/fleet")
@login_required
@role_required("admin")
def admin_fleet():
    """Get fleet status"""
    trucks = Truck.query.all()
    return jsonify([
        {
            "id": t.id,
            "truck_id": t.truck_id,
            "status": t.status,
            "driver": t.driver.full_name if t.driver else None,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "fuel_level": t.fuel_level,
        }
        for t in trucks
    ])


# IoT sensor update
@bp.post("/sensor/update")
def sensor_update():
    """IoT endpoint for sensor data"""
    data = request.get_json(silent=True) or {}
    bin_code = (data.get("bin_code") or "").strip().upper()
    fill_level = data.get("fill_level")
    weight = data.get("weight")
    battery = data.get("battery_level")
    
    if not bin_code:
        return jsonify({"ok": False, "error": "bin_code required"}), 400
    
    b = Bin.query.filter_by(bin_code=bin_code).first()
    if not b:
        return jsonify({"ok": False, "error": "Bin not found"}), 404
    
    if fill_level is not None:
        from ...utils.bin_logic import update_bin_fill_level
        update_bin_fill_level(b, int(fill_level), source="sensor")
    
    if weight is not None:
        b.current_weight = weight
    
    if battery is not None:
        b.battery_level = battery
    
    db.session.commit()
    return jsonify({"ok": True, "bin_code": b.bin_code, "status": b.status})


# Payments
@bp.post("/payments")
@login_required
@role_required("user")
def create_payment():
    """Process payment"""
    data = request.get_json(silent=True) or {}
    amount = data.get("amount")
    method = data.get("method", "card")
    
    if not amount:
        return jsonify({"ok": False, "error": "Amount required"}), 400
    
    payment = Payment(
        user_id=current_user.id,
        amount=amount,
        method=method,
        status="completed",
        transaction_id=f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({"ok": True, "payment_id": payment.id, "transaction_id": payment.transaction_id})
