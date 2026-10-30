from typing import Any

import httpx


def calcular_perfil(elevations: list[float]) -> dict[str, Any]:
    if not elevations:
        return {
            "altitude_minima_m": 0,
            "altitude_maxima_m": 0,
            "ganho_subida_m": 0,
            "perda_descida_m": 0,
            "desnivel_liquido_m": 0,
            "penalizacao_consumo_percentual": 0,
            "elevacoes_m": [],
        }
    subida = sum(max(0, atual - anterior) for anterior, atual in zip(elevations, elevations[1:]))
    descida = sum(max(0, anterior - atual) for anterior, atual in zip(elevations, elevations[1:]))
    penalizacao = min(25.0, subida / 1000 * 4)
    return {
        "altitude_minima_m": round(min(elevations), 1),
        "altitude_maxima_m": round(max(elevations), 1),
        "ganho_subida_m": round(subida, 1),
        "perda_descida_m": round(descida, 1),
        "desnivel_liquido_m": round(elevations[-1] - elevations[0], 1),
        "penalizacao_consumo_percentual": round(penalizacao, 2),
        "elevacoes_m": [round(value, 1) for value in elevations],
    }


async def obter_altimetria(
    client: httpx.AsyncClient,
    coordenadas: list[list[float]],
) -> dict[str, Any]:
    if not coordenadas:
        return calcular_perfil([])
    amostras = coordenadas[:: max(1, len(coordenadas) // 20)][:20]
    locations = ",".join(f"{latitude},{longitude}" for longitude, latitude in amostras)
    try:
        response = await client.get(
            "https://api.open-elevation.com/api/v1/lookup",
            params={"locations": locations},
        )
        response.raise_for_status()
        elevations = [float(item["elevation"]) for item in response.json()["results"]]
        return calcular_perfil(elevations)
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return calcular_perfil([])
