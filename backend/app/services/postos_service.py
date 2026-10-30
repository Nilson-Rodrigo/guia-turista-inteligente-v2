import math


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
