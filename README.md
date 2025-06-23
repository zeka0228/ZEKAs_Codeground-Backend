# Codeground Backend

This repository contains a FastAPI based backend service. It provides authentication APIs and uses PostgreSQL through SQLAlchemy and Alembic for migrations.

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- PostgreSQL instance

## Installation

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd Codeground-Backend
   ```

2. **Install dependencies**

   Use Poetry to install the project requirements:

   ```bash
   poetry install
   ```

3. **Configure environment variables**

   The application loads variables from a `.env` file located **one directory above** the project root. Create `../.env` relative to the repository with values similar to the following:

   ```env
   SECRET_KEY=your-secret-key
   SECRET_KEY_AUTH=your-auth-key
   DB_HOST=localhost
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=codeground
   ```

   These variables are used to construct the database URL for PostgreSQL.

4. **Database setup**

   Initialize the database using Alembic. If no migration files exist, create one:

   ```bash
   alembic revision --autogenerate -m "init"
   alembic upgrade head
   ```

## Running the Service

Start the FastAPI application with Uvicorn:

```bash
poetry run uvicorn src.app.main:app --reload
```

The API will be available at `http://localhost:8000/`. Authentication endpoints are prefixed with `/api/v1` (e.g. `/api/v1/auth/sign-up`).

