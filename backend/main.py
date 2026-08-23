import sys

# Windows abre stdout/stderr con cp1252 por default, que no puede codificar
# emojis usados en los logs (ej. utils/itinerary_validators.py). Forzamos UTF-8
# acá para que ande siempre, sin depender de que alguien setee PYTHONIOENCODING.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from routes.travel_classifier_routes import travel_classifier_router
from routes.document_analyzer_router import document_analyzer_router
from routes.itinerary import itinerary_router
from routes.transportation import transportation_router
from routes.accommodations import accommodations_router
from routes.flights import flights_router
from routes.traveler_test.traveler_type import router as traveler_type_router
from routes.traveler_test.user_traveler_test import router as user_traveler_test_router
from routes.traveler_test.question import router as question_router
from routes.traveler_test.question_option import router as question_option_router
from routes.traveler_test.question_option_score import router as question_option_score_router
from routes.traveler_test.user_answers import router as user_answers_router
from routes.auth_routes import auth_router
from routes.user import user_router
from database import engine
from database import get_db
from models.itinerary import Base as ItineraryBase
from models.user import Base as UserBase
from models.traveler_test.traveler_type import Base as TravelerTypeBase
from models.traveler_test.question import Base as QuestionBase
from models.traveler_test.question_option import Base as QuestionOptionBase
from models.traveler_test.question_option_score import Base as QuestionOptionScoreBase
from models.traveler_test.user_answers import Base as UserAnswersBase
from models.traveler_test.user_traveler_test import Base as UserTravelerTestBase
from starlette.middleware.sessions import SessionMiddleware
from utils.checkpointer import setup_checkpointer
from utils.browser_pool import browser_pool
from utils.scrape_cache_scheduler import start_scrape_cache_scheduler, stop_scrape_cache_scheduler
import os

import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_checkpointer()
    browser_pool.start()
    start_scrape_cache_scheduler()
    yield
    stop_scrape_cache_scheduler()
    browser_pool.stop()


app = FastAPI(
    title="TravelKeep AI API",
    description="AI-powered travel planning and user management API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
# Localhost only, varios puertos porque Next.js toma el siguiente libre si 3000
# está ocupado (3000/3001 cubren el caso común). Todavía no apto para producción
# (ver AGENTS.md, "después").
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET_KEY"))

# Create database tables
# NOTA: comentado — la creación de tablas ahora la maneja Alembic exclusivamente (alembic upgrade head)
# ItineraryBase.metadata.create_all(bind=engine)
# UserBase.metadata.create_all(bind=engine)
# TravelerTypeBase.metadata.create_all(bind=engine)
# QuestionBase.metadata.create_all(bind=engine)
# QuestionOptionBase.metadata.create_all(bind=engine)
# QuestionOptionScoreBase.metadata.create_all(bind=engine)
# UserAnswersBase.metadata.create_all(bind=engine)
# UserTravelerTestBase.metadata.create_all(bind=engine)

# Include routes
app.include_router(auth_router)  # Authentication routes (/auth)
app.include_router(user_router)  # User management routes (/users)
app.include_router(itinerary_router)  # Itinerary routes
app.include_router(transportation_router)  # Transport routes
app.include_router(accommodations_router)  # Accommodations routes
app.include_router(flights_router)  # Flights routes
app.include_router(traveler_type_router)  # Traveler type routes (/traveler-types)
app.include_router(user_traveler_test_router)  # User traveler test routes (/traveler-tests)
app.include_router(user_traveler_test_router, prefix="/api")  # Also expose under /api for FE compatibility
app.include_router(question_router)  # Question routes (/questions)
app.include_router(question_option_router)  # Question option routes (/question-options)
app.include_router(question_option_score_router)  # Question option score routes (/question-option-scores)
app.include_router(user_answers_router)  # User answers routes (/user-answers)
# app.include_router(travel_classifier_router)
# app.include_router(document_analyzer_router)

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)