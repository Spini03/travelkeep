# AGENTS.md - travelkeep
 
TravelKeep (ex TravelSmart). Monorepo `/backend` `/frontend`. Producto: yo (Santiago)
soy el usuario principal — construyo la herramienta a mi medida, la uso, y recién si
anda bien se despliega públicamente. Core (itinerarios + chat IA + traveler-test)
NO se reemplaza, se extiende. Alcance largo plazo: vuelos, alojamiento, city tours,
reservas puntuales, transportes — centralizado.
 
## Stack
 
Backend: Python 3.12 (¡no 3.14, incompatible con varias deps!) + FastAPI + SQLAlchemy
+ Alembic + PostgreSQL, LangGraph/LangChain (OpenAI + Gemini), JWT propio + Google
OAuth, SerpApi + Mapbox + scraping alojamientos.
Frontend: Next.js 15 + React 19 + TS, Context+useReducer (sin Redux/Zustand).
## Commands
 
```powershell
# Backend
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium   # paso extra, no lo cubre pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8001
 
# Frontend (ojo: carpeta anidada frontend/frontend)
cd frontend\frontend
npm install
npm run dev        # next dev --turbopack
npm run lint        # next lint
npm run type-check  # tsc --noEmit
```
 
## Ports
 
| Service | Port |
|---|---|
| Backend (uvicorn) | localhost:8001 |
| Frontend (Next.js) | localhost:3000 |
| PostgreSQL | local, db `db_travelkeep`, user `travelkeep_user` |
 
## Non-standard patterns / gotchas
 
- Frontend está anidado: `frontend/frontend/` (no `frontend/` directo) — el `frontend/`
  raíz solo tiene docs/assets sueltos.
- `frontend/frontend/package.json` todavía dice `"name": "travelsmart-frontend"`
  (nombre viejo, no romper al renombrar sin querer).
- Env vars JWT unificadas con prefijo `JWT_` (`JWT_SECRET_KEY`, `JWT_ALGORITHM`) —
  antes había mismatch de nombres entre código y `.env`.
- `create_all()` comentado en `main.py` — Alembic es la única fuente de verdad para
  el schema, nunca reactivar create_all.
- Migración `aa7c9965a439` tiene un parche (comentado) porque dropeaba
  índices/tabla `token_blocklist` inexistentes en cadena limpia.
- `MemorySaver()` in-memory en `graphs/itinerary_chat_agent.py` y
  `activities_chat_agent.py` — el historial del chat IA se pierde al reiniciar
  el server (bloqueante, ver Pendientes en contexto de sesión).
- CORS hardcodeado a `http://localhost:3000` — funciona solo en local.
## Constraints
 
- **Nunca ejecutar comandos git** sin aprobación explícita — los ejecuta Santiago.
- No tocar carpetas de terceros / generadas (node_modules, venv, migraciones ya
  aplicadas salvo bugfix puntual documentado).
## Tests / Lint
 
- Backend: no hay pytest configurado. `backend/tests/` tiene scripts sueltos de
  prueba/experimentación (document_analyzer, trip_planner_graph, etc.), no una
  suite real. Sin CI.
- Frontend: `npm run lint` (eslint) y `npm run type-check` (tsc) sí están
  configurados y funcionan.
## Verify changes
 
1. Backend: levantar server (`uvicorn main:app --reload --port 8001`), probar
   endpoint afectado manualmente.
2. Frontend: `npm run lint` + `npm run type-check`, luego probar en
   `localhost:3000`.
3. Sin tests automatizados de backend — probar a mano hasta que exista suite.
## Commits
 
Conventional commits con scope:
```
feat(itinerary): ...
fix(chat-agent): ...
refactor(accommodations): ...
```
Sin "Co-Authored-By" ni atribución de IA.
 
## Decisiones tomadas (MVP vs después)
 
- MVP: itinerarios + chat IA + traveler-test (ya existente, se extiende) +
  persistencia de chat + cierre de alojamiento + vuelos (wiring SerpApi).
- Después: city tours, reservas puntuales (boliches/eventos/actividades),
  otros transportes, deploy público, CORS para prod.