"""
Lightweight, idempotent DB migration for the academic prototype.

Adds profile columns to `users` and normalizes legacy roles:
  - public -> user
  - collector -> worker

Usage:
  python scripts/migrate_users_roles_and_profile_fields.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import inspect, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db


def _has_index(table: str, index_name: str) -> bool:
    insp = inspect(db.engine)
    for idx in insp.get_indexes(table):
        if (idx.get("name") or "").lower() == index_name.lower():
            return True
    return False


def _has_unique(table: str, constraint_name: str) -> bool:
    insp = inspect(db.engine)
    for uc in insp.get_unique_constraints(table):
        if (uc.get("name") or "").lower() == constraint_name.lower():
            return True
    return False


def main() -> None:
    app = create_app()
    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name

        insp = inspect(engine)
        if "users" not in insp.get_table_names():
            print("No `users` table found. Nothing to migrate.")
            return

        existing_cols = {c["name"] for c in insp.get_columns("users")}

        # Add columns (safe for SQLite and MySQL)
        add_cols: list[str] = []
        if "first_name" not in existing_cols:
            add_cols.append("ADD COLUMN first_name VARCHAR(80) NULL")
        if "last_name" not in existing_cols:
            add_cols.append("ADD COLUMN last_name VARCHAR(80) NULL")
        if "phone_number" not in existing_cols:
            add_cols.append("ADD COLUMN phone_number VARCHAR(30) NULL")
        if "employee_id" not in existing_cols:
            add_cols.append("ADD COLUMN employee_id VARCHAR(50) NULL")

        if add_cols:
            stmt = "ALTER TABLE users " + ", ".join(add_cols)
            db.session.execute(text(stmt))
            db.session.commit()
            print("Added columns:", ", ".join([c.split()[2] for c in add_cols]))
        else:
            print("User profile columns already present.")

        # Add index/unique for employee_id where supported
        # SQLite supports UNIQUE constraints only at table creation, so we skip there.
        if dialect != "sqlite":
            if "employee_id" in {c["name"] for c in inspect(engine).get_columns("users")}:
                if not _has_unique("users", "uq_users_employee_id"):
                    try:
                        db.session.execute(text("ALTER TABLE users ADD CONSTRAINT uq_users_employee_id UNIQUE (employee_id)"))
                        db.session.commit()
                        print("Added UNIQUE constraint: uq_users_employee_id")
                    except Exception:
                        db.session.rollback()
                if not _has_index("users", "idx_users_employee_id"):
                    try:
                        db.session.execute(text("CREATE INDEX idx_users_employee_id ON users (employee_id)"))
                        db.session.commit()
                        print("Added index: idx_users_employee_id")
                    except Exception:
                        db.session.rollback()

        # Normalize roles (idempotent)
        db.session.execute(text("UPDATE users SET role='worker' WHERE role='collector'"))
        db.session.execute(text("UPDATE users SET role='user' WHERE role='public'"))
        db.session.commit()
        print("Normalized roles: collector->worker, public->user")


if __name__ == "__main__":
    main()
