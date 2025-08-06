import pytest
import pytest

from app.models.user import User
from app.models.intervention import Intervention
from app.models.notification import Notification
from app.core.security import get_password_hash


@pytest.fixture()
def db(db_session):
    """Utilise la session de base de données de test partagée."""
    yield db_session

@pytest.fixture()
def notif_user_and_token(client, db):
    """Crée un utilisateur et retourne header JWT"""
    user = User(
        username="notifuser",
        email="notifuser@example.com",
        hashed_password=get_password_hash("notifpass"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "notifuser", "password": "notifpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user

@pytest.fixture()
def created_intervention(db):
    """Crée une intervention temporaire"""
    intervention = Intervention(
        titre="Notif Intervention",
        description="Pour test de notification",
        statut="ouverte",
        type="corrective",
        urgence=False
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    yield intervention
    db.delete(intervention)
    db.commit()

def test_create_notification(client, notif_user_and_token, created_intervention):
    """Création d'une notification liée à une intervention"""
    headers, user = notif_user_and_token
    response = client.post(
        "/api/v1/notifications/",
        json={
            "type": "affectation",
            "canal": "email",
            "contenu": "Vous avez été affecté à une intervention.",
            "user_id": user.id,
            "intervention_id": created_intervention.id
        },
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "affectation"
    assert data["user_id"] == user.id
    assert data["intervention_id"] == created_intervention.id

    # Nettoyage
    client.delete(f"/api/v1/notifications/{data['id']}", headers=headers)


def test_get_user_notifications(client, notif_user_and_token, created_intervention):
    """Récupère les notifications utilisateur"""
    headers, user = notif_user_and_token

    # Crée une notification pour test
    create_resp = client.post(
        "/api/v1/notifications/",
        json={
            "type": "cloture",
            "canal": "email",
            "contenu": "Intervention clôturée.",
            "user_id": user.id,
            "intervention_id": created_intervention.id
        },
        headers=headers
    )
    assert create_resp.status_code == 201
    notif_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/notifications/user/{user.id}", headers=headers)
    assert response.status_code == 200
    notifications = response.json()
    assert isinstance(notifications, list)
    assert any(n["id"] == notif_id for n in notifications)

    # Nettoyage
    client.delete(f"/api/v1/notifications/{notif_id}", headers=headers)


def test_get_user_notifications_empty(client, notif_user_and_token, db):
    """Retourne une liste vide si l’utilisateur n’a aucune notification"""
    headers, user = notif_user_and_token

    # Supprime toutes les notifs de l’utilisateur (si existantes)
    db.query(Notification).filter_by(user_id=user.id).delete()
    db.commit()

    response = client.get(f"/api/v1/notifications/user/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
