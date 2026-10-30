from uuid import uuid4

import asyncio
import hashlib

import httpx
from fastapi import Depends, APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.responses import Response

from ..core.concurrency import active_requests, request_lock
from ..core.config import get_settings
from ..core.session import get_session
from ..schemas.guia import GuiaStreamRequest
from ..schemas.mapa import MapaRotaResponse
from ..schemas.viagem_avancada import CustosRequest, CustosResponse, MapaRotaRequest
from ..schemas.roteiros import RoteiroRequest, RoteiroResponse
from ..services.custos_service import calcular_custos
from ..services.altimetria_service import obter_altimetria
from ..services.gemini_service import gerar_guia_stream
from ..services.gpx_service import gerar_gpx
from ..services.clima_service import buscar_coordenadas, obter_clima
from ..services.rota_service import obter_percurso, obter_rota_com_geometria
from ..services.share import criar_link_compartilhamento
from ..services.storage_service import listar_roteiros, remover_roteiro, salvar_roteiro

from ..core.dependencies import obter_usuario, obter_http_client
from ..core.catalogo import catalogo, DESTINOS

router = APIRouter(dependencies=[Depends(obter_usuario)], prefix="/api/v1/roteiros", tags=["Roteiros"])


@router.post("/compartilhar", summary="Cria um link de compartilhamento")
async def compartilhar(payload: dict[str, object], background_tasks: BackgroundTasks) -> dict[str, str]:
    canal = str(payload.get("canal", "whatsapp"))
    roteiro = payload.get("roteiro", {})
    if not isinstance(roteiro, dict):
        raise HTTPException(status_code=422, detail="roteiro deve ser um objeto")
    import logging
    background_tasks.add_task(logging.getLogger("compartilhamento").info, "Link preparado para canal %s", canal)
    return {"canal": canal, "link": criar_link_compartilhamento(roteiro, canal)}


@router.post("/exportar/gpx", summary="Exporta a geometria como GPX 1.1")
async def exportar_gpx(payload: dict[str, object]) -> Response:
    geometria = payload.get("geometria", [])
    if not isinstance(geometria, list):
        raise HTTPException(status_code=422, detail="geometria deve ser uma lista")
    if not geometria or not all(isinstance(pt,list) and len(pt)==2 and all(isinstance(v,(int,float)) for v in pt) and -180<=pt[0]<=180 and -90<=pt[1]<=90 for pt in geometria):
        raise HTTPException(422, "Geometria deve conter pares [longitude, latitude] válidos")
    conteudo = gerar_gpx(
        str(payload.get("origem", "Origem")),
        str(payload.get("destino", "Destino")),
        geometria,
    )
    return Response(
        content=conteudo,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": "attachment; filename=roteiro.gpx"},
    )


@router.post("/custos", response_model=CustosResponse, summary="Calcula custos e rateio")
async def custos(payload: CustosRequest) -> CustosResponse:
    return CustosResponse(**calcular_custos(payload))


@router.post("/mapa-rota", response_model=MapaRotaResponse, summary="Retorna geometria, relevo e paradas")
async def mapa_rota(payload: MapaRotaRequest, request: Request, client: httpx.AsyncClient = Depends(obter_http_client)) -> MapaRotaResponse:
    client: httpx.AsyncClient = request.app.state.http_client
    rota = await obter_rota_com_geometria(client, payload)
    rota["altimetria"] = await obter_altimetria(client, rota["geometria"])
    return MapaRotaResponse(**rota)


@router.post("/stream-guia", summary="Gera o guia turístico por SSE")
async def stream_guia(
    payload: GuiaStreamRequest,
    request: Request,
    x_user_id: str | None = Header(default=None),
) -> StreamingResponse:
    if x_user_id and not get_session(x_user_id):
        raise HTTPException(status_code=401, detail="Sessão ausente ou expirada")

    async def eventos():
        async for evento in gerar_guia_stream(
            payload.destino,
            payload.dias_estadia,
            payload.estilo_viagem,
            get_settings().gemini_api_key,
            payload.clima_info, payload.atrativos, payload.gastronomia,
        ):
            if await request.is_disconnected():
                break
            yield evento

    return StreamingResponse(
        eventos(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/planejar", response_model=RoteiroResponse, summary="Planeja um roteiro")
async def planejar_roteiro(
    payload: RoteiroRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    x_user_id: str | None = Header(default=None),
    client: httpx.AsyncClient = Depends(obter_http_client),
) -> RoteiroResponse:
    """Consulta geocodificação, clima e rota em estágios concorrentes."""
    if x_user_id and not get_session(x_user_id):
        raise HTTPException(status_code=401, detail="Sessão ausente ou expirada")
    request_key = hashlib.sha256(
        f"{x_user_id or 'anonymous'}:{payload.model_dump_json()}".encode()
    ).hexdigest()
    async with request_lock:
        if request_key in active_requests:
            raise HTTPException(status_code=409, detail="Planejamento já está em andamento")
        active_requests.add(request_key)
    client: httpx.AsyncClient = request.app.state.http_client
    try:
        if await request.is_disconnected():
            raise HTTPException(499, "Cliente desconectado")
        origem, destino = await asyncio.gather(
            buscar_coordenadas(client, payload.origem_cidade, payload.origem_uf),
            buscar_coordenadas(client, payload.destino_cidade, payload.destino_uf),
        )
        if await request.is_disconnected():
            raise HTTPException(499, "Cliente desconectado")
        clima, percurso = await asyncio.gather(
            obter_clima(client, destino["latitude"], destino["longitude"]),
            obter_percurso(client, origem, destino),
        )
        roteiro = RoteiroResponse(
            id=uuid4().hex,
            origem=f"{payload.origem_cidade} - {payload.origem_uf}",
            destino=f"{payload.destino_cidade} - {payload.destino_uf}",
            origem_coordenadas=[origem["latitude"], origem["longitude"]],
            destino_coordenadas=[destino["latitude"], destino["longitude"]],
            clima=clima,
            percurso=percurso,
            guia_status="provider-ready",
            dias_estadia=payload.dias_estadia, estilo_viagem=payload.estilo_viagem,
            atrativos=[{"id": str(i), "nome": n} for i,n in enumerate(catalogo(payload.destino_cidade,payload.destino_uf).get("atrativos",[]))],
            gastronomia=catalogo(payload.destino_cidade,payload.destino_uf).get("gastronomia",[]),
        )
        if await request.is_disconnected():
            raise HTTPException(499, "Cliente desconectado")
        if x_user_id:
            background_tasks.add_task(salvar_roteiro, x_user_id, roteiro.model_dump())
        return roteiro
    finally:
        async with request_lock:
            active_requests.discard(request_key)


@router.get("", response_model=list[RoteiroResponse], summary="Lista os roteiros do usuário")
async def listar_roteiros_usuario(
    x_user_id: str | None = Header(default=None),
) -> list[RoteiroResponse]:
    if not x_user_id or not get_session(x_user_id):
        raise HTTPException(status_code=401, detail="Sessão ausente ou expirada")
    return [RoteiroResponse(**item) for item in await listar_roteiros(x_user_id)]


@router.delete("/{roteiro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_roteiro(
    roteiro_id: str,
    x_user_id: str | None = Header(default=None),
) -> None:
    if not x_user_id or not get_session(x_user_id):
        raise HTTPException(status_code=401, detail="Sessão ausente ou expirada")
    deleted = await remover_roteiro(x_user_id, roteiro_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

@router.get("/destinos")
async def destinos():
    return DESTINOS

@router.patch("/{roteiro_id}/visitas")
async def visitas(roteiro_id: str, payload: dict, user_id: str = Depends(obter_usuario)):
    from ..services.storage_service import atualizar_visitas
    ids = payload.get("visitas", [])
    if not isinstance(ids,list) or not all(isinstance(i,str) for i in ids):
        raise HTTPException(422,"Lista de visitas inválida")
    result = await atualizar_visitas(user_id, roteiro_id, ids)
    if result is None: raise HTTPException(404,"Viagem não encontrada")
    return result

@router.post("/altimetria")
async def altimetria_extra(payload: dict, request: Request):
    points=payload.get("geometria",[])
    if not isinstance(points,list) or len(points)>100000 or not all(isinstance(pt,list) and len(pt)==2 and all(isinstance(v,(int,float)) for v in pt) for pt in points):
        raise HTTPException(422,"Geometria inválida")
    return await obter_altimetria(request.app.state.http_client, points)
