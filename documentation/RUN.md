# Команды для запуска Wine Recommendation Service

Все команды ниже выполняются из корня проекта:

```bash
cd netology_business_application_of_ML
```

Основной и наиболее простой способ запуска — Docker Compose. Локальный запуск через Poetry приведён ниже как альтернативный вариант для разработки.

## Вариант 1. Запуск через Docker Compose

### 1. Создать файл настроек

```bash
cp .env.example .env
```

Команда создаёт локальный `.env` из примера. В нём находятся адрес базы данных, уровень логирования, настройки парсера и веса рекомендательного алгоритма. Файл `.env` не добавляется в Git.

Стандартный `DATABASE_URL` уже настроен для Docker:

```dotenv
DATABASE_URL=postgresql+psycopg://wine:wine@db:5432/wine
```

Здесь `db` — имя контейнера PostgreSQL внутри сети Docker Compose.

### 2. Собрать и запустить приложение

```bash
docker compose up --build
```

Команда:

1. скачивает образ PostgreSQL;
2. собирает Docker-образ API;
3. запускает PostgreSQL;
4. ожидает готовности базы данных;
5. выполняет `alembic upgrade head`;
6. запускает FastAPI через Uvicorn на порту `8000`.

После запуска доступны:

- веб-интерфейс: <http://localhost:8000>;
- документация Swagger: <http://localhost:8000/docs>;
- проверка состояния API: <http://localhost:8000/health>.

Терминал будет занят выводом логов. Остановить приложение можно сочетанием `Ctrl+C`.

### 3. Запуск в фоновом режиме

```bash
docker compose up --build -d
```

Флаг `-d` запускает контейнеры в фоне и возвращает управление терминалу.

Посмотреть логи после фонового запуска:

```bash
docker compose logs -f api
```

Флаг `-f` продолжает выводить новые сообщения. Для выхода из просмотра логов нажмите `Ctrl+C`; контейнеры продолжат работать.

### 4. Проверить API

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

### 5. Остановить контейнеры

```bash
docker compose down
```

Команда останавливает и удаляет контейнеры и внутреннюю сеть. Данные PostgreSQL сохраняются в Docker volume `postgres_data`.

Чтобы также удалить базу данных проекта:

```bash
docker compose down -v
```

Флаг `-v` удаляет volume вместе со всеми сохранёнными данными. Используйте эту команду только тогда, когда база больше не нужна.

## Вариант 2. Локальный запуск через Poetry

Для этого варианта нужны Python 3.11+, Poetry и запущенный PostgreSQL.

### 1. Установить зависимости

```bash
poetry install
```

Poetry создаёт виртуальное окружение и устанавливает точные версии зависимостей из `poetry.lock`, включая FastAPI, SQLAlchemy, Alembic и инструменты проверки кода.

### 2. Создать настройки

```bash
cp .env.example .env
```

Если API запускается на компьютере, а PostgreSQL — в Docker, в `.env` нужно заменить имя хоста `db` на `localhost`:

```dotenv
DATABASE_URL=postgresql+psycopg://wine:wine@localhost:5432/wine
```

### 3. Запустить только PostgreSQL

```bash
docker compose up -d db
```

Команда запускает контейнер базы данных без контейнера API. PostgreSQL будет доступен приложению на `localhost:5432`.

### 4. Применить миграции

```bash
poetry run alembic upgrade head
```

Alembic последовательно применяет миграции из каталога `alembic/versions` и создаёт таблицы пользователей, вин, предложений, лайков и событий рекомендаций.

Показать текущую версию схемы:

```bash
poetry run alembic current
```

Откатить последнюю миграцию:

```bash
poetry run alembic downgrade -1
```

Откат изменяет структуру базы данных и может привести к потере данных из удаляемых таблиц или колонок.

### 5. Запустить API

```bash
poetry run uvicorn wine_recommendation.main:app --reload --env-file .env
```

Uvicorn загружает настройки из `.env` и запускает FastAPI на <http://127.0.0.1:8000>. Флаг `--reload` автоматически перезапускает сервер после изменения Python-файлов и удобен только для разработки.

Production-подобный запуск без автоматической перезагрузки:

```bash
poetry run uvicorn wine_recommendation.main:app --host 0.0.0.0 --port 8000 --env-file .env
```

## Загрузка каталога вин

Перед включением парсера необходимо проверить правила источника, `robots.txt` и допустимость автоматизированного использования данных.

В `.env` нужно задать:

```dotenv
PARSER_ENABLED=true
PEREKRESTOK_API_URL=https://адрес-разрешённого-json-endpoint
PARSER_USER_AGENT=WineRecommendationMVP/0.1 (+your-email@example.com)
```

При локальном запуске выполнить:

```bash
poetry run dotenv run -- python scripts/update_parser.py
```

Команда `dotenv run` передаёт скрипту переменные из `.env`. Скрипт получает каталог через адаптер источника, нормализует записи и выполняет upsert: существующие вина обновляются, новые добавляются, а отсутствующие в полном снимке предложения отмечаются недоступными.

При запуске через Docker вызвать API парсера:

```bash
docker compose up -d --force-recreate api
curl -X POST http://localhost:8000/parser/update
```

Пересоздание контейнера API требуется, если настройки парсера были изменены в `.env` уже после запуска контейнеров.

Без `PARSER_ENABLED=true` endpoint вернёт HTTP 403. Без заполненного `PEREKRESTOK_API_URL` загрузка также не начнётся.

## Проверка рекомендаций из терминала

```bash
curl -X POST http://localhost:8000/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"query":"красное сухое до 1500","limit":5}'
```

API разбирает строку запроса, фильтрует доступные предложения, рассчитывает score и возвращает до пяти карточек. Если каталог ещё не загружен, массив `recommendations` будет пустым.

## Тесты и контроль качества

Запустить тесты:

```bash
poetry run pytest
```

Проверить Python-код линтером:

```bash
poetry run ruff check .
```

Проверить форматирование без изменения файлов:

```bash
poetry run ruff format --check .
```

Автоматически отформатировать Python-файлы:

```bash
poetry run ruff format .
```

Выполнить статическую проверку типов:

```bash
poetry run mypy src tests
```

Запустить все pre-commit проверки вручную:

```bash
poetry run pre-commit run --all-files
```

Установить автоматический запуск проверок перед каждым Git-коммитом:

```bash
poetry run pre-commit install
```

## Полезные команды Docker

Показать состояние контейнеров:

```bash
docker compose ps
```

Перезапустить только API:

```bash
docker compose restart api
```

Открыть shell внутри API-контейнера:

```bash
docker compose exec api sh
```

Открыть PostgreSQL-консоль:

```bash
docker compose exec db psql -U wine -d wine
```

Пересобрать API после изменения зависимостей или Dockerfile:

```bash
docker compose up -d --build api
```
