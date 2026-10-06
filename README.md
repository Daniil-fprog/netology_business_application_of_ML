# Домашнее задание по Бизнес-применению машинного обучения

## Тесты на hh:

### Скриншот 1
![Скриншот 1](hh/тест_hh_1.png)

### Скриншот 2
![Скриншот 2](hh/тест_hh_2.png)

### Скриншот 3
![Скриншот 3](hh/тест_hh_3.png)

### Скриншот 4
![Скриншот 4](hh/тест_hh_4.png)

### Скриншот 5
![Скриншот 5](hh/тест_hh_5.png)

### Скриншот 6
![Скриншот 6](hh/тест_hh_6.png)


## Wine Recommendation Service

MVP-сервис подбора вина. Он разбирает запрос на русском языке, фильтрует каталог и возвращает TOP-N. Content-based ML-модель обучает профиль пользователя на его лайках и поднимает похожие вина. Без лайков используется стандартный ranking.

### Архитектура

```text
JSON source -> WineSource -> normalize -> Repository -> PostgreSQL
User query -> QueryParser -> filter -> weighted ranking -> TOP-N -> API
User likes -> ML user profile -> cosine similarity -----^
```

- `api` — FastAPI routes и HTTP-схемы.
- `query_parser` — rule-based parser за интерфейсом `QueryParser`.
- `recommendation` — фильтрация и ranking.
- `ml` — обучение content-based модели и ML-scoring.
- `parser` — сменяемый `WineSource`, загрузчик JSON-мока и pipeline upsert.
- `db` — SQLAlchemy-модели и repository; `alembic` — миграции.

Ranking: `0.55 * rating + 0.25 * price_fit + 0.20 * popularity`. Веса задаются в `.env`.

### Требования

- Python 3.11+
- Poetry 2.x (`pipx install poetry`)
- PostgreSQL 16 или Docker + Docker Compose

### Быстрый запуск в Docker

```bash
cp .env.example .env
docker compose up --build
```

Веб-интерфейс: <http://localhost:8000>, Swagger UI: <http://localhost:8000/docs>. Контейнер применит миграции и запустит Uvicorn.

### Локальная установка

```bash
poetry install
cp .env.example .env
# для host-запуска заменить @db: на @localhost: в DATABASE_URL
docker compose up -d db
poetry run alembic upgrade head
poetry run uvicorn wine_recommendation.main:app --reload
```

### API

- `GET /health`
- `GET /wines`, `GET /wines/{id}`
- `GET /users`, `POST /users`
- `POST /users/{id}/likes`, `DELETE /users/{id}/likes/{wine_id}`
- `POST /recommendations`
- `POST /parser/update`
- `POST /ml/retrain`

```bash
curl -X POST http://localhost:8000/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"query":"красное сухое до 1500","limit":5}'
```

Для переобучения модели на текущем каталоге и лайках:

```bash
curl -X POST http://localhost:8000/ml/retrain
```

Поле `recommendation_mode` в ответе имеет значение `ml` или `standard`.

### Загрузка каталога

По умолчанию внешний парсер выключен, а локальный JSON-мок загружается в БД
автоматически после применения миграций при каждом старте API:

```dotenv
PARSER_ENABLED=false
MOCK_JSON_DATA=src/wine_recommendation/data/mock_wines.json
```

Встроенные моки содержат 100 вин, 20 пользователей и 120 лайков. Повторный
запуск контейнера безопасен: вина и пользователи обновляются, а лайки не
дублируются.
При `PARSER_ENABLED=true` автозагрузка локального мока пропускается, а endpoint
`POST /parser/update` становится доступен для ручного обновления.

### Качество кода

```bash
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy src tests
poetry run pre-commit install
poetry run pre-commit run --all-files
```

Тесты источника читают локальную fixture и не обращаются к реальному сайту.
