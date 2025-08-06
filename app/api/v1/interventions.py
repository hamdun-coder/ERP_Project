from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import SessionLocal
from app.schemas.intervention import InterventionCreate, InterventionOut, StatutIntervention
from app.schemas.historique import HistoriqueOut
from app.services.intervention_service import (
    create_intervention,
    get_intervention_by_id,
    get_all_interventions,
    update_statut_intervention,
)
from app.services.historique_service import list_historique_by_intervention
from app.core.rbac import get_current_user, technicien_required, responsable_required

router = APIRouter(
    prefix="/interventions",
    tags=["interventions"],
    responses={404: {"description": "Intervention non trouvée"}},
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/", 
    response_model=InterventionOut,
    summary="Créer une intervention",
    description="Crée une intervention préventive ou corrective. (admin, responsable uniquement)",
    dependencies=[Depends(responsable_required)]
)
def create_new_intervention(
    data: InterventionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # Ajout utilisateur courant ici
):
    # 👇 Passe l'id du user authentifié au service
    return create_intervention(db, data, user_id=int(user["user_id"]))

@router.get(
    "/", 
    response_model=List[InterventionOut],
    summary="Lister les interventions",
    description="Retourne toutes les interventions du système (authentification requise)"
)
def list_interventions(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_all_interventions(db)

@router.get(
    "/{intervention_id}", 
    response_model=InterventionOut,
    summary="Détail d’une intervention",
    description="Récupère les détails d’une intervention par ID (authentification requise)"
)
def get_intervention(intervention_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_intervention_by_id(db, intervention_id)

@router.patch(
    "/{intervention_id}/statut", 
    response_model=InterventionOut,
    summary="Changer le statut d’une intervention",
    description="Met à jour le statut (cycle de vie) de l’intervention. Action historisée avec l’utilisateur en cours.",
    dependencies=[Depends(technicien_required)]
)
def change_statut_intervention(
    intervention_id: int,
    statut: StatutIntervention,
    remarque: str = "",
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    return update_statut_intervention(
        db=db,
        intervention_id=intervention_id,
        new_statut=statut,
        user_id=int(user["user_id"]),
        remarque=remarque
    )


@router.get(
    "/{intervention_id}/historique",
    response_model=List[HistoriqueOut],
    summary="Historique d'une intervention",
    description="Retourne la liste des événements enregistrés pour l'intervention donnée.",
)
def get_historique_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return list_historique_by_intervention(db, intervention_id)
