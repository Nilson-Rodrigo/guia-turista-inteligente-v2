# Guia do Turista Inteligente — Atividade 2

Versão desenvolvida a partir do projeto enviado, com backend FastAPI e frontend React/Vite. Leia este arquivo antes de executar.

## Requisitos

- Python 3.11 ou superior.
- Node.js 22.12 ou superior (Node 24 recomendado).
- Internet para instalar dependências e consultar mapas e APIs.

## 1. Backend — primeiro terminal

Na pasta extraída:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8001
```

Antes de iniciar, edite `backend/.env`:

```dotenv
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-flash-latest
GOOGLE_CLIENT_ID=seu_cliente.apps.googleusercontent.com
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

A chave Gemini fica SOMENTE no backend. Obtenha-a em https://aistudio.google.com/apikey. O nome do modelo é configurável conforme sua conta e disponibilidade.

API: http://localhost:8001/docs. Saúde: `/healthz`, prontidão: `/readyz`, métricas: `/metrics`.

## 2. Frontend — segundo terminal

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Abra http://localhost:5173. O backend deve continuar aberto no outro terminal.

Para Google, coloque em `frontend/.env` o mesmo Client ID do backend:

```dotenv
VITE_API_URL=http://localhost:8001
VITE_GOOGLE_CLIENT_ID=seu_cliente.apps.googleusercontent.com
```

Crie um cliente OAuth do tipo aplicativo Web no Google Cloud e autorize as origens `http://localhost:5173` e `http://127.0.0.1:5173`. Sem Client ID, use visitante. Sem chave Gemini, o guia informa indisponibilidade; não simula uma resposta de IA.

Reinicie os servidores após editar `.env`.

## Funcionalidades

- Formulário de origem/destino, UF, duração, perfil e parâmetros de combustão/EV.
- Geocodificação por município e estado; consultas concorrentes de clima/rota.
- Leaflet com geometria OSRM e rotas alternativas, quando fornecidas.
- Perfil de elevação Open-Meteo (Copernicus GLO-90) e ajuste didático de consumo.
- Custos, pedágios informados manualmente e rateio por passageiros.
- Projeção de paradas com reserva de 18%, calculadas pela distância acumulada da geometria.
- Gemini com SDK oficial e streaming SSE; cancelamento do streaming ao trocar de viagem.
- Catálogo local de destinos/atrativos/gastronomia e marcação de visitas.
- Sugestões pelo GPS para quatro destinos do catálogo acima de 400 km em linha reta.
- Histórico isolado por usuário, exclusão e persistência JSON atômica com file lock.
- Visitante de duas horas e Google; alternância sem perder a conta Google salva.
- Exportação GPX 1.1, link WhatsApp e Google Maps.
- Tema persistido, status de rede, ErrorBoundary e métricas de latência.

## Limites que precisam ser conhecidos na apresentação

- Os serviços externos são reais, mas esta entrega foi validada com respostas simuladas nos testes. Não foram usadas chaves pessoais para testar Gemini ou login Google ao vivo.
- Não há garantia de resposta abaixo de 1.000 ms. A latência deve ser medida na rede da apresentação. O tempo de API e o tempo total da operação são mostrados separadamente.
- O autocomplete usa um catálogo local de oito destinos, não todos os municípios brasileiros. Outros municípios podem ser digitados e geocodificados.
- As paradas não são postos/eletropostos confirmados; são pontos projetados de autonomia. Confirme a infraestrutura real antes de viajar.
- Pedágios são fornecidos manualmente. Não existe integração com tarifas rodoviárias atualizadas.
- O perfil de relevo utiliza até vinte amostras; o ajuste de consumo é uma regra didática, não um modelo físico validado.
- O compartilhamento prepara um link para o usuário enviar no WhatsApp; não envia mensagens automaticamente.
- A exportação GPX contém o traçado em latitude/longitude, sem elevações ou catálogo de waypoints.
- Sessões e circuitos são mantidos em memória; execute com um único worker. Reiniciar o backend exige entrar novamente; viagens Google permanecem no arquivo JSON e voltam após novo login. Visitantes recebem uma identidade nova a cada login.
- `X-User-Id` segue o contrato didático da atividade. Para produção, substituir por token de sessão secreto e aplicar controles adicionais.
- O estado `closed` dos circuitos significa que chamadas são permitidas; não constitui uma verificação ativa da disponibilidade.

## Testes e qualidade

Na raiz (mesmo nível das pastas backend e frontend), após instalar dependências Python:

```bash
python -m pytest -v
```

No frontend:

```bash
npm test
npm run lint
npm run build
```

Inclui teste de fluxo da interface com APIs simuladas. Validação desta entrega: 18 testes de backend e 12 de frontend aprovados; build e lint aprovados. O editor não apontou diagnósticos nos arquivos alterados, mas ainda não há type check automatizado configurado. Testes de backend usam `httpx.MockTransport`, sem depender da disponibilidade da internet.

## Divisão para apresentação

1. Frontend: `App.jsx`, `RoteiroForm.jsx`, `MapaRota.jsx`, `services/api.js`, `geolocation.js`, CSS, login e sessão.
2. Backend: `main.py`, `/planejar`, `core/dependencies.py`, concorrência e circuit breakers.
3. Dados: schemas, `custos_service.py`, `postos_service.py`, `altimetria_service.py` e `storage_service.py` (JSON em `backend/static/data/`).
4. Streaming/QA: `gemini_service.py`, SSE, `gpx_service.py`, métricas e `test_roteiros.py`.

Cada aluno deve estudar e conseguir defender o código que apresenta. Este ZIP não inclui `.venv`, `node_modules`, chaves ou dados pessoais.

## Pendências para a entrega final

- Integrar um catálogo real de postos e eletropostos ao mapa; as paradas atuais são projeções de autonomia.
- Configurar um type checker automatizado para Python e JavaScript/React.
- Repetir o teste manual com os processos atualizados nas portas 8001 e 5173; durante esta validação elas já estavam ocupadas, então foram usadas portas alternativas.
- Definir a divisão da demonstração individual entre os integrantes da equipe.
