"""Pack CRUD routes — optimized for fast data entry."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.models import InventoryItem
from app.services.bunny import BunnyStorageError, BunnyStorageService
from app.services.pack_service import PackService
from app.utils.auth import login_required
from app.utils.guards import database_required

packs_bp = Blueprint("packs", __name__, url_prefix="/packs")


def _user_id() -> str:
    return current_app.config["DEFAULT_USER_ID"]


def _handle_photo_upload() -> str | None:
    """Upload photo to Bunny.net if present; return CDN URL or None."""
    photo = request.files.get("photo")
    if not photo or not photo.filename:
        return None

    bunny = BunnyStorageService.from_app_config()
    if not bunny.allowed_file(photo.filename):
        raise BunnyStorageError("Unsupported image type.")

    return bunny.upload_file(photo)


def _form_context(pack: InventoryItem | None = None, location_text: str = "") -> dict:
    return {
        "pack": pack,
        "location_text": location_text
        or (pack.location_display() if pack else ""),
        "statuses": InventoryItem.STATUSES,
    }


@packs_bp.route("/")
# @login_required  # Temporarily disabled for testing
@database_required
def list_packs():
    service = PackService()
    search = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "all").strip()
    packs = service.list_packs(user_id=_user_id(), search=search or None, status=status)
    return render_template(
        "packs/list.html",
        packs=packs,
        search=search,
        status=status,
        statuses=InventoryItem.STATUSES,
    )


@packs_bp.route("/add", methods=["GET", "POST"])
# @login_required  # Temporarily disabled for testing
@database_required
def add():
    service = PackService()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        location = (request.form.get("location") or "").strip()
        action = (request.form.get("action") or "save").strip()

        if not name:
            flash("Item name is required.", "danger")
            return render_template("packs/form.html", mode="add", **_form_context())

        if not location:
            flash("Location is required.", "danger")
            return render_template(
                "packs/form.html",
                mode="add",
                **_form_context(location_text=location),
            )

        try:
            photo_url = _handle_photo_upload()
        except BunnyStorageError as exc:
            flash(str(exc), "danger")
            return render_template(
                "packs/form.html",
                mode="add",
                **_form_context(location_text=location),
            )

        pack = service.create_from_form(
            user_id=_user_id(),
            form_data=request.form,
            photo_url=photo_url,
        )
        flash(f"Saved “{pack.name}”.", "success")

        if action == "save_next":
            return redirect(url_for("packs.add", clear="0"))
        if action == "save_clear":
            return redirect(url_for("packs.add", clear="1"))
        return redirect(url_for("packs.detail", pack_id=pack.id))

    clear = request.args.get("clear") == "1"
    return render_template(
        "packs/form.html",
        mode="add",
        clear_prefs=clear,
        **_form_context(),
    )


@packs_bp.route("/<uuid:pack_id>")
# @login_required  # Temporarily disabled for testing
@database_required
def detail(pack_id):
    pack = PackService().get_by_id(pack_id, _user_id())
    if not pack:
        flash("Pack not found.", "warning")
        return redirect(url_for("packs.list_packs"))
    return render_template("packs/detail.html", pack=pack)


@packs_bp.route("/<uuid:pack_id>/edit", methods=["GET", "POST"])
# @login_required  # Temporarily disabled for testing
@database_required
def edit(pack_id):
    service = PackService()
    pack = service.get_by_id(pack_id, _user_id())
    if not pack:
        flash("Pack not found.", "warning")
        return redirect(url_for("packs.list_packs"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        location = (request.form.get("location") or "").strip()

        if not name or not location:
            flash("Item name and location are required.", "danger")
            return render_template(
                "packs/form.html",
                mode="edit",
                **_form_context(pack, location),
            )

        try:
            photo_url = _handle_photo_upload()
        except BunnyStorageError as exc:
            flash(str(exc), "danger")
            return render_template(
                "packs/form.html",
                mode="edit",
                **_form_context(pack, location),
            )

        service.update_from_form(pack, request.form, photo_url=photo_url)
        flash(f"Updated “{pack.name}”.", "success")
        return redirect(url_for("packs.detail", pack_id=pack.id))

    return render_template(
        "packs/form.html",
        mode="edit",
        **_form_context(pack),
    )


@packs_bp.route("/<uuid:pack_id>/delete", methods=["POST"])
# @login_required  # Temporarily disabled for testing
@database_required
def delete(pack_id):
    service = PackService()
    pack = service.get_by_id(pack_id, _user_id())
    if not pack:
        flash("Pack not found.", "warning")
        return redirect(url_for("packs.list_packs"))

    name = pack.name
    service.delete(pack)
    flash(f"Deleted “{name}”.", "info")
    return redirect(url_for("packs.list_packs"))
