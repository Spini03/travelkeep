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
- Chat IA persiste con `PostgresSaver` compartido (`utils/checkpointer.py`),
  no `MemorySaver()`. `itinerary_agent` y `activities_chat_agent` comparten
  `thread_id` (= `itinerary_id`) pero usan `thread_id` sufijado
  (`:itinerary` / `:activities`) para no pisarse — NO usar `checkpoint_ns`
  para esto, es para subgrafos internos de LangGraph, no para separar agentes
  independientes (rompe `get_state()` con `ValueError` si se usa mal).
- Alojamiento: scraping con Playwright headless (`utils/scrapper.py`), no
  httpx — Airbnb/Booking bloquean bots con 200/202 disfrazados de éxito, httpx
  no ejecuta JS y no lo detecta. Caché cache-aside en tabla `scrape_cache`
  (Postgres, TTL 7 días, compartida por URL entre usuarios/itinerarios) antes
  de scrapear. `scrape_status` persistido en `Accommodations`
  (success/blocked/error). Pool fijo de browsers (`utils/browser_pool.py`,
  default 3, `PLAYWRIGHT_POOL_SIZE`) arrancado en el lifespan de `main.py` —
  OJO: Playwright sync API NO es thread-safe entre threads (un `Browser`
  lanzado en un thread no se puede usar desde otro, crashea con
  `greenlet.error`), así que el pool NO presta el objeto `Browser` crudo;
  cada slot es un thread dedicado con su propio `sync_playwright()` + browser,
  y el borrow real es "someter un job a ese thread y esperar". En Windows,
  `browser_pool.py` fuerza `asyncio.WindowsProactorEventLoopPolicy` a nivel
  de módulo (antes de crear threads) — sin esto, si algo en el import chain
  del proceso real (no reproducido en sandbox) deja la política del loop en
  Selector, los threads del pool heredan esa política y `sync_playwright()`
  revienta con `NotImplementedError` al lanzar el subproceso de Chromium
  (Selector no soporta `subprocess_exec` en Windows). Limpieza de
  `scrape_cache` corre cada 24hs vía APScheduler (`utils/scrape_cache_scheduler.py`,
  reusa `SCRAPE_CACHE_TTL` de `services/accommodations.py`), también arrancado
  en el lifespan. Endpoint `POST /api/accommodations/{id}/retry-scrape` re-corre
  el cache-aside de siempre (no bypassea caché).
- `alembic revision --autogenerate` va a detectar como "diff" las tablas de
  LangGraph (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) y
  `token_blocklist` — existen en la DB pero no en el metadata de SQLAlchemy
  (las crea `PostgresSaver.setup()`, no un modelo ORM). Podar esas líneas a
  mano de cada migración autogenerada, no son parte del diff real.
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
  persistencia de chat (listo) + cierre de alojamiento (listo) + vuelos
  (wiring SerpApi, pendiente).
- Después: pool de browsers (listo), limpieza automática de `scrape_cache`
  (listo), endpoint de reintentar scrape (listo, backend + frontend), migrar
  caché a Redis si el volumen de tráfico lo justifica, city
  tours, reservas puntuales (boliches/eventos/actividades), otros
  transportes, deploy público, CORS
  para prod.