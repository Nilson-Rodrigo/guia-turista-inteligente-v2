import asyncio
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services import storage
from backend.app.core.circuit_breaker import providers_breakers, CircuitBreaker
from backend.app.core.session import sessions
from backend.app.services.altimetria import calcular_perfil
from backend.app.services.advanced import calcular_custos
from backend.app.schemas.viagem_avancada import CustosRequest

@pytest.fixture
def client(tmp_path,monkeypatch):
    sessions.clear()
    for b in providers_breakers.values(): b.record_success()
    monkeypatch.setattr(storage,'DATA_FILE',tmp_path/'viagens.json')
    from backend.app.core.config import get_settings
    monkeypatch.setattr(get_settings(),'gemini_api_key','')
    def provider(req):
        if 'geocoding' in str(req.url):
            city=req.url.params['name']
            return httpx.Response(200,json={'results':[{'name':city,'admin1':'Pernambuco' if city=='Recife' else 'Bahia','latitude':-8,'longitude':-35}]})
        if 'forecast' in str(req.url): return httpx.Response(200,json={'current':{'temperature_2m':28,'relative_humidity_2m':70,'wind_speed_10m':12}})
        if 'elevation' in str(req.url): return httpx.Response(200,json={'results':[{'elevation':100},{'elevation':200}]})
        return httpx.Response(200,json={'routes':[{'distance':800000,'duration':36000,'geometry':{'coordinates':[[-35,-8],[-38,-13]]}}]})
    with TestClient(app) as c:
        original=app.state.http_client
        mocked=httpx.AsyncClient(transport=httpx.MockTransport(provider))
        app.state.http_client=mocked
        yield c
        asyncio.run(mocked.aclose())
        app.state.http_client=original

@pytest.fixture
def headers(client):return {'X-User-Id':client.post('/api/v1/auth/demo').json()['usuario']['id']}
DATA={'origem_cidade':'Recife','origem_uf':'pe','destino_cidade':'Salvador','destino_uf':'ba'}
def test_health(client):assert client.get('/healthz').json()=={'status':'ok'}
def test_requires_session(client):assert client.post('/api/v1/roteiros/planejar',json=DATA).status_code==401

def test_history_isolation_delete(client,headers):
    r=client.post('/api/v1/roteiros/planejar',json=DATA,headers=headers);assert r.status_code==200,r.text
    trip=r.json();assert trip['origem']=='Recife - PE'
    assert 'X-Process-Time' in r.headers
    assert client.get('/api/v1/roteiros',headers=headers).json()[0]['id']==trip['id']
    other={'X-User-Id':client.post('/api/v1/auth/demo').json()['usuario']['id']}
    assert client.get('/api/v1/roteiros',headers=other).json()==[]
    assert client.delete('/api/v1/roteiros/'+trip['id'],headers=other).status_code==404
    assert client.delete('/api/v1/roteiros/'+trip['id'],headers=headers).status_code==204

@pytest.mark.parametrize('uf',['P','ZZ','12'])
def test_invalid_uf(client,headers,uf):assert client.post('/api/v1/roteiros/planejar',headers=headers,json={**DATA,'origem_uf':uf}).status_code==422

def test_costs():
    a=calcular_custos(CustosRequest(distancia_km=120,consumo_medio=12,preco_combustivel=6,passageiros=2,penalizacao_percentual=10))
    assert a['custo_total']==66 and a['custo_por_passageiro']==33
    assert calcular_custos(CustosRequest(distancia_km=120,propulsao='eletrico'))['custo_total']==20

def test_elevation():assert calcular_perfil([100,200,150])['ganho_subida_m']==100

def test_map_gpx_stream(client,headers):
    r=client.post('/api/v1/roteiros/mapa-rota',headers=headers,json={'origem_latitude':-8,'origem_longitude':-35,'destino_latitude':-13,'destino_longitude':-38});assert r.status_code==200,r.text
    assert r.json()['altimetria']['disponivel']
    gpx=client.post('/api/v1/roteiros/exportar/gpx',headers=headers,json={'geometria':r.json()['geometria']})
    from xml.etree.ElementTree import fromstring
    assert fromstring(gpx.content).attrib['version']=='1.1'
    stream=client.post('/api/v1/roteiros/stream-guia',headers=headers,json={'destino':'Recife'})
    e=json.loads(stream.text.split('data: ')[1]);assert e['done'] and e['fallback']

def test_visits(client,headers):
    trip=client.post('/api/v1/roteiros/planejar',headers=headers,json=DATA).json()
    r=client.patch('/api/v1/roteiros/'+trip['id']+'/visitas',headers=headers,json={'visitas':['0','invalid']})
    assert r.json()['visitas']==['0']

def test_breaker():
    b=CircuitBreaker(failure_limit=2);b.record_failure();b.record_failure();assert b.state=='open';b.record_success();assert b.state=='closed'

def test_duplicate(client,headers):
    from backend.app.core.concurrency import active_requests
    from backend.app.schemas.roteiros import RoteiroRequest
    import hashlib
    key=hashlib.sha256(f"{headers['X-User-Id']}:{RoteiroRequest(**DATA).model_dump_json()}".encode()).hexdigest();active_requests.add(key)
    try:assert client.post('/api/v1/roteiros/planejar',headers=headers,json=DATA).status_code==409
    finally:active_requests.discard(key)

def test_concurrent_storage(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DATA_FILE',tmp_path/'concurrent.json')
    async def run():await asyncio.gather(*(storage.salvar_roteiro('u',{'id':str(i)}) for i in range(20)))
    asyncio.run(run());assert len(json.loads(storage.DATA_FILE.read_text())['usuarios']['u']['roteiros'])==20
