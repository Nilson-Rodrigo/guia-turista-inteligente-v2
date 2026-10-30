import asyncio
import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).resolve().parents[3] / "static" / "data" / "viagens.json"
_storage_lock = asyncio.Lock()


def _empty_data() -> dict[str, Any]:
    return {
        "versao_schema": "2.0",
        "atualizado_em": None,
        "total_usuarios": 0,
        "total_roteiros": 0,
        "usuarios": {},
    }


def _read() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return _empty_data()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else _empty_data()
    except (OSError, json.JSONDecodeError):
        return _empty_data()


def _write(data: dict[str, Any]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    temporary_file.replace(DATA_FILE)


async def salvar_roteiro(user_id: str, roteiro: dict[str, Any]) -> None:
    async with _storage_lock:
        data = await asyncio.to_thread(_read)
        usuarios = data.setdefault("usuarios", {})
        usuario = usuarios.setdefault(user_id, {"roteiros": []})
        usuario.setdefault("roteiros", []).append(roteiro)
        data["total_usuarios"] = len(usuarios)
        data["total_roteiros"] = sum(
            len(usuario_data.get("roteiros", []))
            for usuario_data in usuarios.values()
        )
        await asyncio.to_thread(_write, data)


async def listar_roteiros(user_id: str) -> list[dict[str, Any]]:
    async with _storage_lock:
        data = await asyncio.to_thread(_read)
        return list(data.get("usuarios", {}).get(user_id, {}).get("roteiros", []))


async def remover_roteiro(user_id: str, roteiro_id: str) -> bool:
    async with _storage_lock:
        data = await asyncio.to_thread(_read)
        usuario = data.get("usuarios", {}).get(user_id, {})
        roteiros = usuario.get("roteiros", [])
        restantes = [roteiro for roteiro in roteiros if roteiro.get("id") != roteiro_id]
        if len(restantes) == len(roteiros):
            return False
        usuario["roteiros"] = restantes
        data["total_roteiros"] = sum(
            len(item.get("roteiros", [])) for item in data.get("usuarios", {}).values()
        )
        await asyncio.to_thread(_write, data)
        return True
