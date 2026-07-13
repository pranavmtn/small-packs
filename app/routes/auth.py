"""Authentication routes — temporary session login."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.utils.auth import is_authenticated, login_user, logout_user, verify_credentials

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if verify_credentials(username, password):
            login_user(username)
            flash("Welcome back.", "success")
            next_url = request.args.get("next") or url_for("dashboard.index")
            return redirect(next_url)

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
