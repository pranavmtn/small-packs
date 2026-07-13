"""Database models for Packs.

Maps to the existing inventory_items table — do not create or migrate tables.
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import JSON, SmallInteger, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.services.database import db


class InventoryItem(db.Model):
    """Household inventory pack mapped to inventory_items."""

    __tablename__ = "inventory_items"
    __table_args__ = {"extend_existing": True}

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = db.Column(UUID(as_uuid=True), nullable=True, index=True)
    name = db.Column(Text, nullable=False)
    photo_url = db.Column(Text, nullable=True)
    category = db.Column(Text, nullable=True)  # Filled by AI later
    age_years = db.Column(SmallInteger, nullable=False, default=0)
    age_months = db.Column(SmallInteger, nullable=False, default=0)
    location = db.Column(JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=list)
    condition_percent = db.Column(SmallInteger, nullable=True)
    importance_percent = db.Column(SmallInteger, nullable=True)
    suggested_price = db.Column(db.Numeric(12, 2), nullable=True)
    notes = db.Column(Text, nullable=True)
    ai_description = db.Column(Text, nullable=True)  # Filled by AI later
    status = db.Column(Text, nullable=False, default="active", index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    STATUSES = ("active", "archived", "sold", "disposed")

    def location_display(self) -> str:
        """Human-readable location path."""
        loc = self.location
        if not loc:
            return ""
        if isinstance(loc, str):
            import json

            try:
                loc = json.loads(loc)
            except (TypeError, ValueError):
                return loc
        if isinstance(loc, list):
            return " > ".join(str(part) for part in loc)
        return str(loc)

    def age_display(self) -> str:
        """Human-readable age."""
        years = self.age_years or 0
        months = self.age_months or 0
        parts = []
        if years:
            parts.append(f"{years}y")
        if months:
            parts.append(f"{months}m")
        return " ".join(parts) if parts else "—"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "name": self.name,
            "photo_url": self.photo_url,
            "category": self.category,
            "age_years": self.age_years,
            "age_months": self.age_months,
            "location": self.location,
            "location_display": self.location_display(),
            "condition_percent": self.condition_percent,
            "importance_percent": self.importance_percent,
            "suggested_price": float(self.suggested_price)
            if self.suggested_price is not None
            else None,
            "notes": self.notes,
            "ai_description": self.ai_description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<InventoryItem id={self.id} name={self.name!r}>"
