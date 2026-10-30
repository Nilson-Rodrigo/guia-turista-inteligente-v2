# Checklist da Atividade 2

## 1. Fundacao do projeto

- [x] Separar o backend FastAPI do Flask legado.
- [x] Criar configuracao por ambiente e exemplo de `.env`.
- [x] Configurar CORS para o frontend em `localhost:5173`.
- [x] Disponibilizar OpenAPI em `/docs` e `/redoc`.
- [x] Criar probes `/healthz` e `/readyz`.
- [x] Criar contrato Pydantic inicial para planejamento.
- [x] Retornar `422` para UF com formato invalido.

## 2. Backend FastAPI

- [x] Criar ciclo de vida com `httpx.AsyncClient` compartilhado.
- [x] Implementar autenticacao Google e modo visitante com TTL de 2 horas.
- [x] Implementar `/api/v1/auth` e isolamento por `X-User-Id`.
- [x] Implementar geocodificacao, clima e OSRM de forma assincrona.
- [x] Orquestrar geocodificacao e telemetria com `asyncio.gather`.
- [x] Implementar bloqueio de requisicoes duplicadas com `asyncio.Lock` e `409`.
- [x] Implementar deteccao de desconexao do cliente.
- [x] Implementar persistencia atomica em JSON com tarefas em segundo plano.
- [x] Implementar autonomia e calculo de custos para combustao/EV com rateio.
- [x] Integrar altimetria e Open-Elevation ao mapa.
- [ ] Integrar catálogo real de postos ao mapa.
- [x] Implementar `/stream-guia` com SSE e fallback do Gemini.
- [x] Implementar exportacao GPX 1.1.
- [x] Implementar compartilhamento via WhatsApp.
- [x] Implementar endpoint de métricas Prometheus.
- [x] Implementar estados básicos de circuit breakers.
- [x] Implementar telemetria basica, correlation ID e tempo de processamento.

## 3. Frontend React 19 + Vite

- [x] Criar SPA com Vite e componentes semanticos.
- [x] Criar formulario unificado de planejamento.
- [x] Adicionar UF, GPS e Haversine para destinos acima de 400 km.
- [ ] Adicionar autocomplete e recomendacoes de destinos.
- [x] Adicionar selecao combustao/EV, duracao, perfil e passageiros.
- [x] Integrar REST e streaming SSE.
- [x] Criar mapa Leaflet com rota e paradas de autonomia.
- [x] Criar cards de clima, guia, atrativos e gastronomia.
- [x] Criar tema claro/escuro e acessibilidade WCAG 2.1 AA.
- [x] Criar historico e exclusao.
- [x] Criar sessao visitante e armazenamento local.
- [x] Criar ErrorBoundary.
- [x] Criar Toast, status de rede e timer de visitante.

## 4. Qualidade e entrega

- [x] Criar primeiro teste de contrato do backend.
- [x] Cobrir backend com `pytest tests/ -v`.
- [x] Cobrir frontend com Vitest.
- [x] Executar lint.
- [ ] Configurar e executar type checks automatizados.
- [ ] Testar o processo atualizado com backend na porta 8001 e frontend na porta 5173.
- [ ] Preparar demonstracao individual por responsabilidade.
