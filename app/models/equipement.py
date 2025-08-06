# app/models/equipement.py
"""
Modèle Equipement - Gestion du parc matériel.

Ce module gère le patrimoine technique de l'ERP :
- Inventaire complet des équipements industriels
- Caractéristiques techniques et localisation
- Maintenance préventive et corrective
- Historique des interventions et pannes
- Planification et cycles d'entretien
- Relations avec contrats et clients

Architecture:
- Modèle central pour la maintenance industrielle
- Relations optimisées avec interventions/planning
- Index de performance sur localisation et type
- Propriétés calculées pour KPI maintenance
- Interface to_dict() standardisée pour API
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, Index, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any, List
import enum

# NOTE: Import conditionnel pour éviter les imports circulaires
if TYPE_CHECKING:
    from .intervention import Intervention
    from .planning import Planning
    from .client import Client
    from .contrat import Contrat
    from .intervention_equipement import InterventionEquipement


class StatutEquipement(str, enum.Enum):
    """
    Statuts opérationnels des équipements.
    
    - operationnel : en service normal
    - maintenance : en cours de maintenance
    - panne : hors service suite à défaillance
    - retire : retiré du service définitivement
    """
    operationnel = "operationnel"
    maintenance = "maintenance"
    panne = "panne"
    retire = "retire"


class CriticiteEquipement(str, enum.Enum):
    """
    Niveaux de criticité métier des équipements.
    
    - critique : arrêt de production si panne
    - important : impact significatif sur production
    - standard : impact modéré
    - non_critique : impact minimal
    """
    critique = "critique"
    important = "important"
    standard = "standard"
    non_critique = "non_critique"


class Equipement(Base):
    """
    Modèle Equipement - Patrimoine technique de l'entreprise.
    
    Gestion complète du parc matériel avec :
    - Identification unique et caractéristiques techniques
    - Localisation géographique et responsabilités
    - Statut opérationnel et criticité métier
    - Cycles de maintenance préventive
    - Historique des interventions et performances
    - Relations contractuelles et propriété client
    
    Relations clés :
    - 1:N avec Interventions (historique maintenance)
    - 1:N avec Planning (planification préventive)
    - N:1 avec Client (propriétaire/responsable)
    - N:1 avec Contrat (couverture contractuelle)
    
    Performances :
    - Index composites sur type+localisation, statut+criticité
    - Relations lazy=dynamic pour collections volumineuses
    - Propriétés calculées mises en cache applicatif
    """
    __tablename__ = "equipements"

    # NOTE: Index composites pour requêtes métier fréquentes
    __table_args__ = (
        Index('idx_equipement_type_localisation', 'type_equipement', 'localisation'),
        Index('idx_equipement_statut_criticite', 'statut', 'criticite'),
        Index('idx_equipement_client_statut', 'client_id', 'statut'),
        Index('idx_equipement_created_type', 'created_at', 'type_equipement'),
    )

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)

    # Identification et caractéristiques
    nom = Column(String(255), nullable=False, index=True)
    numero_serie = Column(String(100), unique=True, nullable=True, index=True)
    code_interne = Column(String(50), unique=True, nullable=True, index=True)
    type_equipement = Column(String(100), nullable=False, index=True)
    marque = Column(String(100), nullable=True)
    modele = Column(String(100), nullable=True)
    
    # Localisation et environnement
    localisation = Column(String(255), nullable=False, index=True)
    batiment = Column(String(100), nullable=True)
    etage = Column(String(20), nullable=True)
    zone = Column(String(100), nullable=True)
    
    # Statut opérationnel
    statut = Column(Enum(StatutEquipement), default=StatutEquipement.operationnel, nullable=False, index=True)
    criticite = Column(Enum(CriticiteEquipement), default=CriticiteEquipement.standard, nullable=False, index=True)
    
    # Caractéristiques techniques
    description = Column(Text, nullable=True)
    specifications_techniques = Column(Text, nullable=True)
    puissance = Column(Numeric(10, 2), nullable=True)  # en kW
    poids = Column(Numeric(10, 2), nullable=True)  # en kg
    
    # Maintenance et cycles
    frequence_entretien_jours = Column(Integer, nullable=True)  # Cycles en jours
    duree_garantie_mois = Column(Integer, nullable=True)  # Garantie en mois
    cout_acquisition = Column(Integer, nullable=True)  # En centimes d'euro
    
    # Métadonnées temporelles
    date_acquisition = Column(DateTime, nullable=True)
    date_mise_en_service = Column(DateTime, nullable=True)
    date_fin_garantie = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relations métier
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id", ondelete="SET NULL"), nullable=True, index=True)

    # 🔗 Relations ORM optimisées
    
    # Relations principales (N:1)
    client: Optional["Client"] = relationship(
        "Client", 
        back_populates="equipements",
        lazy="select"
    )
    
    contrat: Optional["Contrat"] = relationship(
        "Contrat", 
        back_populates="equipements",
        lazy="select"
    )
    
    # Relations de maintenance (1:N) - lazy dynamic pour performances
    interventions = relationship(
        "Intervention", 
        back_populates="equipement", 
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(Intervention.date_creation)"
    )
    
    plannings = relationship(
        "Planning",
        back_populates="equipement",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Planning.prochaine_date"
    )

    interventions_assoc = relationship(
        "InterventionEquipement",
        back_populates="equipement",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """Représentation concise pour debugging."""
        return f"<Equipement(id={self.id}, nom='{self.nom}', type='{self.type_equipement}', statut='{self.statut.value}')>"

    # 🏷️ Propriétés métier et calculs KPI

    @property
    def est_operationnel(self) -> bool:
        """Vérifie si l'équipement est opérationnel."""
        return self.statut == StatutEquipement.operationnel

    @property
    def est_en_panne(self) -> bool:
        """Vérifie si l'équipement est en panne."""
        return self.statut == StatutEquipement.panne

    @property
    def est_en_maintenance(self) -> bool:
        """Vérifie si l'équipement est en maintenance."""
        return self.statut == StatutEquipement.maintenance

    @property
    def est_critique(self) -> bool:
        """Vérifie si l'équipement est critique pour la production."""
        return self.criticite == CriticiteEquipement.critique

    @property
    def est_sous_garantie(self) -> bool:
        """Vérifie si l'équipement est encore sous garantie."""
        if not self.date_fin_garantie:
            return False
        return datetime.utcnow() < self.date_fin_garantie

    @property
    def age_en_jours(self) -> Optional[int]:
        """Calcule l'âge de l'équipement en jours depuis mise en service."""
        if not self.date_mise_en_service:
            return None
        delta = datetime.utcnow() - self.date_mise_en_service
        return delta.days

    @property
    def age_en_annees(self) -> Optional[float]:
        """Calcule l'âge de l'équipement en années."""
        if not self.age_en_jours:
            return None
        return round(self.age_en_jours / 365.25, 1)

    @property
    def prochaine_maintenance_calculee(self) -> Optional[datetime]:
        """Calcule la date de prochaine maintenance préventive."""
        if not self.frequence_entretien_jours:
            return None
            
        # Récupère la dernière intervention préventive
        derniere_preventive = self.interventions.filter_by(
            type_intervention="preventive"
        ).first()
        
        if derniere_preventive and derniere_preventive.date_cloture:
            base_date = derniere_preventive.date_cloture
        elif self.date_mise_en_service:
            base_date = self.date_mise_en_service
        else:
            base_date = self.created_at
            
        return base_date + timedelta(days=self.frequence_entretien_jours)

    @property
    def maintenance_en_retard(self) -> bool:
        """Vérifie si la maintenance préventive est en retard."""
        prochaine = self.prochaine_maintenance_calculee
        if not prochaine:
            return False
        return datetime.utcnow() > prochaine

    @property
    def nb_interventions_total(self) -> int:
        """Nombre total d'interventions sur cet équipement."""
        return self.interventions.count()

    @property
    def nb_interventions_correctives(self) -> int:
        """Nombre d'interventions correctives."""
        return self.interventions.filter_by(type_intervention="corrective").count()

    @property
    def nb_interventions_preventives(self) -> int:
        """Nombre d'interventions préventives."""
        return self.interventions.filter_by(type_intervention="preventive").count()

    @property
    def taux_pannes_annuel(self) -> Optional[float]:
        """Calcule le taux de pannes par an (interventions correctives/âge)."""
        if not self.age_en_annees or self.age_en_annees == 0:
            return None
        return round(self.nb_interventions_correctives / self.age_en_annees, 2)

    @property
    def cout_maintenance_total(self) -> float:
        """Calcule le coût total des maintenances réalisées."""
        total = 0.0
        for intervention in self.interventions:
            if intervention.cout_reel:
                total += float(intervention.cout_reel) / 100  # Conversion centimes -> euros
        return round(total, 2)

    @property
    def derniere_intervention(self) -> Optional["Intervention"]:
        """Retourne la dernière intervention effectuée."""
        return self.interventions.first()

    @property
    def derniere_intervention_date(self) -> Optional[datetime]:
        """Date de la dernière intervention."""
        derniere = self.derniere_intervention
        return derniere.date_cloture or derniere.date_creation if derniere else None

    @property
    def temps_depuis_derniere_intervention(self) -> Optional[timedelta]:
        """Temps écoulé depuis la dernière intervention."""
        if not self.derniere_intervention_date:
            return None
        return datetime.utcnow() - self.derniere_intervention_date

    @property
    def niveau_criticite_numerique(self) -> int:
        """Convertit la criticité en valeur numérique pour tri/calculs."""
        mapping = {
            CriticiteEquipement.critique: 4,
            CriticiteEquipement.important: 3,
            CriticiteEquipement.standard: 2,
            CriticiteEquipement.non_critique: 1
        }
        return mapping.get(self.criticite, 0)

    @property
    def identificateur_complet(self) -> str:
        """Retourne l'identificateur complet le plus approprié."""
        if self.numero_serie:
            return f"{self.nom} (S/N: {self.numero_serie})"
        elif self.code_interne:
            return f"{self.nom} ({self.code_interne})"
        else:
            return self.nom

    @property
    def localisation_complete(self) -> str:
        """Retourne la localisation complète formatée."""
        parts = [self.localisation]
        if self.batiment:
            parts.append(f"Bât. {self.batiment}")
        if self.etage:
            parts.append(f"Étage {self.etage}")
        if self.zone:
            parts.append(f"Zone {self.zone}")
        return " - ".join(parts)

    # 🔧 Méthodes métier pour gestion équipement

    def mettre_en_panne(self, raison: str = None) -> None:
        """Passe l'équipement en statut panne."""
        self.statut = StatutEquipement.panne
        self.updated_at = datetime.utcnow()

    def mettre_en_maintenance(self) -> None:
        """Passe l'équipement en statut maintenance."""
        self.statut = StatutEquipement.maintenance
        self.updated_at = datetime.utcnow()

    def remettre_en_service(self) -> None:
        """Remet l'équipement en service opérationnel."""
        self.statut = StatutEquipement.operationnel
        self.updated_at = datetime.utcnow()

    def retirer_du_service(self) -> None:
        """Retire définitivement l'équipement du service."""
        self.statut = StatutEquipement.retire
        self.updated_at = datetime.utcnow()

    def calculer_date_fin_garantie(self) -> None:
        """Calcule et met à jour la date de fin de garantie."""
        if self.date_acquisition and self.duree_garantie_mois:
            self.date_fin_garantie = self.date_acquisition + timedelta(
                days=self.duree_garantie_mois * 30.44  # Moyenne jours/mois
            )

    def programmer_maintenance_preventive(self) -> Optional[datetime]:
        """
        Retourne la date recommandée pour programmer la prochaine maintenance.
        
        Returns:
            datetime: Date recommandée ou None si pas de cycle défini
        """
        if not self.frequence_entretien_jours:
            return None
            
        prochaine = self.prochaine_maintenance_calculee
        if not prochaine:
            return None
            
        # Ajouter une marge de sécurité pour les équipements critiques
        if self.est_critique:
            prochaine -= timedelta(days=7)  # 1 semaine d'avance
            
        return prochaine

    def get_historique_pannes(self) -> List["Intervention"]:
        """Retourne l'historique des pannes (interventions correctives)."""
        return list(self.interventions.filter_by(type_intervention="corrective").all())

    def get_planning_maintenance(self) -> List["Planning"]:
        """Retourne les maintenances planifiées à venir."""
        return list(self.plannings.filter(
            Planning.prochaine_date >= datetime.utcnow()
        ).all())

    def peut_etre_supprime(self) -> bool:
        """Vérifie si l'équipement peut être supprimé du système."""
        # Ne peut pas supprimer s'il y a des interventions en cours
        interventions_actives = self.interventions.filter(
            Intervention.statut.in_(["ouverte", "affectee", "en_cours"])
        ).count()
        
        return interventions_actives == 0 and self.statut == StatutEquipement.retire

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        """
        Sérialisation harmonisée en dictionnaire.
        
        Args:
            include_sensitive: Inclut données sensibles/coûts (admin/responsable)
            include_relations: Inclut les données des relations liées
            
        Returns:
            Dict contenant les données sérialisées
            
        NOTE: Interface standardisée pour tous les modèles ERP
        """
        # Données de base (toujours incluses)
        data = {
            "id": self.id,
            "nom": self.nom,
            "numero_serie": self.numero_serie,
            "code_interne": self.code_interne,
            "type_equipement": self.type_equipement,
            "marque": self.marque,
            "modele": self.modele,
            "localisation": self.localisation,
            "localisation_complete": self.localisation_complete,
            "statut": self.statut.value,
            "criticite": self.criticite.value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            
            # Propriétés calculées utiles
            "identificateur_complet": self.identificateur_complet,
            "est_operationnel": self.est_operationnel,
            "est_en_panne": self.est_en_panne,
            "est_critique": self.est_critique,
            "est_sous_garantie": self.est_sous_garantie,
            "age_en_jours": self.age_en_jours,
            "age_en_annees": self.age_en_annees,
            "maintenance_en_retard": self.maintenance_en_retard,
            "nb_interventions_total": self.nb_interventions_total,
            "derniere_intervention_date": self.derniere_intervention_date.isoformat() if self.derniere_intervention_date else None,
        }
        
        # Données sensibles (coûts, détails techniques)
        if include_sensitive:
            data.update({
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "specifications_techniques": self.specifications_techniques,
                "puissance": float(self.puissance) if self.puissance else None,
                "poids": float(self.poids) if self.poids else None,
                "cout_acquisition": float(self.cout_acquisition) / 100 if self.cout_acquisition else None,
                "date_acquisition": self.date_acquisition.isoformat() if self.date_acquisition else None,
                "date_mise_en_service": self.date_mise_en_service.isoformat() if self.date_mise_en_service else None,
                "date_fin_garantie": self.date_fin_garantie.isoformat() if self.date_fin_garantie else None,
                "frequence_entretien_jours": self.frequence_entretien_jours,
                "duree_garantie_mois": self.duree_garantie_mois,
                
                # KPI de maintenance
                "prochaine_maintenance_calculee": self.prochaine_maintenance_calculee.isoformat() if self.prochaine_maintenance_calculee else None,
                "nb_interventions_correctives": self.nb_interventions_correctives,
                "nb_interventions_preventives": self.nb_interventions_preventives,
                "taux_pannes_annuel": self.taux_pannes_annuel,
                "cout_maintenance_total": self.cout_maintenance_total,
                "niveau_criticite_numerique": self.niveau_criticite_numerique,
            })
        
        # Relations détaillées (pour vues complètes)
        if include_relations:
            data.update({
                "client": self.client.to_dict() if self.client else None,
                "contrat": self.contrat.to_dict() if self.contrat else None,
                "client_id": self.client_id,
                "contrat_id": self.contrat_id,
                
                # Historique récent
                "derniere_intervention": self.derniere_intervention.to_dict() if self.derniere_intervention else None,
                "planning_maintenance": [p.to_dict() for p in self.get_planning_maintenance()[:5]],  # 5 prochaines
                
                # Métadonnées système
                "peut_etre_supprime": self.peut_etre_supprime(),
                "batiment": self.batiment,
                "etage": self.etage,
                "zone": self.zone,
            })
            
        return data
