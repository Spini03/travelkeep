# TravelKeep AI API - Project Structure

## 📁 Directory Structure

```
TravelKeep-AI-API/
├── 📂 alembic/                          # Database migrations
│   ├── versions/                        # Migration versions
│   │   ├── b60401dd36dc_initial_schema.py
│   │   ├── 06ac05114ff3_nueva_columna_visited_countries_en_users.py
│   │   ├── 1bcb4d924950_upgrade_database_to_handle_oauth_con_.py
│   │   ├── 20250811_000001_add_multi_select_to_questions.py
│   │   ├── 20250812_000002_add_itinerary_change_log.py
│   │   ├── 20250814_000003_add_traveler_type_to_user.py
│   │   ├── 20250815_000004_remove_itinerary_change_log.py
│   │   ├── 20250912_000005_add_accommodations_table.py
│   │   ├── 20250919_000006_add_full_name_to_users.py
│   │   ├── a73a07d2fba6_delete_property.py
│   │   ├── cec3d8961b5e_add_username_to_db.py
│   │   └── e8e035f66129_change_visited_countries_from_json_to_.py
│   ├── env.py                           # Alembic environment configuration
│   ├── script.py.mako                   # Migration template
│   └── README                           # Alembic documentation
│
├── 📂 docs/                             # Project documentation
│   ├── database-diagram.md              # Database ER diagram & schema documentation
│   └── project-structure.md             # This file - Project organization
│
├── 📂 graphs/                           # LangGraph workflow definitions
│   ├── examples/                        # Example graphs and outputs
│   ├── activities_city.py               # City activities generation graph
│   ├── activities_city_map_reducer.py   # Map-reduce for activities
│   ├── activities_city_with_feedback.py # Activities with feedback loop
│   ├── document_analyzer_graph.py       # Document analysis workflow
│   ├── itinerary_agent.py               # Itinerary creation agent
│   ├── itinerary_graph.py               # Itinerary generation graph
│   ├── main_itinerary_graph.py          # Main orchestration graph
│   ├── route.py                         # Route planning graph
│   └── transportation_agent.py          # Transportation planning agent
│
├── 📂 models/                           # SQLAlchemy ORM Models
│   ├── traveler_test/                   # Traveler test system models
│   │   ├── question.py                  # Question model
│   │   ├── question_option.py           # Question options model
│   │   ├── question_option_score.py     # Scoring system model
│   │   ├── traveler_type.py             # Traveler type profiles
│   │   ├── user_answers.py              # User test answers
│   │   └── user_traveler_test.py        # Test sessions
│   ├── __init__.py
│   ├── accommodations.py                # Accommodations model
│   ├── itinerary.py                     # Itinerary model
│   ├── token_models.py                  # JWT token blocklist
│   ├── transportation.py                # Transportation model
│   └── user.py                          # User & OAuth accounts models
│
├── 📂 routes/                           # FastAPI route handlers
│   ├── traveler_test/                   # Traveler test endpoints
│   │   ├── question.py
│   │   ├── question_option.py
│   │   ├── question_option_score.py
│   │   ├── traveler_type.py
│   │   ├── user_answers.py
│   │   └── user_traveler_test.py
│   ├── accommodations.py                # Accommodations endpoints
│   ├── auth_routes.py                   # Authentication & OAuth routes
│   ├── document_analyzer_router.py      # Document analysis endpoints
│   ├── itinerary.py                     # Itinerary CRUD endpoints
│   ├── itinerary_routes.py              # Additional itinerary routes
│   ├── transportation.py                # Transportation endpoints
│   ├── travel_classifier_routes.py      # Travel classification endpoints
│   └── user.py                          # User management endpoints
│
├── 📂 schemas/                          # Pydantic schemas (DTOs)
│   ├── traveler_test/                   # Traveler test schemas
│   │   ├── __init__.py
│   │   ├── question.py
│   │   ├── question_option.py
│   │   ├── question_option_score.py
│   │   ├── traveler_type.py
│   │   ├── user_answers.py
│   │   └── user_traveler_test.py
│   ├── accommodations.py
│   ├── itinerary.py
│   ├── transportation.py
│   └── user.py
│
├── 📂 services/                         # Business logic layer
│   ├── traveler_test/                   # Traveler test services
│   │   ├── question.py
│   │   ├── question_option.py
│   │   ├── question_option_score.py
│   │   ├── travel_style_mapping.py      # Travel style algorithm
│   │   ├── traveler_type.py
│   │   ├── user_answers.py
│   │   └── user_traveler_test.py
│   ├── accommodations.py                # Accommodation business logic
│   ├── document_analyzer_services.py    # Document processing services
│   ├── email.py                         # Email sending services
│   ├── itinerary.py                     # Itinerary business logic
│   ├── jwt_service.py                   # JWT token management
│   ├── transportation.py                # Transportation services
│   ├── traveler_classifier_services.py  # Traveler classification logic
│   └── user.py                          # User management services
│
├── 📂 utils/                            # Utility functions & helpers
│   ├── accommodation_link.py            # Accommodation link utilities
│   ├── agent.py                         # AI agent utilities
│   ├── auth_google_utils.py             # Google OAuth utilities
│   ├── email_utlis.py                   # Email utilities
│   ├── jwt_utils.py                     # JWT token utilities
│   ├── scrapper.py                      # Web scraping utilities
│   ├── session.py                       # Session management
│   └── utils.py                         # General utilities
│
├── 📂 states/                           # LangGraph state definitions
│   ├── itinerary.py                     # Itinerary workflow state
│   └── route.py                         # Route planning state
│
├── 📂 prompts/                          # AI prompt templates
│   ├── itinerary_prompt.py              # Itinerary generation prompts
│   └── transportation_prompt.py         # Transportation prompts
│
├── 📂 templates/                        # HTML templates
│   ├── emails/                          # Email templates
│   │   ├── magic-link.html              # Passwordless login email
│   │   ├── password_reset.html          # Password reset email
│   │   ├── verification.html            # Email verification
│   │   └── welcome.html                 # Welcome email
│   ├── agent_planner.html               # Agent planner UI
│   ├── itinerario.html                  # Itinerary display template
│   └── traveler_classifier_template.html # Traveler classification UI
│
├── 📂 tools/                            # LangGraph tools & integrations
│   ├── geocoding_tool.py                # Geocoding integration
│   ├── web_search.py                    # Web search integration
│   └── wikipedia_tool.py                # Wikipedia integration
│
├── 📂 scripts/                          # Utility scripts
│   ├── cleanup_soft_deletes.py          # Clean soft-deleted records
│   ├── reset_traveler_test_data.py      # Reset test data
│   └── seed_traveler_test.py            # Seed traveler test questions
│
├── 📂 tests/                            # Test files & examples
│   ├── accommodation_graph/             # Accommodation graph tests
│   │   ├── accommodation_graph.py
│   │   └── state.py
│   ├── document_analyzer/               # Document analyzer tests
│   │   ├── pdf_example.pdf
│   │   ├── png_example-1.png
│   │   ├── png_example-2.png
│   │   ├── png_example-3.png
│   │   ├── boarding-pass-template-sample-text-qr-code-air-travel-concept-design-business-meetings-vector-paper-airline-ticket-186380802.webp
│   │   ├── test_docling.py
│   │   └── test_markitdown.py
│   └── trip_planner_graph/              # Trip planner graph tests
│       ├── HIL_graph.py                 # Human-in-the-loop graph
│       ├── create_react_agent_example.py
│       └── modify_itinerary_graph.py
│
├── 📂 examples/                         # Generated examples & outputs
│   ├── activities_city_Amsterdam_*.md
│   ├── activities_city_Buenos Aires_*.md
│   ├── activities_city_Marbella_*.md
│   ├── activities_city_Miami_*.md
│   ├── activities_city_Paris_*.md
│   └── ... (various city activity examples)
│
├── 📂 itinerary_examples/              # Sample itinerary outputs
│   └── v0.0.1-grecia-10d.json          # Greece 10-day itinerary
│
├── 📂 venv/                             # Python virtual environment (ignored)
│
├── 📄 main.py                           # FastAPI application entry point
├── 📄 database.py                       # Database connection & session management
├── 📄 dependencies.py                   # FastAPI dependencies
├── 📄 requirements.txt                  # Python dependencies
├── 📄 alembic.ini                       # Alembic configuration
├── 📄 langgraph.json                    # LangGraph configuration
├── 📄 index.html                        # Frontend entry point
├── 📄 package-lock.json                 # NPM lock file
├── 📄 test.py                           # Test runner
├── 📄 readme.md                         # Project README
├── 📄 env.example                       # Environment variables template
└── 📄 .gitignore                        # Git ignore rules
```

---

## 📋 Module Descriptions

### Core Application Files

| File | Description |
|------|-------------|
| `main.py` | FastAPI application initialization, middleware, and route registration |
| `database.py` | SQLAlchemy engine, session factory, and base model configuration |
| `dependencies.py` | Dependency injection functions for FastAPI routes |
| `requirements.txt` | Python package dependencies |

### Database Layer (`/models`)

Contains SQLAlchemy ORM models representing database tables.

**Main Models:**
- **`user.py`** - User accounts, authentication, and social accounts
- **`itinerary.py`** - Trip itineraries
- **`accommodations.py`** - Hotel/lodging recommendations
- **`transportation.py`** - Transportation details
- **`token_models.py`** - JWT token blocklist

**Traveler Test System:**
- **`traveler_type.py`** - Traveler personality types
- **`question.py`** - Test questions
- **`question_option.py`** - Answer options
- **`question_option_score.py`** - Scoring matrix
- **`user_traveler_test.py`** - Test sessions
- **`user_answers.py`** - User responses

### API Layer (`/routes`)

FastAPI route handlers organized by feature domain.

**Authentication & Users:**
- `auth_routes.py` - Login, OAuth, registration, password reset
- `user.py` - User profile management

**Itinerary System:**
- `itinerary.py` - Itinerary CRUD operations
- `itinerary_routes.py` - Additional itinerary endpoints
- `accommodations.py` - Accommodation management
- `transportation.py` - Transportation management

**AI Features:**
- `travel_classifier_routes.py` - Travel style classification
- `document_analyzer_router.py` - Document parsing (tickets, passports)

**Traveler Test:**
- Full CRUD for questions, options, scores, types, tests, and answers

### Business Logic (`/services`)

Service layer containing business rules and data processing logic.

- Mirrors the structure of `/routes`
- Handles database operations
- Implements business rules
- Manages external API integrations

### Data Transfer Objects (`/schemas`)

Pydantic models for request/response validation and serialization.

- Input validation
- Response formatting
- Type safety
- API documentation

### AI Workflows (`/graphs`)

LangGraph workflow definitions for AI-powered features.

**Main Graphs:**
- `main_itinerary_graph.py` - Orchestrates entire itinerary creation
- `itinerary_agent.py` - Day-by-day itinerary generation
- `activities_city.py` - City-specific activity recommendations
- `transportation_agent.py` - Transportation planning
- `route.py` - Route optimization
- `document_analyzer_graph.py` - Document parsing workflow

**Advanced Patterns:**
- `activities_city_map_reducer.py` - Parallel activity generation
- `activities_city_with_feedback.py` - Human-in-the-loop refinement

### Workflow State (`/states`)

State management for LangGraph workflows.

- `itinerary.py` - Itinerary generation state
- `route.py` - Route planning state

### AI Utilities

**`/prompts`** - Structured prompts for AI models
- `itinerary_prompt.py` - Itinerary generation prompts
- `transportation_prompt.py` - Transportation prompts

**`/tools`** - LangGraph tool integrations
- `geocoding_tool.py` - Geocoding integration
- `web_search.py` - Web search integration
- `wikipedia_tool.py` - Wikipedia integration

### Utilities (`/utils`)

Helper functions and reusable utilities.

- `auth_google_utils.py` - Google OAuth integration
- `jwt_utils.py` - JWT token generation/validation
- `email_utlis.py` - Email sending utilities
- `session.py` - Session management
- `scrapper.py` - Web scraping utilities
- `agent.py` - AI agent helpers

### Frontend (`/templates`)

HTML templates for emails and UI components.

- Email templates for authentication flows
- UI templates for itinerary display

### Database Migrations (`/alembic`)

Alembic migration scripts for schema versioning.

**Migration History:**
1. Initial schema
2. Visited countries column
3. OAuth connection handling
4. Multi-select questions
5. Itinerary change log
6. Traveler type assignment
7. Remove change log
8. Accommodations table
9. Full name to users

### Scripts (`/scripts`)

Utility scripts for database management.

- `seed_traveler_test.py` - Populate traveler test data
- `reset_traveler_test_data.py` - Reset test data
- `cleanup_soft_deletes.py` - Clean soft-deleted records

### Tests (`/tests`)

Test files and test data.

- Unit tests for graphs
- Integration tests for document analyzer
- Example files for testing

### Examples & Outputs (`/examples`)

Generated outputs from AI workflows for reference and debugging.

---

## 🏗️ Architecture Patterns

### Layered Architecture

```
┌─────────────────────────────────────┐
│         Routes (API Layer)          │  ← FastAPI endpoints
├─────────────────────────────────────┤
│      Services (Business Logic)      │  ← Business rules & orchestration
├─────────────────────────────────────┤
│       Models (Data Layer)           │  ← SQLAlchemy ORM
├─────────────────────────────────────┤
│         Database (PostgreSQL)       │  ← Data persistence
└─────────────────────────────────────┘
```

### AI Workflow Architecture

```
┌─────────────────────────────────────┐
│         LangGraph Graphs            │  ← Workflow orchestration
├─────────────────────────────────────┤
│         Agents & Tools              │  ← AI decision-making
├─────────────────────────────────────┤
│         Prompts                     │  ← Structured templates
├─────────────────────────────────────┤
│         LLM (OpenAI/Anthropic)      │  ← Language model
└─────────────────────────────────────┘
```

### Feature Organization

Each feature follows a consistent structure:

```
Feature/
├── models/feature.py       # Database model
├── schemas/feature.py      # Pydantic schemas
├── routes/feature.py       # API endpoints
└── services/feature.py     # Business logic
```

---

## 🔧 Technology Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy |
| **Database** | PostgreSQL |
| **Migrations** | Alembic |
| **AI Workflows** | LangGraph |
| **LLM** | OpenAI / Anthropic |
| **Authentication** | JWT + OAuth 2.0 |
| **Validation** | Pydantic |
| **Email** | SMTP / SendGrid |

---

## 📝 Naming Conventions

### Files
- **Models**: Singular noun (`user.py`, `itinerary.py`)
- **Routes**: Plural noun or feature name (`users.py`, `auth_routes.py`)
- **Services**: Same as routes (`users.py`)
- **Schemas**: Same as models (`user.py`)

### Database Tables
- **Table names**: Plural snake_case (`users`, `itineraries`, `user_social_accounts`)
- **Columns**: Snake_case (`created_at`, `email_verified`)

### Python Classes
- **Models**: Singular PascalCase (`User`, `Itinerary`)
- **Schemas**: Singular PascalCase with suffix (`UserCreate`, `UserResponse`)

---

## 🚀 Getting Started

### Prerequisites
```bash
# Python 3.13+
python --version

# PostgreSQL
psql --version
```

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Seed traveler test data
python scripts/seed_traveler_test.py

# Start server
uvicorn main:app --reload
```

---

## 📚 Related Documentation

- [Database Schema Diagram](./database-diagram.md)
- [API Documentation](http://localhost:8000/docs) (when server is running)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

*Last updated: October 2025*

