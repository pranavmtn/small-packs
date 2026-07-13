"""Shared route guards and helpers."""

from functools import wraps

from flask import current_app, flash, render_template
from sqlalchemy.exc import OperationalError, SQLAlchemyError


def database_required(view):
    """Block DB-backed pages until SUPABASE_DB_URL is set."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_app.config.get("DATABASE_CONFIGURED"):
            return render_template("errors/setup.html"), 503
        try:
            return view(*args, **kwargs)
        except OperationalError:
            current_app.logger.exception("Database connection failed")
            return (
                render_template(
                    "errors/setup.html",
                    connection_failed=True,
                ),
                503,
            )
        except SQLAlchemyError as exc:
            current_app.logger.exception("Database error")
            flash(
                "A database error occurred. Check the server log for details.",
                "danger",
            )
            return (
                render_template(
                    "errors/setup.html",
                    connection_failed=True,
                    error_detail=str(exc.orig) if getattr(exc, "orig", None) else str(exc),
                ),
                500,
            )

    return wrapped
