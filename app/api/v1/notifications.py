# app/api/v1/notifications.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import SessionLocal
from app.schemas.notification import NotificationCreate, NotificationOut
from app.services.notification_service import (
    create_notification,
    get_notifications_by_user,
    delete_notification,
)
from app.models.notification import Notification
from app.core.rbac import responsable_required

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Notification non trouvée"}}
)

# Dépendance DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/",
    response_model=NotificationOut,
    summary="Créer une notification",
    description="Crée une notification par email ou log pour une intervention (admin/responsable uniquement).",
    dependencies=[Depends(responsable_required)]
)
def create_new_notification(data: NotificationCreate, db: Session = Depends(get_db)):
    return create_notification(db, data)

@router.get(
    "/",
    response_model=List[NotificationOut],
    summary="Lister les notifications",
    description="Retourne toutes les notifications envoyées (admin/responsable uniquement).",
    dependencies=[Depends(responsable_required)]
)
def list_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).all()


@router.get(
    "/user/{user_id}",
    response_model=List[NotificationOut],
    summary="Notifications d'un utilisateur",
    description="Retourne toutes les notifications associées à un utilisateur donné.",
    dependencies=[Depends(responsable_required)],
)
def list_user_notifications(user_id: int, db: Session = Depends(get_db)):
    return get_notifications_by_user(db, user_id)


@router.delete(
    "/{notification_id}",
    status_code=204,
    summary="Supprimer une notification",
    description="Supprime définitivement une notification (admin/responsable uniquement).",
    dependencies=[Depends(responsable_required)],
)
def remove_notification(notification_id: int, db: Session = Depends(get_db)):
    delete_notification(db, notification_id)
    return None
