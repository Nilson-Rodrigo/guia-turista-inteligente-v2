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
        return {**calcular_perfil([]), "disponivel": False}
    from ..core.circuit_breaker import providers_breakers
    circuito = providers_breakers["elevation"]
    if circuito.state == "open": return {**calcular_perfil([]), "disponivel": False}
    amostras = [coordenadas[round(i * (len(coordenadas)-1) / 19)] for i in range(20)] if len(coordenadas)>20 else coordenadas
    latitudes = ",".join(str(latitude) for _, latitude in amostras)
    longitudes = ",".join(str(longitude) for longitude, _ in amostras)
    try:
        response = await client.get(
            "https://api.open-meteo.com/v1/elevation",
            params={"latitude": latitudes, "longitude": longitudes},
        )
        response.raise_for_status()
        elevations = [float(value) for value in response.json()["elevation"]]
        if len(elevations) != len(amostras):
            raise ValueError("O serviço retornou quantidade inesperada de elevações")
        circuito.record_success()
        return {**calcular_perfil(elevations), "disponivel": True}
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        circuito.record_failure()
        return {**calcular_perfil([]), "disponivel": False}
