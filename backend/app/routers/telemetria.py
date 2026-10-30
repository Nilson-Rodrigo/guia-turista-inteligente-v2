from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..core.circuit_breaker import providers_breakers
from ..core.concurrency import active_requests
from ..services.storage import DATA_FILE, _read

router = APIRouter(prefix="/api/v1/telemetria", tags=["Telemetria"])


@router.get("/resumo")
async def resumo_telemetria() -> dict[str, int | str]:
    data = _read()
    total = int(data.get("total_roteiros", 0))
    return {
        "roteiros_gerados": total,
        "conexoes_ativas": len(active_requests),
        "arquivo_persistencia": str(DATA_FILE),
        "status": "operacional",
        "circuitos": {name: breaker.state for name, breaker in providers_breakers.items()},
    }


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics() -> str:
    data = _read()
    total = int(data.get("total_roteiros", 0))
    lines = [
        "# HELP guia_roteiros_gerados Total de roteiros persistidos.",
        "# TYPE guia_roteiros_gerados counter",
        f"guia_roteiros_gerados {total}",
    ]
    for name, breaker in providers_breakers.items():
        lines.extend([
            f"# TYPE guia_circuit_breaker_{name} gauge",
            f"guia_circuit_breaker_{name} {1 if breaker.state == 'open' else 0}",
        ])
    return "\n".join(lines) + "\n"
