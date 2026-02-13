# GitLab Insights

<p align="center">
  <strong>All-in-One GitLab Project Analysis and Management Platform - A Vibe Coding Project</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Vibe_Coding-AI_Driven-ff69b4?style=for-the-badge" alt="Vibe Coding">
  <img src="https://img.shields.io/badge/AI-Claude_%2B_Copilot-blueviolet?style=for-the-badge&logo=github" alt="AI Powered">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1-green?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/Vue-3.4-brightgreen?logo=vue.js" alt="Vue 3">
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

<p align="center">
  <a href="README_CN.md">Chinese Documentation</a>
</p>

---

## What is Vibe Coding?

> *"You just see things, say things, run things, and copy-paste things, and it mostly works."*
>
> — Andrej Karpathy

**This project is a Vibe Coding practice.** The entire development process is a collaboration between a human developer and AI (GitHub Copilot / Claude). The developer defines requirements, sets direction, and reviews results, while AI handles code generation, architecture design, and refactoring.

- **Human-Driven Direction**: Defining feature requirements, technology choices, and product decisions
- **AI-Generated Code**: From backend APIs to frontend pages, from database models to deployment configs
- **Conversational Iteration**: Continuous improvement through natural language dialogue
- **Human Quality Assurance**: Running, testing, reviewing, and deploying

---

## Introduction

GitLab Insights is a full-stack web application for analyzing and managing GitLab project data. It provides GitLab API access monitoring, branch rule management, batch tag creation, work report generation, and more, helping teams manage GitLab projects more efficiently.

## Screenshots

| Dashboard | Branch Management |
|:---------:|:-----------------:|
| ![Dashboard](screenshots/dashboard.png) | ![Branches](screenshots/branches.png) |
| **Repository Management** | **Create Branch** |
| ![Repositories](screenshots/repositories.png) | ![Create Branch](screenshots/branch-create.png) |

## Extensible Micro-Frontend Architecture

This project adopts a **pluggable platform design**. The `shared/` module decouples authentication and user management into independent components that can be reused across multiple sub-applications:

```
                         +---------------------+
                         |   GitLab Insights    |
                         |  Main Frontend(Vue3) |
                         |   +---+---+---+      |
                         |   |Lnk|Lnk|Lnk|      |
                         |   +-+-+-+-+-+-+      |
                         +-----+-+-+-+-+--------+
                               |   |   |
              +----------------+   |   +----------------+
              v                    v                    v
     +----------------+  +----------------+   +-----------------+
     | GitLab Insight |  |   Jira Mgmt    |   |  Jenkins Mgmt   |
     | Backend(Flask) |  | Backend(Flask) |   | Backend(Flask)  |
     +-------+--------+  +-------+--------+   +-------+---------+
             |                   |                     |
             +-------------------+---------------------+
                                 v
                    +--------------------------+
                    |     shared/ Module       |
                    |  +----------------------+|
                    |  | auth_middleware.py   ||  JWT Token gen/verify
                    |  | (Auth Middleware)    ||  Common auth decorators
                    |  +----------------------+|
                    |  | user_model.py        ||  User query/create/perms
                    |  | (User Service)       ||  Cross-app data sharing
                    |  +----------------------+|
                    +------------+-------------+
                                 v
                    +--------------------------+
                    |  PostgreSQL (Shared DB)  |
                    |  User / Permission tables|
                    +--------------------------+
```

**Extend with a new app in 3 steps:**

1. **Backend**: Create a new Flask app and import the `shared/` module to gain authentication and user management capabilities
2. **Frontend**: Create an independent frontend project with its own pages and features
3. **Integration**: Add a navigation link in the GitLab Insights main frontend for a unified entry point

All sub-applications share the same user system and session (JWT), eliminating the need to re-implement authentication logic.

## Core Features

| Module | Description |
|--------|-------------|
| **Unified Auth** | LDAP-integrated login + JWT Token management (Access Token / Refresh Token) |
| **Data Sync** | Auto-sync GitLab projects and branches to local database, supporting full/incremental sync |
| **Batch Tag Creation** | Batch create GitLab tags with submodule tag support and task queue management |
| **Branch Rule Management** | Define/manage branch protection rules, auto-clean non-compliant branches, and track cleanup history |
| **Monitoring and Statistics** | API access log analysis, system performance monitoring, reports and visualization (ECharts) |
| **Work Reports** | Generate team work reports and export to Excel |
| **Task Management** | GitLab TODO integration, task list management |
| **Home Management** | Configurable homepage quick links |
| **Scheduled Jobs** | Automated task scheduling based on APScheduler |

## Tech Stack

### Backend

- **Web Framework:** Flask 3.1
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL (psycopg2 driver)
- **Authentication:** LDAP3 + PyJWT
- **GitLab API:** python-gitlab
- **Task Scheduling:** APScheduler
- **Data Export:** openpyxl (Excel)
- **Data Validation:** Pydantic
- **Testing:** pytest + pytest-cov

### Frontend

- **Framework:** Vue 3 (Composition API)
- **Build Tool:** Vite 5
- **UI Library:** Element Plus
- **State Management:** Pinia
- **Router:** Vue Router 4
- **HTTP Client:** Axios
- **Data Visualization:** ECharts / vue-echarts
- **Styling:** Sass

### Deployment

- **Containerization:** Docker (multi-stage build)

## Project Structure

```
gitlab_insights/
├── src/                          # Backend source code
│   ├── main.py                   # Flask application entry
│   ├── api/                      # API route layer
│   │   ├── auth_routes.py        # Auth routes (login/logout)
│   │   ├── gitlab_routes.py      # GitLab data sync routes
│   │   ├── tag_routes.py         # Tag creation management
│   │   ├── task_routes.py        # Task management routes
│   │   ├── branch_rule_routes.py # Branch rule management
│   │   ├── home_link_routes.py   # Home link management
│   │   ├── log_routes.py         # Log query routes
│   │   ├── monitoring_routes.py  # Monitoring & stats routes
│   │   ├── auth_decorators.py    # Auth decorators
│   │   └── response.py          # Unified response format
│   ├── services/                 # Business logic layer
│   │   ├── gitlab_service.py     # GitLab API interaction
│   │   ├── auth_service.py       # Auth service
│   │   ├── ldap_service.py       # LDAP service
│   │   ├── database_service.py   # Database operations
│   │   ├── branch_rule_service.py # Branch rule service
│   │   ├── task_service.py       # Task service
│   │   ├── export_service.py     # Data export (Excel)
│   │   ├── log_parser.py         # Log parser
│   │   ├── monitoring_service.py # Monitoring service
│   │   ├── scheduler.py          # Scheduled task scheduler
│   │   └── ...
│   ├── database/                 # Database layer
│   │   ├── connection.py         # Database connection management
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── dto/                      # Data Transfer Objects (Pydantic)
│   ├── config/                   # Configuration
│   │   ├── settings.py           # App settings (env variables)
│   │   ├── logging_config.py     # Logging configuration
│   │   └── ldap_config.py        # LDAP configuration
│   ├── middleware/               # Middleware
│   │   └── logging_middleware.py # HTTP request logging
│   ├── shared/                   # Shared modules
│   └── utils/                    # Utility functions
├── frontend/                     # Frontend source code
│   ├── src/
│   │   ├── main.js               # Vue app entry
│   │   ├── App.vue               # Root component
│   │   ├── views/                # Page components
│   │   │   ├── Dashboard.vue     # Dashboard
│   │   │   ├── Home.vue          # Home page
│   │   │   ├── gitlab/           # GitLab related pages
│   │   │   ├── tasks/            # Task management pages
│   │   │   └── logs/             # Log viewer pages
│   │   ├── components/           # Reusable components
│   │   ├── api/                  # API request wrappers
│   │   ├── router/               # Route configuration
│   │   ├── stores/               # Pinia state management
│   │   ├── layouts/              # Layout components
│   │   ├── styles/               # Global styles
│   │   └── utils/                # Frontend utilities
│   ├── index.html                # HTML entry
│   ├── vite.config.js            # Vite configuration
│   └── package.json              # Frontend dependencies
├── tests/                        # Test files
├── Dockerfile                    # Docker build file
├── requirements.txt              # Python dependencies
└── claude.md                     # AI-assisted development guide
```

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 14+

### 1. Clone the Repository

```bash
git clone https://github.com/azvvv/gitlab_insights.git
cd gitlab_insights
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gitlab_insight
DB_USER=postgres
DB_PASSWORD=your_password

# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your_gitlab_token

# LDAP Configuration
LDAP_SERVER=ldap://ldap.example.com
LDAP_BASE_DN=dc=example,dc=com
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=admin_password

# JWT Configuration
JWT_SECRET_KEY=your_secret_key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=86400

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000
```

### 3. Start the Backend

```bash
pip install -r requirements.txt
cd src
python main.py
```

The backend will be available at `http://localhost:5000`.

### 4. Start the Frontend (Development Mode)

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server will be available at `http://localhost:5173`.

### 5. Docker Deployment

```bash
docker build -t gitlab-insights:latest .
docker run -d -p 5000:5000 --env-file .env gitlab-insights:latest
```

> Docker uses a multi-stage build: first building the frontend static assets, then packaging them into the backend image. A single container serves both frontend and backend.

## API Overview

| Module | Path | Description |
|--------|------|-------------|
| Auth | `POST /api/auth/login` | User login |
| Auth | `POST /api/auth/logout` | User logout |
| Auth | `POST /api/auth/refresh` | Refresh token |
| GitLab | `POST /api/gitlab/sync` | Sync GitLab data |
| GitLab | `GET /api/gitlab/projects` | Get project list |
| GitLab | `GET /api/gitlab/branches` | Get branch list |
| Tags | `POST /api/tags/create` | Create tag task |
| Tags | `GET /api/tags/tasks` | Get tag task list |
| Branch Rules | `GET /api/branch-rules` | Get all rules |
| Branch Rules | `POST /api/branch-rules` | Create new rule |
| Monitoring | `GET /api/monitoring/stats` | Get statistics |
| Monitoring | `GET /api/monitoring/logs` | Query logs |

## Testing

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_database_service.py

# Generate coverage report
pytest --cov=src --cov-report=html
```

## Logging System

The application uses a layered logging system, with log files output to the `logs/` directory:

| Log File | Description |
|----------|-------------|
| `app.log` | Main application log |
| `error.log` | Error log |
| `access.log` | HTTP access log |
| `gitlab.log` | GitLab API call log |
| `security.log` | Security-related log |

## Development Guidelines

- **Python Style:** PEP 8, 4-space indentation
- **JS/Vue Style:** ESLint recommended rules, 2-space indentation
- **Naming Conventions:** Python `snake_case`, classes `PascalCase`, Vue components `PascalCase.vue`
- **Commit Messages:** `feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:`
- **Branch Strategy:** `main` (production), `develop` (development), `feature/*`, `hotfix/*`

## License

MIT
