"""
Association InterventionEquipement : lien many-to-many entre interventions et équipements.

Permet de suivre les équipements concernés par une intervention au-delà de
l'équipement principal.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship

from app.db.database import Base

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les types
    from .intervention import Intervention
    from .equipement import Equipement


class InterventionEquipement(Base):
    """Table d'association interventions ↔ équipements."""

    __tablename__ = "interventions_equipements"
    __table_args__ = (
        Index("idx_intervention_equipement", "intervention_id", "equipement_id"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    intervention_id: int = Column(
        Integer,
        ForeignKey("interventions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    equipement_id: int = Column(
        Integer,
        ForeignKey("equipements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    intervention: "Intervention" = relationship(
        "Intervention", back_populates="equipements_assoc", lazy="select"
    )
    equipement: "Equipement" = relationship(
        "Equipement", back_populates="interventions_assoc", lazy="select"
    )

    def to_dict(self, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "intervention_id": self.intervention_id,
            "equipement_id": self.equipement_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_relations:
            data["intervention"] = (
                self.intervention.to_dict() if self.intervention else None
            )
            data["equipement"] = self.equipement.to_dict() if self.equipement else None
        return data


__all__ = ["InterventionEquipement"]

