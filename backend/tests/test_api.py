import backend.app.services.storage as storage
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_planejar_normaliza_uf(client: TestClient) -> None:
    response = client.post(
        "/api/v1/roteiros/planejar",
        json={
            "origem_cidade": "Recife",
            "origem_uf": "pe",
            "destino_cidade": "Salvador",
            "destino_uf": "ba",
        },
    )

    assert response.status_code == 200
    assert response.json()["origem"] == "Recife - PE"
    assert response.json()["destino"] == "Salvador - BA"


def test_planejar_rejeita_uf_invalida(client: TestClient) -> None:
    response = client.post(
        "/api/v1/roteiros/planejar",
        json={
            "origem_cidade": "Recife",
            "origem_uf": "P",
            "destino_cidade": "Salvador",
            "destino_uf": "BA",
        },
    )

    assert response.status_code == 422


def test_visitante_planeja_e_consulta_historico(client: TestClient, monkeypatch) -> None:
    temporary_file = storage.DATA_FILE.parent / "test_viagens.json"
    monkeypatch.setattr(storage, "DATA_FILE", temporary_file)

    login = client.post("/api/v1/auth/demo")
    user_id = login.json()["usuario"]["id"]
    response = client.post(
        "/api/v1/roteiros/planejar",
        headers={"X-User-Id": user_id},
        json={
            "origem_cidade": "Recife",
            "origem_uf": "PE",
            "destino_cidade": "Salvador",
            "destino_uf": "BA",
        },
    )

    assert response.status_code == 200
    roteiro_id = response.json()["id"]
    historico = client.get("/api/v1/roteiros", headers={"X-User-Id": user_id})
    assert historico.status_code == 200
    assert historico.json()[0]["id"] == roteiro_id

    deleted = client.delete(
        f"/api/v1/roteiros/{roteiro_id}", headers={"X-User-Id": user_id}
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/roteiros", headers={"X-User-Id": user_id}).json() == []

    temporary_file.unlink(missing_ok=True)
