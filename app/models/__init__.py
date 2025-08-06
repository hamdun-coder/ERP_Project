# app/models/__init__.py
"""
Package models - Modèles de données ORM SQLAlchemy.

Ce package contient tous les modèles de données de l'ERP de maintenance :
- Architecture SQLAlchemy 2.x avec types Python modernes
- Relations ORM optimisées avec cascade appropriée
- Propriétés calculées pour KPI métier temps réel
- Interface to_dict() harmonisée pour sérialisation API
- Index de performance sur requêtes fréquentes
- Enums typés pour états et classifications métier

Organisation des modèles :
- User/Technicien/Client : Gestion utilisateurs et authentification
- Equipement/Intervention : Cœur métier maintenance industrielle  
- Planning/Notification : Orchestration et communication
- Document/Historique : Traçabilité et audit complet
- Stock/Contrat : Gestion économique et commerciale
- Report : Business Intelligence et reporting

NOTE: Tous les modèles suivent les conventions d'excellence :
- Docstrings métier complètes avec architecture
- Propriétés calculées pour logique applicative
- Méthodes métier pour workflows complexes
- Type hints complets pour IDE/mypy
- Cascade et contraintes d'intégrité robustes
"""

# Modèles utilisateurs et authentification
from .user import User, UserRole

# Modèles techniciens et compétences  
from .technicien import (
    Technicien, 
    Competence, 
    technicien_competence,
    DisponibiliteTechnicien,
    NiveauCompetence
)

# Modèles clients et relations commerciales
from .client import Client, TypeClient, NiveauService

# Modèles équipements et patrimoine
from .equipement import (
    Equipement, 
    StatutEquipement, 
    CriticiteEquipement
)

# Modèles interventions - cœur métier
from .intervention import (
    Intervention,
    InterventionType,
    StatutIntervention,
    PrioriteIntervention
)
from .intervention_equipement import InterventionEquipement

# Modèles planification et organisation
from .planning import Planning

# Modèles documentation et fichiers
from .document import Document

# Modèles notification et communication
from .notification import Notification

# Modèles audit et traçabilité
from .historique import HistoriqueIntervention
from .audit import Audit

# Modèles contractuels et commerciaux
from .contrat import Contrat, Facture, TypeContrat, StatutContrat

# Modèles stock et logistique
from .stock import (
    PieceDetachee, 
    MouvementStock, 
    InterventionPiece, 
    TypeMouvement
)

# Modèles reporting et business intelligence
from .report import (
    Report, 
    ReportSchedule, 
    ReportStatus, 
    ReportType, 
    ReportFormat
)

# Export des classes principales pour utilisation externe
__all__ = [
    # Authentification et utilisateurs
    "User", "UserRole",
    
    # Personnel technique
    "Technicien", "Competence", "technicien_competence",
    "DisponibiliteTechnicien", "NiveauCompetence",
    
    # Clients et commercial
    "Client", "TypeClient", "NiveauService",
    
    # Patrimoine technique
    "Equipement", "StatutEquipement", "CriticiteEquipement",
    
    # Interventions - métier principal
    "Intervention", "InterventionType", "StatutIntervention", "PrioriteIntervention",
    "InterventionEquipement",
    
    # Organisation et planification
    "Planning",
    
    # Documentation
    "Document",
    
    # Communication
    "Notification", 
    
    # Audit et traçabilité
    "HistoriqueIntervention", "Audit",
    
    # Commercial et contrats
    "Contrat", "Facture", "TypeContrat", "StatutContrat",
    
    # Logistique et stock
    "PieceDetachee", "MouvementStock", "InterventionPiece", "TypeMouvement",
    
    # Business Intelligence
    "Report", "ReportSchedule", "ReportStatus", "ReportType", "ReportFormat"
]
