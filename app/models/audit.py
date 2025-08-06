"""
Modèle Audit : journalisation des actions utilisateur pour la traçabilité.

- N:1 avec User
- Enregistre l'action, la table ciblée et l'horodatage
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Any, Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from .user import User


class Audit(Base):
    """Journal des actions réalisées dans le système."""

    __tablename__ = "audits"
    __table_args__ = (
        Index("idx_audit_table_object", "table_name", "object_id"),
        Index("idx_audit_user_date", "user_id", "created_at"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    action: str = Column(String(255), nullable=False, index=True)
    table_name: str = Column(String(255), nullable=False, index=True)
    object_id: Optional[int] = Column(Integer, nullable=True, index=True)
    details: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user_id: Optional[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user: "User" = relationship("User", back_populates="audits", lazy="select")

    def to_dict(self, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "action": self.action,
            "table_name": self.table_name,
            "object_id": self.object_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id,
        }
        if include_relations:
            data["user"] = self.user.to_dict() if self.user else None
        return data


__all__ = ["Audit"]

