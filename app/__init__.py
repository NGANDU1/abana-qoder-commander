"""
Smart Waste Management System (Flask)

Factory pattern keeps the project modular and scalable for an academic prototype.
"""

from pathlib import Path

from flask import Flask, render_template

from .config import AppConfig
from .extensions import db, login_manager


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(AppConfig())

    # Frontend integration:
    # Serve templates/assets from ../smart-waste-system/ (new UI folder).
    frontend_dir = Path(app.root_path).resolve().parent / "smart-waste-system"
    if frontend_dir.exists():
        from jinja2 import ChoiceLoader, FileSystemLoader
        from flask import Blueprint

        # Load templates from smart-waste-system/ (fallback to app/templates)
        app.jinja_loader = ChoiceLoader([FileSystemLoader(str(frontend_dir)), app.jinja_loader])

        # Serve static assets (css/js/images) from smart-waste-system/
        assets_bp = Blueprint(
            "frontend_assets",
            __name__,
            static_folder=str(frontend_dir),
            static_url_path="/smart-waste-system",
        )
        app.register_blueprint(assets_bp)
    else:
        print(f"WARNING: Frontend directory not found: {frontend_dir}")

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Blueprints
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.admin.routes import bp as admin_bp
    from .blueprints.collector.routes import bp as collector_bp
    from .blueprints.public.routes import bp as public_bp
    from .blueprints.user.routes import bp as user_bp
    from .blueprints.api.routes import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(collector_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp)

    # Error pages
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    # Ensure DB exists (for a prototype). In production, use migrations.
    with app.app_context():
        from . import models  # noqa: F401

        db.create_all()

    return app
