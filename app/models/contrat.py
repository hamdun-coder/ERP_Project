# app/models/contrat.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Text, Date, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.database import Base
import enum


class TypeContrat(str, enum.Enum):
    """Types de contrats de maintenance"""
    maintenance_preventive = "maintenance_preventive"
    maintenance_corrective = "maintenance_corrective"
    maintenance_complete = "maintenance_complete"
    support_technique = "support_technique"
    contrat_cadre = "contrat_cadre"


class StatutContrat(str, enum.Enum):
    """Statuts d'un contrat"""
    brouillon = "brouillon"
    en_cours = "en_cours"
    expire = "expire"
    resilie = "resilie"
    suspendu = "suspendu"



"""
Modèle Contrat : gestion des contrats de maintenance, conditions, SLA, facturation, KPIs.
Relations : N:1 avec Client, 1:N avec Intervention, 1:N avec Facture.
Exemple : suivi des droits, renouvellement, reporting, audit.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Text, Date, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any
import enum

if TYPE_CHECKING:
    from .client import Client
    from .intervention import Intervention
    from .facture import Facture

class ModeFacturation(str, enum.Enum):
    mensuel = "mensuel"
    trimestriel = "trimestriel"
    annuel = "annuel"

class Contrat(Base):
    """
    Modèle Contrat de Maintenance.
    - Informations contractuelles, conditions financières, SLA, KPIs
    - Relations avec client, interventions, factures
    - Préparé pour extension (audit, renouvellement, logs)
    """
    __tablename__ = "contrats"
    __table_args__ = (
        Index('idx_contrat_client_dates', 'client_id', 'date_debut', 'date_fin'),
        Index('idx_contrat_statut', 'statut'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    numero_contrat: str = Column(String(50), nullable=False, unique=True, index=True)
    nom_contrat: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    type_contrat: TypeContrat = Column(Enum(TypeContrat), nullable=False, index=True)
    statut: StatutContrat = Column(Enum(StatutContrat), default=StatutContrat.brouillon, nullable=False, index=True)

    date_signature: Optional[date] = Column(Date, nullable=True)
    date_debut: date = Column(Date, nullable=False, index=True)
    date_fin: date = Column(Date, nullable=False, index=True)
    date_renouvellement: Optional[date] = Column(Date, nullable=True)

    montant_annuel: Optional[float] = Column(Numeric(12, 2), nullable=True)
    montant_mensuel: Optional[float] = Column(Numeric(10, 2), nullable=True)
    devise: str = Column(String(3), default="EUR")
    mode_facturation: ModeFacturation = Column(Enum(ModeFacturation), default=ModeFacturation.mensuel, nullable=False, index=True)

    temps_reponse_urgence: Optional[int] = Column(Integer, nullable=True)
    temps_reponse_normal: Optional[int] = Column(Integer, nullable=True)
    taux_disponibilite: Optional[float] = Column(Numeric(5, 2), nullable=True)
    penalites_retard: Optional[float] = Column(Numeric(10, 2), nullable=True)

    nb_interventions_incluses: Optional[int] = Column(Integer, nullable=True)
    nb_interventions_utilisees: int = Column(Integer, default=0)
    heures_maintenance_incluses: Optional[int] = Column(Integer, nullable=True)
    heures_maintenance_utilisees: int = Column(Integer, default=0)

    equipements_couverts: Optional[str] = Column(Text, nullable=True)

    contact_client: Optional[str] = Column(String(255), nullable=True)
    contact_responsable: Optional[str] = Column(String(255), nullable=True)

    is_active: bool = Column(Boolean, default=True, nullable=False, index=True)
    date_creation: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    date_modification: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client_id: int = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    client: "Client" = relationship("Client", back_populates="contrats", lazy="joined")
    interventions = relationship(
        "Intervention",
        back_populates="contrat",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    factures = relationship(
        "Facture",
        back_populates="contrat",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    equipements = relationship(
        "Equipement",
        back_populates="contrat",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Contrat(id={self.id}, numero='{self.numero_contrat}', client='{self.client_id}')>"

    @property
    def est_actif(self) -> bool:
        today = date.today()
        return (
            self.statut == StatutContrat.en_cours and
            self.date_debut <= today <= self.date_fin
        )

    @property
    def est_expire(self) -> bool:
        return date.today() > self.date_fin

    @property
    def jours_restants(self) -> int:
        if self.est_expire:
            return 0
        return (self.date_fin - date.today()).days

    @property
    def pourcentage_interventions_utilisees(self) -> float:
        if self.nb_interventions_incluses and self.nb_interventions_incluses > 0:
            return (self.nb_interventions_utilisees / self.nb_interventions_incluses) * 100
        return 0.0

    @property
    def pourcentage_heures_utilisees(self) -> float:
        if self.heures_maintenance_incluses and self.heures_maintenance_incluses > 0:
            return (self.heures_maintenance_utilisees / self.heures_maintenance_incluses) * 100
        return 0.0

    @property
    def interventions_restantes(self) -> Optional[int]:
        if self.nb_interventions_incluses:
            return max(0, self.nb_interventions_incluses - self.nb_interventions_utilisees)
        return None

    @property
    def heures_restantes(self) -> Optional[int]:
        if self.heures_maintenance_incluses:
            return max(0, self.heures_maintenance_incluses - self.heures_maintenance_utilisees)
        return None

    def peut_faire_intervention(self) -> bool:
        if not self.est_actif:
            return False
        if self.nb_interventions_incluses and self.nb_interventions_utilisees >= self.nb_interventions_incluses:
            return False
        return True

    def consommer_intervention(self, heures_travaillees: int = 0) -> None:
        if self.nb_interventions_incluses:
            self.nb_interventions_utilisees += 1
        if self.heures_maintenance_incluses and heures_travaillees > 0:
            self.heures_maintenance_utilisees += heures_travaillees

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "numero_contrat": self.numero_contrat,
            "nom_contrat": self.nom_contrat,
            "type_contrat": self.type_contrat.value,
            "statut": self.statut.value,
            "date_signature": self.date_signature.isoformat() if self.date_signature else None,
            "date_debut": self.date_debut.isoformat() if self.date_debut else None,
            "date_fin": self.date_fin.isoformat() if self.date_fin else None,
            "date_renouvellement": self.date_renouvellement.isoformat() if self.date_renouvellement else None,
            "montant_annuel": float(self.montant_annuel) if self.montant_annuel else None,
            "montant_mensuel": float(self.montant_mensuel) if self.montant_mensuel else None,
            "devise": self.devise,
            "mode_facturation": self.mode_facturation.value,
            "temps_reponse_urgence": self.temps_reponse_urgence,
            "temps_reponse_normal": self.temps_reponse_normal,
            "taux_disponibilite": float(self.taux_disponibilite) if self.taux_disponibilite else None,
            "penalites_retard": float(self.penalites_retard) if self.penalites_retard else None,
            "nb_interventions_incluses": self.nb_interventions_incluses,
            "nb_interventions_utilisees": self.nb_interventions_utilisees,
            "heures_maintenance_incluses": self.heures_maintenance_incluses,
            "heures_maintenance_utilisees": self.heures_maintenance_utilisees,
            "equipements_couverts": self.equipements_couverts,
            "contact_client": self.contact_client,
            "contact_responsable": self.contact_responsable,
            "is_active": self.is_active,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "date_modification": self.date_modification.isoformat() if self.date_modification else None,
            "client_id": self.client_id,
            "est_actif": self.est_actif,
            "est_expire": self.est_expire,
            "jours_restants": self.jours_restants,
            "pourcentage_interventions_utilisees": self.pourcentage_interventions_utilisees,
            "pourcentage_heures_utilisees": self.pourcentage_heures_utilisees,
            "interventions_restantes": self.interventions_restantes,
            "heures_restantes": self.heures_restantes,
        }
        if include_relations:
            data["client"] = self.client.to_dict() if self.client else None
        return data

    # NOTE: Préparé pour extension future (audit, renouvellement, logs, etc.)



class StatutPaiement(str, enum.Enum):
    en_attente = "en_attente"
    payee = "payee"
    en_retard = "en_retard"

class Facture(Base):
    """
    Modèle Facture liée à un contrat de maintenance.
    - Informations de facturation, montants, statut de paiement
    - Préparé pour extension (audit, relance, logs)
    """
    __tablename__ = "factures"
    __table_args__ = (
        Index('idx_facture_contrat_echeance', 'contrat_id', 'date_echeance'),
        Index('idx_facture_statut', 'statut_paiement'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    numero_facture: str = Column(String(50), nullable=False, unique=True, index=True)
    date_emission: date = Column(Date, nullable=False, index=True)
    date_echeance: date = Column(Date, nullable=False, index=True)
    montant_ht: float = Column(Numeric(10, 2), nullable=False)
    taux_tva: float = Column(Numeric(5, 2), default=20.0)
    montant_ttc: float = Column(Numeric(10, 2), nullable=False)
    statut_paiement: StatutPaiement = Column(Enum(StatutPaiement), default=StatutPaiement.en_attente, nullable=False, index=True)
    date_paiement: Optional[date] = Column(Date, nullable=True)
    description: Optional[str] = Column(Text, nullable=True)
    periode_debut: Optional[date] = Column(Date, nullable=True)
    periode_fin: Optional[date] = Column(Date, nullable=True)
    date_creation: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    contrat_id: int = Column(Integer, ForeignKey("contrats.id", ondelete="CASCADE"), nullable=False, index=True)
    contrat: "Contrat" = relationship("Contrat", back_populates="factures", lazy="joined")

    def __repr__(self) -> str:
        return f"<Facture(id={self.id}, numero='{self.numero_facture}', montant={self.montant_ttc})>"

    @property
    def est_en_retard(self) -> bool:
        return (
            self.statut_paiement != StatutPaiement.payee and
            date.today() > self.date_echeance
        )

    @property
    def jours_retard(self) -> int:
        if self.est_en_retard:
            return (date.today() - self.date_echeance).days
        return 0

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "numero_facture": self.numero_facture,
            "date_emission": self.date_emission.isoformat() if self.date_emission else None,
            "date_echeance": self.date_echeance.isoformat() if self.date_echeance else None,
            "montant_ht": float(self.montant_ht),
            "taux_tva": float(self.taux_tva),
            "montant_ttc": float(self.montant_ttc),
            "statut_paiement": self.statut_paiement.value,
            "date_paiement": self.date_paiement.isoformat() if self.date_paiement else None,
            "description": self.description,
            "periode_debut": self.periode_debut.isoformat() if self.periode_debut else None,
            "periode_fin": self.periode_fin.isoformat() if self.periode_fin else None,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "contrat_id": self.contrat_id,
            "est_en_retard": self.est_en_retard,
            "jours_retard": self.jours_retard,
        }
        if include_relations:
            data["contrat"] = self.contrat.to_dict() if self.contrat else None
        return data

    # NOTE: Préparé pour extension future (audit, relance, logs, etc.)