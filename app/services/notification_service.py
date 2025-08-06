# app/services/notification_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from typing import List

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.models.user import User
from app.core.config import settings

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Configuration des templates Jinja
env = Environment(loader=FileSystemLoader("app/templates"))


def create_notification(db: Session, data: NotificationCreate) -> Notification:
    """
    Crée une notification (log ou email) pour un utilisateur.

    Si canal == email, envoie un mail via SMTP.

    Raises:
        HTTPException 404: utilisateur ou intervention non trouvés
        HTTPException 500: échec envoi email
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur cible introuvable")

    notif = Notification(
        type=data.type,
        canal=data.canal,
        contenu=data.contenu,
        user_id=data.user_id,
        intervention_id=data.intervention_id,
        date_envoi=datetime.utcnow()
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    if data.canal == "email":
        send_email_notification(user.email, notif)

    return notif


def get_notifications_by_user(db: Session, user_id: int) -> List[Notification]:
    """Retourne toutes les notifications d'un utilisateur."""
    return db.query(Notification).filter(Notification.user_id == user_id).all()


def delete_notification(db: Session, notification_id: int) -> None:
    """Supprime une notification existante.

    Args:
        db: Session de base de données.
        notification_id: identifiant de la notification à supprimer.

    Raises:
        HTTPException: si la notification n'existe pas.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    db.delete(notif)
    db.commit()


def send_email_notification(email_to: str, notification: Notification):
    """
    Envoie un email à l'utilisateur cible avec rendu HTML.

    Le template est choisi dynamiquement selon le type (ex: "notification_affectation.html").

    Raises:
        HTTPException 500: en cas d’échec d’envoi
    """
    try:
        subject = f"[MIF] Notification - {notification.type.capitalize()}"
        template_name = f"notification_{notification.type}.html"

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise HTTPException(status_code=500, detail=f"Template '{template_name}' introuvable")

        html_content = template.render(
            type=notification.type,
            contenu=notification.contenu or "Voir détails dans l’application."
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAILS_FROM_EMAIL
        msg["To"] = email_to
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.EMAILS_FROM_EMAIL,
                email_to,
                msg.as_string()
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur envoi email : {str(e)}")
