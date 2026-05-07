from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user


_ROLE_ALIASES: dict[str, str] = {
    "admin": "admin",
    "worker": "worker",
    "user": "user",
    # legacy names used in earlier prototype versions
    "collector": "worker",
    "public": "user",
}


def _canonical_role(role: str) -> str:
    return _ROLE_ALIASES.get((role or "").strip(), (role or "").strip())


def role_required(*roles: str):
    """
    Authorization helper for views.
    Example: @role_required("admin")
    """

    def decorator(view_fn):
        @wraps(view_fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            allowed = {_canonical_role(r) for r in roles}
            if _canonical_role(getattr(current_user, "role", "")) not in allowed:
                abort(403)
            return view_fn(*args, **kwargs)

        return wrapped

    return decorator
