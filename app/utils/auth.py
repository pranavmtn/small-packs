"""Authentication helpers and route protection."""

from functools import wraps

from flask import current_app, flash, redirect, session, url_for


def login_user(username: str) -> None:
    session.clear()
    session["user"] = username
    session.permanent = True


def logout_user() -> None:
    session.clear()


def is_authenticated() -> bool:
    return bool(session.get("user"))


def verify_credentials(username: str, password: str) -> bool:
    """Validate against temporary credentials in config."""
    expected_user = current_app.config["TEMP_USERNAME"]
    expected_pass = current_app.config["TEMP_PASSWORD"]
    return username == expected_user and password == expected_pass


def login_required(view):
    """Protect routes until Supabase Auth replaces session login."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped
