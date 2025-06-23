# Codeground 백엔드

이 저장소는 FastAPI 기반의 백엔드 서비스입니다. 인증 API를 제공하며 데이터베이스 마이그레이션을 위해 SQLAlchemy와 Alembic을 사용합니다.

## 요구 사항

- Python 3.11+
- 의존성 관리를 위한 [Poetry](https://python-poetry.org/)
- PostgreSQL 인스턴스

## 설치

1. **레포지토리 클론**

   ```bash
   git clone <repo-url>
   cd Codeground-Backend
   ```

2. **의존성 설치**

   Poetry로 프로젝트 의존성을 설치합니다:

   ```bash
   poetry install
   ```

3. **환경 변수 설정**

   애플리케이션은 프로젝트 루트 **상위 디렉터리에** 위치한 `.env` 파일에서 변수를 로드합니다. 다음과 같이 `../.env` 파일을 생성합니다:

   ```env
   SECRET_KEY=your-secret-key
   SECRET_KEY_AUTH=your-auth-key
   DB_HOST=localhost
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=codeground
   ```

   이 변수들은 PostgreSQL 연결 URL을 구성하는 데 사용됩니다.

4. **데이터베이스 설정**

   Alembic을 사용하여 데이터베이스를 초기화합니다. 마이그레이션 파일이 없다면 생성합니다:

   ```bash
   alembic revision --autogenerate -m "init"
   alembic upgrade head
   ```

## 서비스 실행

Uvicorn으로 FastAPI 애플리케이션을 실행합니다:

```bash
poetry run uvicorn src.app.main:app --reload
```

API는 `http://localhost:8000/`에서 확인할 수 있으며, 인증 엔드포인트는 `/api/v1` 로 시작합니다 (예: `/api/v1/auth/sign-up`).
