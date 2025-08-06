from __future__ import annotations

"""Services liés aux historiques d'intervention (audit).

Ces fonctions encapsulent les opérations CRUD de base sur le modèle
:class:`HistoriqueIntervention`. Elles facilitent la réutilisation de la
logique métier notamment pour la consultation des événements d'une
intervention et la suppression d'entrées lorsque nécessaire.
"""

from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.historique import HistoriqueIntervention
from app.schemas.historique import HistoriqueCreate


def create_historique(db: Session, data: HistoriqueCreate) -> HistoriqueIntervention:
    """Crée une entrée d'historique pour une intervention."""
    historique = HistoriqueIntervention(
        statut=data.statut,
        remarque=data.remarque,
        horodatage=datetime.utcnow(),
        intervention_id=data.intervention_id,
        user_id=data.user_id,
    )
    db.add(historique)
    db.commit()
    db.refresh(historique)
    return historique


def get_historique(db: Session, historique_id: int) -> HistoriqueIntervention:
    """Récupère une entrée d'historique par son identifiant."""
    historique = (
        db.query(HistoriqueIntervention)
        .filter(HistoriqueIntervention.id == historique_id)
        .first()
    )
    if not historique:
        raise HTTPException(status_code=404, detail="Historique introuvable")
    return historique


def list_historique_by_intervention(
    db: Session, intervention_id: int
) -> List[HistoriqueIntervention]:
    """Liste les historiques associés à une intervention."""
    return (
        db.query(HistoriqueIntervention)
        .filter(HistoriqueIntervention.intervention_id == intervention_id)
        .order_by(HistoriqueIntervention.horodatage)
        .all()
    )


def delete_historique(db: Session, historique_id: int) -> None:
    """Supprime une entrée d'historique.

    Raises:
        HTTPException: si l'entrée n'existe pas.
    """
    historique = get_historique(db, historique_id)
    db.delete(historique)
    db.commit()
