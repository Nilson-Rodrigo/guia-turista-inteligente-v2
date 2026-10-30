from typing import Any

import httpx


async def buscar_coordenadas(
    client: httpx.AsyncClient,
    cidade: str,
    uf: str,
) -> dict[str, Any]:
    fallback = {"latitude": 0.0, "longitude": 0.0, "nome": f"{cidade} - {uf}"}
    try:
        response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": cidade,
                "count": 10,
                "language": "pt",
                "format": "json",
                "countryCode": "BR",
            },
        )
        response.raise_for_status()
        resultados = response.json().get("results", [])
        resultado = next(
            (
                item
                for item in resultados
                if str(item.get("admin1", "")).upper() == uf
                or str(item.get("admin1", "")).lower() == uf.lower()
            ),
            resultados[0] if resultados else None,
        )
        if not resultado:
            return fallback
        return {
            "latitude": float(resultado["latitude"]),
            "longitude": float(resultado["longitude"]),
            "nome": f"{resultado.get('name', cidade)} - {uf}",
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return fallback


async def obter_clima(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
) -> dict[str, str]:
    fallback = {"temperatura": "N/D", "umidade": "N/D", "vento": "N/D"}
    if latitude == 0.0 and longitude == 0.0:
        return fallback
    try:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        current = response.json()["current"]
        units = response.json().get("current_units", {})
        return {
            "temperatura": f"{current['temperature_2m']} {units.get('temperature_2m', '°C')}",
            "umidade": f"{current['relative_humidity_2m']} {units.get('relative_humidity_2m', '%')}",
            "vento": f"{current['wind_speed_10m']} {units.get('wind_speed_10m', 'km/h')}",
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return fallback


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
