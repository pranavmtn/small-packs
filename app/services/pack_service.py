"""Inventory / pack business logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import desc, func, or_

from app.models import InventoryItem
from app.services.database import DatabaseService, db
from app.services.location_parser import parse_location

UserId = Union[str, UUID]
PackId = Union[str, UUID]


def _as_uuid(value: UserId) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class PackService:
    """CRUD and query helpers for inventory packs."""

    def __init__(self, db_service: DatabaseService | None = None):
        self.db = db_service or DatabaseService()

    def get_by_id(self, pack_id: PackId, user_id: UserId) -> Optional[InventoryItem]:
        return InventoryItem.query.filter_by(
            id=_as_uuid(pack_id),
            user_id=_as_uuid(user_id),
        ).first()

    def list_packs(
        self,
        user_id: UserId,
        search: str | None = None,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[InventoryItem]:
        query = InventoryItem.query.filter_by(user_id=_as_uuid(user_id))

        if status and status != "all":
            query = query.filter_by(status=status)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    InventoryItem.name.ilike(term),
                    InventoryItem.category.ilike(term),
                    InventoryItem.notes.ilike(term),
                    InventoryItem.ai_description.ilike(term),
                )
            )

        query = query.order_by(desc(InventoryItem.created_at))
        if limit:
            query = query.limit(limit)
        return query.all()

    def dashboard_stats(self, user_id: UserId) -> dict[str, Any]:
        uid = _as_uuid(user_id)
        total = (
            db.session.query(func.count(InventoryItem.id))
            .filter_by(user_id=uid)
            .scalar()
            or 0
        )
        active = (
            db.session.query(func.count(InventoryItem.id))
            .filter_by(user_id=uid, status="active")
            .scalar()
            or 0
        )
        recent = self.list_packs(user_id=uid, limit=8)
        return {
            "total_packs": total,
            "active_packs": active,
            "recent_packs": recent,
        }

    def create_from_form(
        self,
        user_id: UserId,
        form_data: dict,
        photo_url: str | None = None,
    ) -> InventoryItem:
        pack = InventoryItem(id=uuid.uuid4(), user_id=_as_uuid(user_id))
        self._apply_form(pack, form_data, photo_url=photo_url, is_create=True)
        return self.db.save(pack)

    def update_from_form(
        self,
        pack: InventoryItem,
        form_data: dict,
        photo_url: str | None = None,
    ) -> InventoryItem:
        self._apply_form(pack, form_data, photo_url=photo_url, is_create=False)
        pack.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return pack

    def delete(self, pack: InventoryItem) -> None:
        self.db.delete(pack)
        self.db.commit()

    def _apply_form(
        self,
        pack: InventoryItem,
        form_data: dict,
        photo_url: str | None = None,
        is_create: bool = False,
    ) -> None:
        pack.name = (form_data.get("name") or "").strip()
        pack.age_years = self._to_int(form_data.get("age_years"), default=0)
        pack.age_months = self._clamp(
            self._to_int(form_data.get("age_months"), default=0), 0, 11
        )
        location = parse_location(form_data.get("location") or "")
        # Column is NOT NULL — never write null
        pack.location = location if location else []
        pack.category = (form_data.get("category") or "").strip() or None
        pack.condition_percent = self._optional_percent(
            form_data.get("condition_percent")
        )
        pack.importance_percent = self._optional_percent(
            form_data.get("importance_percent")
        )
        pack.suggested_price = self._to_decimal(form_data.get("suggested_price"))
        pack.notes = (form_data.get("notes") or "").strip() or None
        pack.status = (form_data.get("status") or "active").strip() or "active"

        if photo_url:
            pack.photo_url = photo_url
        elif is_create and not pack.photo_url:
            pack.photo_url = None

        if is_create:
            pack.ai_description = None
            if not pack.category:
                pack.category = None

    @staticmethod
    def _to_int(value, default: int = 0) -> int:
        try:
            if value is None or str(value).strip() == "":
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, value))

    @staticmethod
    def _optional_percent(value) -> int | None:
        if value is None or str(value).strip() == "":
            return None
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        if value is None or str(value).strip() == "":
            return None
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            return None
