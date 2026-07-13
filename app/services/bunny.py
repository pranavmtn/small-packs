"""Bunny.net storage upload service."""

from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime, timezone
from typing import BinaryIO

import requests
from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class BunnyStorageError(Exception):
    """Raised when a Bunny.net upload fails."""


class BunnyStorageService:
    """Upload images to Bunny.net Storage and return CDN URLs."""

    REGION_HOSTS = {
        "": "storage.bunnycdn.com",
        "de": "storage.bunnycdn.com",
        "uk": "uk.storage.bunnycdn.com",
        "ny": "ny.storage.bunnycdn.com",
        "la": "la.storage.bunnycdn.com",
        "sg": "sg.storage.bunnycdn.com",
        "se": "se.storage.bunnycdn.com",
        "br": "br.storage.bunnycdn.com",
        "jh": "jh.storage.bunnycdn.com",
        "syd": "syd.storage.bunnycdn.com",
    }

    def __init__(
        self,
        storage_zone: str | None = None,
        access_key: str | None = None,
        region: str | None = None,
        pull_zone: str | None = None,
    ):
        self.storage_zone = storage_zone
        self.access_key = access_key
        self.region = (region or "").lower().strip()
        self.pull_zone = pull_zone

    @classmethod
    def from_app_config(cls) -> "BunnyStorageService":
        cfg = current_app.config
        return cls(
            storage_zone=cfg.get("BUNNY_STORAGE_ZONE"),
            access_key=cfg.get("BUNNY_ACCESS_KEY"),
            region=cfg.get("BUNNY_REGION"),
            pull_zone=cfg.get("BUNNY_PULL_ZONE"),
        )

    def is_configured(self) -> bool:
        return bool(self.storage_zone and self.access_key and self.pull_zone)

    def _storage_host(self) -> str:
        return self.REGION_HOSTS.get(self.region, "storage.bunnycdn.com")

    def _build_object_path(self, filename: str, folder: str = "packs") -> str:
        safe = secure_filename(filename) or "image.jpg"
        ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else "jpg"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        unique = uuid.uuid4().hex[:12]
        return f"{folder}/{stamp}/{unique}.{ext}"

    def _cdn_url(self, object_path: str) -> str:
        zone = self.pull_zone.rstrip("/")
        if zone.startswith("http://") or zone.startswith("https://"):
            return f"{zone}/{object_path}"
        return f"https://{zone}.b-cdn.net/{object_path}"

    def upload_file(
        self,
        file_obj: BinaryIO | FileStorage,
        filename: str | None = None,
        folder: str = "packs",
        content_type: str | None = None,
    ) -> str:
        """Upload a file and return the public CDN URL."""
        if not self.is_configured():
            raise BunnyStorageError(
                "Bunny.net is not configured. Set BUNNY_* variables in .env."
            )

        name = filename
        if isinstance(file_obj, FileStorage):
            name = name or file_obj.filename
            content_type = content_type or file_obj.mimetype
            stream = file_obj.stream
        else:
            stream = file_obj

        if not name:
            raise BunnyStorageError("Filename is required for upload.")

        object_path = self._build_object_path(name, folder=folder)
        url = f"https://{self._storage_host()}/{self.storage_zone}/{object_path}"

        guessed_type = content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        headers = {
            "AccessKey": self.access_key,
            "Content-Type": guessed_type,
        }

        data = stream.read()
        if hasattr(stream, "seek"):
            stream.seek(0)

        response = requests.put(url, data=data, headers=headers, timeout=60)
        if response.status_code not in (200, 201):
            raise BunnyStorageError(
                f"Bunny upload failed ({response.status_code}): {response.text}"
            )

        return self._cdn_url(object_path)

    def allowed_file(self, filename: str, allowed: set[str] | None = None) -> bool:
        if not filename or "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[-1].lower()
        allowed = allowed or current_app.config.get(
            "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"}
        )
        return ext in allowed
