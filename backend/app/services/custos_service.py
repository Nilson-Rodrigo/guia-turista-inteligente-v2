import math
from typing import Any


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
