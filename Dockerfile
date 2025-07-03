# 1. Python 3.11.9 slim 기반
FROM python:3.11.9-slim

ARG TZ=Asia/Seoul
ENV TZ=${TZ} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.3 \
    # Poetry가 venv를 따로 만들지 않도록(레이어 수·용량 감소)
    POETRY_VIRTUALENVS_CREATE=false

# pg_config와 컴파일러·헤더를 한꺼번에 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential gcc libpq-dev curl && \
    curl -sSL https://install.python-poetry.org | python - && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory
WORKDIR /

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock README.md ./

# Copy the project files
COPY src/ ./src

# Install dependencies using Poetry
RUN poetry install --only main --no-interaction --no-ansi

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the FastAPI application
CMD ["poetry", "run", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
