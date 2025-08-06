from app.models import (
    Audit,
    Intervention,
    InterventionEquipement,
    InterventionType,
    User,
    UserRole,
    Equipement,
)


def test_audit_relation(db_session):
    user = User(
        username="auditor",
        full_name="Auditor",
        email="audit@example.com",
        hashed_password="x",
        role=UserRole.admin,
    )
    db_session.add(user)
    db_session.commit()

    audit = Audit(action="create", table_name="users", object_id=user.id, user=user)
    db_session.add(audit)
    db_session.commit()

    assert audit.user_id == user.id
    assert audit.user.username == "auditor"


def test_intervention_equipement_link(db_session):
    equip_principal = Equipement(nom="E1", type_equipement="T1", localisation="Site")
    equip_second = Equipement(nom="E2", type_equipement="T2", localisation="Site")
    db_session.add_all([equip_principal, equip_second])
    db_session.flush()

    intervention = Intervention(
        titre="Test",
        description="",
        type_intervention=InterventionType.corrective,
        equipement_id=equip_principal.id,
    )
    link = InterventionEquipement(intervention=intervention, equipement=equip_second)
    db_session.add_all([intervention, link])
    db_session.commit()

    assert link.intervention_id == intervention.id
    assert link.equipement_id == equip_second.id
    assert intervention.equipements_assoc.count() == 1
    assert equip_second.interventions_assoc.count() == 1

