import pytest


@pytest.fixture()
def equipement(client, responsable_token):
    """Crée un équipement pour les besoins des tests."""
    headers = {"Authorization": f"Bearer {responsable_token}"}
    payload = {
        "nom": "Machine Audit",
        "type": "électrique",
        "localisation": "Atelier B",
        "frequence_entretien": "30",
    }
    response = client.post("/api/v1/equipements/", json=payload, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_historique_intervention(client, responsable_token, technicien_token, equipement):
    """Vérifie que les historiques sont créés et récupérés correctement."""
    headers_resp = {"Authorization": f"Bearer {responsable_token}"}
    payload = {
        "titre": "Intervention historisée",
        "description": "Test historique",
        "type": "corrective",
        "statut": "ouverte",
        "urgence": False,
        "equipement_id": equipement["id"],
    }
    # Création intervention
    resp = client.post("/api/v1/interventions/", json=payload, headers=headers_resp)
    assert resp.status_code == 200
    intervention_id = resp.json()["id"]

    # Vérifie historique initial (création)
    hist_resp = client.get(
        f"/api/v1/interventions/{intervention_id}/historique",
        headers=headers_resp,
    )
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert len(hist_data) == 1
    assert hist_data[0]["statut"] == "ouverte"

    # Mise à jour du statut -> nouvel historique
    headers_tech = {"Authorization": f"Bearer {technicien_token}"}
    resp_patch = client.patch(
        f"/api/v1/interventions/{intervention_id}/statut",
        params={"statut": "en_cours", "remarque": "Début"},
        headers=headers_tech,
    )
    assert resp_patch.status_code == 200

    hist_resp = client.get(
        f"/api/v1/interventions/{intervention_id}/historique",
        headers=headers_resp,
    )
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert len(hist_data) == 2
    assert hist_data[1]["statut"] == "en_cours"
