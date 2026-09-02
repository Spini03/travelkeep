# TravelKeep

> Organizá y centralizá todo tu viaje - vuelos, alojamiento, tours y reservas en un solo lugar.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)

<!-- TODO: agregar screenshot -->

## Overview

TravelKeep es una herramienta para centralizar la planificación de un viaje: itinerarios generados con IA o armados a mano, chat conversacional, test de perfil de viajero, alojamiento, vuelos y tours en un solo lugar. Hoy es de uso personal - lo construye y usa Santiago para sus propios viajes - y solo se despliega públicamente si el uso propio valida que funciona bien, con roadmap hacia multi-tenant.

## Features

**MVP funcional:**
- 🧳 Itinerarios de viaje (generación con IA + edición manual), con persistencia
- 💬 Chat IA sobre el itinerario (agentes LangGraph/LangChain, checkpointer persistente en Postgres)
- 🧠 Traveler test - perfil de viajero que alimenta la generación de itinerarios
- 🏨 Alojamiento - scraping de plataformas (Playwright) con caché cache-aside
- ✈️ Vuelos - búsqueda y booking options vía SerpApi (round-trip, one-way y multi-city)
- 🎟️ Tours y actividades - scraping de GetYourGuide
- 🔐 Autenticación - JWT propio + Google OAuth, modo invitado por sesión

**Roadmap:**
- Reservas puntuales (boliches, eventos, actividades)
- Otros medios de transporte más allá de vuelos
- Migrar caché de scraping a Redis si el volumen de tráfico lo justifica
- Deploy público y CORS apto para producción
- Evolución a multi-tenant

## Tech stack

| Capa | Tecnologías |
|---|---|
| **Backend** | Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 + Alembic, PostgreSQL |
| **IA / Agentes** | LangGraph 0.6, LangChain 0.3 (OpenAI + Gemini) |
| **Integraciones externas** | SerpApi (vuelos), Playwright (scraping alojamiento), GetYourGuide (scraping tours), Mapbox |
| **Auth** | JWT propio (PyJWT / python-jose) + Google OAuth (Authlib) |
| **Frontend** | Next.js 15, React 19, TypeScript |
| **UI** | Tailwind CSS 4, shadcn/ui (Radix), React Hook Form + Zod |
| **Estado (frontend)** | React Context + useReducer (sin Redux/Zustand) |
| **Infra / otros** | APScheduler (limpieza de caché), LangSmith (tracing, opcional) |

## Arquitectura

Backend en **flat layered**: `routes/` → `services/` → `models/`, con `graphs/` como capa paralela para los agentes de IA (sin repositorios intermedios, los services usan SQLAlchemy `Session` directo). Para integraciones externas *nuevas* (vuelos, tours) se define una interfaz `Protocol` en `ports/` con su implementación en `adapters/` - las integraciones más viejas (scraping de alojamiento, OAuth, LLM) no se migraron retroactivamente a este patrón.

Más detalle de convenciones y decisiones de arquitectura en [AGENTS.md](AGENTS.md).

## Estructura del repo

```
travelkeep/
├── backend/
│   ├── routes/          # Endpoints FastAPI
│   ├── services/         # Lógica de negocio
│   ├── models/           # Modelos SQLAlchemy
│   ├── schemas/          # Modelos Pydantic
│   ├── graphs/            # Agentes LangGraph
│   ├── ports/             # Interfaces (Protocol) para integraciones externas nuevas
│   ├── adapters/          # Implementaciones concretas (SerpApi, GetYourGuide, ...)
│   ├── alembic/           # Migraciones de base de datos
│   └── utils/
└── frontend/
    └── frontend/           # App Next.js (carpeta anidada)
        └── src/
            ├── app/          # App Router
            ├── components/
            ├── contexts/
            ├── hooks/
            └── lib/
```

## Getting started

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
playwright install chromium
cp env.example .env           # completar con tus propias claves
alembic upgrade head
uvicorn main:app --reload --reload-exclude venv --port 8002
```

La API queda disponible en `http://localhost:8002` (docs interactivas en `/docs`).

### Frontend

```bash
cd frontend/frontend
npm install
npm run dev
```

La app queda disponible en `http://localhost:3000`.

## Variables de entorno

- Backend: [`backend/env.example`](backend/env.example) - DB, JWT, Google OAuth, OpenAI/Gemini, SerpApi, Mapbox, SMTP.
- Frontend: `frontend/frontend/.env.example` - URL base de la API (`NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_ROOT_BASE_URL`) y token público de Mapbox (`NEXT_PUBLIC_MAPBOX_API_TOKEN`).

En ambos casos, copiá el archivo a `.env` (backend) o `.env.local` (frontend) y completá con tus propias claves.

## Roadmap

Ver sección [Features](#features) arriba y el backlog completo en [AGENTS.md](AGENTS.md).

## Licencia

MIT - ver [LICENSE](LICENSE).

## Autor

**Santiago Spini** - [github.com/Spini03/travelkeep](https://github.com/Spini03/travelkeep)
