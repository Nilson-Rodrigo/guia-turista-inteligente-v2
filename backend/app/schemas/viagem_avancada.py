from typing import Annotated, Literal

from pydantic import BaseModel, Field


Positive = Annotated[float, Field(gt=0)]


class MapaRotaRequest(BaseModel):
    origem_latitude: float = Field(ge=-90, le=90)
    origem_longitude: float = Field(ge=-180, le=180)
    destino_latitude: float = Field(ge=-90, le=90)
    destino_longitude: float = Field(ge=-180, le=180)
    autonomia_km: Positive = 500
    margem_seguranca: Annotated[float, Field(ge=0.05, le=0.5)] = 0.18


class CustosRequest(BaseModel):
    distancia_km: Positive
    propulsao: Literal["combustao", "eletrico"] = "combustao"
    consumo_medio: Positive = 12
    capacidade_tanque: Positive = 50
    preco_combustivel: Positive = 6
    eficiencia_kwh: Positive = 6
    capacidade_bateria: Positive = 60
    preco_kwh: Positive = 1
    pedagios: Annotated[float, Field(ge=0)] = 0
    passageiros: Annotated[int, Field(ge=1, le=8)] = 1


class CustosResponse(BaseModel):
    propulsao: str
    energia_consumida: float
    custo_energia: float
    pedagios: float
    custo_total: float
    custo_por_passageiro: float
    autonomia_por_carga: float
    cargas_ou_abastecimentos: int
