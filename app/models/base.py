"""Base entity helpers shared by all models.

``BaseModel`` represents the common columns every table carries
(``id``, ``created_at``, ``updated_at``) and is used as a convenience
base for the data-access modules.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def now_utc():
    """ISO-8601 UTC timestamp, e.g. ``2026-09-12 10:00:00``."""
    return datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")


def to_dict(row):
    """Convert a sqlite3.Row (or None) to a plain dict (or None)."""
    return dict(row) if row is not None else None


@dataclass
class BaseModel:
    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_row(cls, row):
        """Build an instance from a sqlite3.Row, stashing unknown columns."""
        if row is None:
            return None
        data = dict(row)
        obj = cls(
            id=data.pop("id", None),
            created_at=data.pop("created_at", None),
            updated_at=data.pop("updated_at", None),
            extra=data,
        )
        return obj

    def asdict(self):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            **self.extra,
        }