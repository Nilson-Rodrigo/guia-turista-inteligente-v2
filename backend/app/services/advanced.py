import math
from typing import Any

import httpx


def calcular_custos(data: Any) -> dict[str, float | int | str]:
    if data.propulsao == "eletrico":
        energia = data.distancia_km / data.eficiencia_kwh
        autonomia = data.capacidade_bateria * data.eficiencia_kwh
        custo_energia = energia * data.preco_kwh
        propulsao = "100% elétrico"
    else:
        energia = data.distancia_km / data.consumo_medio
        autonomia = data.capacidade_tanque * data.consumo_medio
        custo_energia = energia * data.preco_combustivel
        propulsao = "combustão"
    fator = 1 + data.penalizacao_percentual / 100
    energia *= fator
    custo_energia *= fator
    autonomia /= fator
    total = custo_energia + data.pedagios
    return {
        "propulsao": propulsao,
        "energia_consumida": round(energia, 2),
        "custo_energia": round(custo_energia, 2),
        "pedagios": round(data.pedagios, 2),
        "custo_total": round(total, 2),
        "custo_por_passageiro": round(total / data.passageiros, 2),
        "autonomia_por_carga": round(autonomia, 2),
        "cargas_ou_abastecimentos": max(0, math.ceil(data.distancia_km / autonomia) - 1),
    }


def sugerir_paradas(
    distancia_km: float,
    autonomia_km: float,
    margem_seguranca: float,
) -> list[dict[str, float | str]]:
    intervalo = autonomia_km * (1 - margem_seguranca)
    if distancia_km <= intervalo:
        return []
    quantidade = math.ceil(distancia_km / intervalo) - 1
    return [
        {
            "progresso_km": round(min(intervalo * (index + 1), distancia_km), 1),
            "tipo": "abastecimento ou recarga",
        }
        for index in range(quantidade)
    ]


async def obter_rota_com_geometria(
    client: httpx.AsyncClient,
    payload: Any,
) -> dict[str, Any]:
    from ..core.circuit_breaker import providers_breakers
    circuito = providers_breakers["routing"]
    fallback = {
        "distancia_km": 0,
        "duracao_minutos": 0,
        "geometria": [],
        "rotas_alternativas": [],
        "paradas": sugerir_paradas(0, payload.autonomia_km, payload.margem_seguranca),
        "altimetria": {},
    }
    if circuito.state == "open": return fallback
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{payload.origem_longitude},{payload.origem_latitude};"
        f"{payload.destino_longitude},{payload.destino_latitude}"
    )
    try:
        response = await client.get(
            url,
            params={"overview": "full", "geometries": "geojson", "alternatives": "true"},
        )
        response.raise_for_status()
        routes = response.json().get("routes", [])
        if not routes:
            return fallback
        circuito.record_success()
        principal = routes[0]
        distancia = principal["distance"] / 1000
        return {
            "distancia_km": round(distancia, 2),
            "duracao_minutos": round(principal["duration"] / 60),
            "geometria": principal.get("geometry", {}).get("coordinates", []),
            "rotas_alternativas": [
                {
                    "distancia_km": round(route["distance"] / 1000, 2),
                    "duracao_minutos": round(route["duration"] / 60),
                    "geometria": route.get("geometry", {}).get("coordinates", []),
                }
                for route in routes[1:]
            ],
            "paradas": sugerir_paradas(distancia, payload.autonomia_km, payload.margem_seguranca),
            "altimetria": {},
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        circuito.record_failure()
        return fallback
