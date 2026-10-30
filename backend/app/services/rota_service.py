from typing import Any

import httpx
from fastapi import HTTPException

from ..core.circuit_breaker import providers_breakers
from .clima_service import proteger
from .postos_service import sugerir_paradas


async def obter_percurso(
    client: httpx.AsyncClient,
    origem: dict[str, Any],
    destino: dict[str, Any],
) -> dict[str, str]:
    fallback = {"distancia": "Sem rota direta", "tempo": "N/D"}
    if origem["latitude"] == 0.0 or destino["latitude"] == 0.0:
        return fallback
    try:
        url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{origem['longitude']},{origem['latitude']};"
            f"{destino['longitude']},{destino['latitude']}"
        )
        response = await client.get(url, params={"overview": "false"})
        response.raise_for_status()
        route = response.json()["routes"][0]
        distancia_km = route["distance"] / 1000
        minutos = round(route["duration"] / 60)
        horas, minutos_restantes = divmod(minutos, 60)
        tempo = f"{horas}h {minutos_restantes}min" if horas else f"{minutos}min"
        return {"distancia": f"{distancia_km:.1f} km", "tempo": tempo}
    except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
        return fallback


obter_percurso = proteger("routing", obter_percurso)


async def obter_rota_com_geometria(
    client: httpx.AsyncClient,
    payload: Any,
) -> dict[str, Any]:
    circuito = providers_breakers["routing"]
    fallback = {
        "distancia_km": 0,
        "duracao_minutos": 0,
        "geometria": [],
        "rotas_alternativas": [],
        "paradas": sugerir_paradas(0, payload.autonomia_km, payload.margem_seguranca),
        "altimetria": {},
    }
    if circuito.state == "open":
        return fallback
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
            "paradas": sugerir_paradas(
                distancia, payload.autonomia_km, payload.margem_seguranca
            ),
            "altimetria": {},
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        circuito.record_failure()
        return fallback
