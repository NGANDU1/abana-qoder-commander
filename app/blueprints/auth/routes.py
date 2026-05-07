from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ...extensions import db
from ...models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.dashboard"))
    return render_template("login.html")


@bp.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.is_active or not user.check_password(password):
        flash("Invalid username or password.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user)
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Welcome back.", "success")
    return redirect(url_for("public.dashboard"))


@bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.dashboard"))
    return render_template("register.html")


def _register_common(role: str | None = None):
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip() or None
    first_name = (request.form.get("first_name") or "").strip() or None
    last_name = (request.form.get("last_name") or "").strip() or None
    phone_number = (request.form.get("phone_number") or "").strip() or None
    employee_id = (request.form.get("employee_id") or "").strip() or None

    selected_role = (role or request.form.get("role") or "user").strip()
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""
    admin_code = (request.form.get("admin_code") or "").strip()

    if not username or not password:
        flash("Username and password are required.", "danger")
        return redirect(url_for("auth.register"))
    if password != password2:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("auth.register"))
    if not first_name or not last_name:
        flash("First name and surname are required.", "danger")
        return redirect(url_for("auth.register"))
    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for("auth.register"))
    if not phone_number:
        flash("Phone number is required.", "danger")
        return redirect(url_for("auth.register"))
    if selected_role not in ("admin", "worker", "user"):
        flash("Invalid role selection.", "danger")
        return redirect(url_for("auth.register"))
    if selected_role in ("worker", "admin") and not employee_id:
        flash("Employee ID is required for worker/admin accounts.", "danger")
        return redirect(url_for("auth.register"))
    if selected_role == "admin":
        expected = current_app.config.get("ADMIN_SIGNUP_CODE")
        if not expected:
            flash("Admin signup is disabled. Ask an admin to create your account.", "danger")
            return redirect(url_for("auth.register"))
        if admin_code != expected:
            flash("Invalid admin signup code.", "danger")
            return redirect(url_for("auth.register"))
    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "danger")
        return redirect(url_for("auth.register"))
    if email and User.query.filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("auth.register"))
    if employee_id and User.query.filter_by(employee_id=employee_id).first():
        flash("Employee ID already exists.", "danger")
        return redirect(url_for("auth.register"))

    u = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        employee_id=employee_id,
        role=selected_role,
        is_active=True,
    )
    u.set_password(password)
    db.session.add(u)
    db.session.commit()

    login_user(u)
    flash("Account created.", "success")
    return redirect(url_for("public.dashboard"))


@bp.post("/register")
def register_post():
    return _register_common()


@bp.post("/register/public")
def register_public_post():
    # Backwards-compatible endpoint
    return _register_common("user")


@bp.post("/register/worker")
def register_worker_post():
    # Backwards-compatible endpoint
    return _register_common("worker")


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("public.landing"))
