from filelock import FileLock
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
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_lock = FileLock(str(DATA_FILE)+".lock", thread_local=False)
        await asyncio.to_thread(file_lock.acquire)
        try:
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


        finally:
            await asyncio.to_thread(file_lock.release)

async def listar_roteiros(user_id: str) -> list[dict[str, Any]]:
    async with _storage_lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_lock = FileLock(str(DATA_FILE)+".lock", thread_local=False)
        await asyncio.to_thread(file_lock.acquire)
        try:
            data = await asyncio.to_thread(_read)
            return list(data.get("usuarios", {}).get(user_id, {}).get("roteiros", []))


        finally:
            await asyncio.to_thread(file_lock.release)

async def remover_roteiro(user_id: str, roteiro_id: str) -> bool:
    async with _storage_lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_lock = FileLock(str(DATA_FILE)+".lock", thread_local=False)
        await asyncio.to_thread(file_lock.acquire)
        try:
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

        finally:
            await asyncio.to_thread(file_lock.release)

async def atualizar_visitas(user_id, roteiro_id, visitas):
    async with _storage_lock:
        def change():
            with FileLock(str(DATA_FILE)+".lock", thread_local=False):
                data = _read()
                for item in data.get("usuarios",{}).get(user_id,{}).get("roteiros",[]):
                    if item["id"] == roteiro_id:
                        validos = {a["id"] for a in item.get("atrativos",[])}
                        item["visitas"] = [v for v in visitas if v in validos]
                        _write(data)
                        return item
                return None
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        return await asyncio.to_thread(change)
