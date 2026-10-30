# 🇧🇷 Guia do Turista Inteligente (Flask + HTTPX + Google Auth + Gemini AI)

Aplicação web desenvolvida com o microframework **Flask** e Python moderno para orquestração de APIs externas com autenticação via **Google Identity Services (OAuth JWT)**, gerando roteiros de viagem com dados meteorológicos, cálculo de percurso rodoviário e guia turístico & culinário com inteligência artificial.

---

## Arquitetura atual

```text
├── backend/       API FastAPI, serviços, schemas Pydantic e testes pytest
├── frontend/      SPA React/Vite, Leaflet, SSE e testes Vitest
├── static/data/   Persistência JSON dos roteiros
├── app.py         Flask legado, mantido para referência
└── CHECKLIST_ATIVIDADE.md
```

A versão atual usa FastAPI na porta `8001` e React/Vite na porta `5173`.

## Configuração e execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
uvicorn backend.app.main:app --reload --port 8001
```

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Preencha `backend/.env` quando necessário:

```env
GEMINI_API_KEY=
GOOGLE_CLIENT_ID=
CORS_ORIGINS=http://localhost:5173
```

Acesse `http://localhost:5173`, `http://localhost:8001/docs` e
`http://localhost:8001/metrics`.

## Endpoints principais

| Endpoint | Função |
| --- | --- |
| `POST /api/v1/auth/demo` | Sessão visitante por 2 horas |
| `POST /api/v1/roteiros/planejar` | Planejamento com clima e rota |
| `POST /api/v1/roteiros/stream-guia` | Guia turístico por SSE |
| `POST /api/v1/roteiros/mapa-rota` | Geometria, alternativas, paradas e relevo |
| `POST /api/v1/roteiros/custos` | Custos de combustível/energia e rateio |
| `GET /api/v1/roteiros` | Histórico por `X-User-Id` |
| `DELETE /api/v1/roteiros/{id}` | Excluir roteiro |
| `POST /api/v1/roteiros/exportar/gpx` | Exportar GPX 1.1 |
| `POST /api/v1/roteiros/compartilhar` | Link para WhatsApp |
| `GET /api/v1/telemetria/resumo` | Resumo operacional |

## Testes

```bash
# Backend
.venv/bin/pytest backend/tests -q

# Frontend
cd frontend
npm test
npm run build
```

## Organização da equipe

- **Frontend:** `frontend/src`, formulário, Leaflet, SSE, geolocalização e UX.
- **Backend core:** `backend/app/main.py`, autenticação e orquestração assíncrona.
- **Dados e altimetria:** schemas, custos, autonomia, Open-Elevation e persistência.
- **QA e streaming:** SSE, GPX, telemetria, testes e documentação.

Consulte [CHECKLIST_ATIVIDADE.md](CHECKLIST_ATIVIDADE.md) antes de assumir uma tarefa.
Marque uma etapa somente após validá-la com teste ou execução local.

## Commits e colaboração

```bash
git pull --rebase origin main
git diff --check
git add caminho/dos/arquivos
git commit -m "feat: descreve a alteração em português"
git push origin main
```

Mensagens devem ser objetivas e em português:

- `feat: adiciona exportação de roteiros em GPX`
- `fix: corrige validação de UF no planejamento`
- `test: cobre cálculo de distância Haversine`
- `docs: atualiza instruções de execução`

Não versionar `.venv/`, `node_modules/`, `frontend/dist/`, arquivos `.env` ou chaves de API.
