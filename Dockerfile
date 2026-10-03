FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.1.1 && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root --no-interaction
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY src ./src
RUN poetry install --only-root --no-interaction
CMD ["uvicorn", "wine_recommendation.main:app", "--host", "0.0.0.0", "--port", "8000"]
