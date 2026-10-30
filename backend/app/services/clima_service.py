from typing import Any
import unicodedata

import httpx
from fastapi import HTTPException

from ..core.circuit_breaker import providers_breakers


async def buscar_coordenadas(
    client: httpx.AsyncClient,
    cidade: str,
    uf: str,
) -> dict[str, Any]:
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
        estados = dict(zip("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(), ["Acre","Alagoas","Amapá","Amazonas","Bahia","Ceará","Distrito Federal","Espírito Santo","Goiás","Maranhão","Mato Grosso","Mato Grosso do Sul","Minas Gerais","Pará","Paraíba","Paraná","Pernambuco","Piauí","Rio de Janeiro","Rio Grande do Norte","Rio Grande do Sul","Rondônia","Roraima","Santa Catarina","São Paulo","Sergipe","Tocantins"]))

        def norm(text):
            return "".join(
                character
                for character in unicodedata.normalize("NFD", text.lower())
                if unicodedata.category(character) != "Mn"
            )

        resultado = next(
            (
                item
                for item in resultados
                if norm(str(item.get("admin1", "")))
                in [norm(uf), norm(estados[uf])]
            ),
            None,
        )
        if not resultado:
            raise HTTPException(422, "Cidade não localizada na UF informada")
        return {
            "latitude": float(resultado["latitude"]),
            "longitude": float(resultado["longitude"]),
            "nome": f"{resultado.get('name', cidade)} - {uf}",
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise HTTPException(503, "Geocodificação indisponível; tente novamente")


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
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m",
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        current = response.json()["current"]
        units = response.json().get("current_units", {})
        return {
            "temperatura": f"{current['temperature_2m']} {units.get('temperature_2m', '°C')}",
            "sensacao": str(current.get("apparent_temperature", "N/D")) + " °C",
            "umidade": f"{current['relative_humidity_2m']} {units.get('relative_humidity_2m', '%')}",
            "vento": f"{current['wind_speed_10m']} {units.get('wind_speed_10m', 'km/h')}",
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return fallback


def proteger(nome, func):
    async def chamada(*args, **kwargs):
        circuito = providers_breakers[nome]
        if circuito.state == "open":
            raise HTTPException(503, f"Serviço {nome} temporariamente indisponível")
        try:
            resultado = await func(*args, **kwargs)
            falhou = (
                resultado.get("temperatura") == "N/D"
                or resultado.get("tempo") == "N/D"
            )
            if falhou:
                circuito.record_failure()
            else:
                circuito.record_success()
            return resultado
        except Exception:
            circuito.record_failure()
            raise

    return chamada


buscar_coordenadas = proteger("geocoding", buscar_coordenadas)
obter_clima = proteger("weather", obter_clima)
