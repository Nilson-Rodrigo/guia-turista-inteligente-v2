from typing import Any


def criar_link_compartilhamento(roteiro: dict[str, Any], canal: str) -> str:
    origem = str(roteiro.get("origem", "Origem"))
    destino = str(roteiro.get("destino", "Destino"))
    mensagem = f"Meu roteiro: {origem} -> {destino}"
    if canal == "whatsapp":
        import urllib.parse

        return "https://wa.me/?text=" + urllib.parse.quote(mensagem)
    return mensagem
