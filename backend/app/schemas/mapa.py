from typing import Any

from pydantic import BaseModel


class MapaRotaResponse(BaseModel):
    distancia_km: float
    duracao_minutos: int
    geometria: list[list[float]]
    rotas_alternativas: list[dict[str, float]]
    paradas: list[dict[str, Any]]
    altimetria: dict[str, Any]
