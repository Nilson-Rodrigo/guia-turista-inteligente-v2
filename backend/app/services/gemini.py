import asyncio
from collections.abc import AsyncIterator


def _fallback_text(destino: str, dias: int, estilo: str) -> str:
    return (
        f"{destino} combina história, sabores regionais e paisagens para uma viagem {estilo.lower()}.\n\n"
        f"Roteiro de {dias} dias: Manhã: visite o centro histórico e observe a arquitetura local.\n"
        "Tarde: experimente dois pratos regionais em um mercado tradicional.\n"
        "Noite: escolha um passeio cultural tranquilo e reserve energia para o dia seguinte.\n\n"
        "Clima e prática: confirme a previsão antes de sair, use roupas leves e mantenha água na mochila."
    )


async def gerar_guia_stream(
    destino: str,
    dias: int,
    estilo: str,
    api_key: str = "",
) -> AsyncIterator[str]:
    """Transmite o guia em pequenos fragmentos, com fallback determinístico."""
    del api_key
    texto = _fallback_text(destino, dias, estilo)
    for fragmento in texto.split(" "):
        yield f"data: {fragmento} \n\n"
        await asyncio.sleep(0.015)
    yield "event: done\ndata: [DONE]\n\n"
