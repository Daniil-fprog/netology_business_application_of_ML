# Production-стандарты проекта Wine Recommendation Service

## Цель работы

ML-проект подготовлен к воспроизводимому запуску и дальнейшей разработке. Код разделён на независимые слои, зависимости зафиксированы, добавлены автоматические проверки и настроена работа с виртуальным окружением в Git-репозитории.

## 1. Рефакторинг кода под production-стандарты

Исходный код размещён в каталоге `src/wine_recommendation` и разделён по ответственности:

- `api` — маршруты FastAPI и схемы HTTP-запросов;
- `core` — конфигурация приложения и логирование;
- `db` — модели SQLAlchemy, подключение к PostgreSQL и repository;
- `parser` — чтение, нормализация и загрузка каталога вин;
- `recommendation` — фильтрация кандидатов и итоговый ranking;
- `ml` — content-based модель, векторы вин и профили пользователей;
- `static` — HTML, CSS и JavaScript веб-интерфейса.

Разделение позволяет независимо тестировать бизнес-логику и ML-модель. Например, расчёт рекомендаций можно проверить без запуска браузера, а ML-модель — без обращения к внешнему сайту.

### Используемые production-технологии

**FastAPI** создаёт HTTP API для каталога, пользователей, лайков, рекомендаций и переобучения модели. Pydantic проверяет входные данные до выполнения бизнес-логики.

**PostgreSQL и SQLAlchemy** отвечают за постоянное хранение вин, предложений, пользователей, лайков и истории рекомендаций. Работа с базой изолирована в repository.

**Alembic** хранит последовательность миграций и воспроизводимо создаёт структуру базы данных.

**Docker и Docker Compose** запускают API и PostgreSQL в одинаковом окружении. При старте контейнера применяются миграции, загружаются mock-данные и строится ML-модель.

**pytest** проверяет отдельные функции и интеграцию компонентов. Тесты покрывают фильтрацию, ranking, ML-score, fallback без лайков, repository, загрузку данных и API.

### Запуск проекта

```bash
# Создать локальные настройки
cp .env.example .env

# Собрать и запустить API и PostgreSQL
docker compose up --build -d

# Проверить состояние контейнеров
docker compose ps

# Проверить готовность API
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Веб-интерфейс доступен по адресу `http://localhost:8000`, документация API — `http://localhost:8000/docs`.

### Проверка production-структуры

```bash
# Применить миграции
poetry run alembic upgrade head

# Запустить все автоматические тесты
poetry run pytest

# Проверить импорт установленного пакета
poetry run python -c "import wine_recommendation; print(wine_recommendation.__file__)"

# Проверить сборку wheel и source archive
poetry build
```

На момент подготовки работы успешно выполняются 22 теста.

## 2. Poetry, pre-commit и линтеры

### Poetry

Poetry управляет зависимостями, виртуальным окружением и сборкой проекта.

- `pyproject.toml` содержит зависимости и настройки инструментов;
- `poetry.lock` фиксирует точные версии пакетов;
- `poetry run` запускает команду внутри окружения проекта.

Команды проверки Poetry:

```bash
# Установить зависимости
poetry install

# Проверить pyproject.toml
poetry check

# Показать сведения о виртуальном окружении
poetry env info

# Показать установленные пакеты
poetry show
```

### Ruff

Ruff используется как линтер и форматтер Python-кода. В проекте включены проверки ошибок, импортов, устаревших конструкций, потенциальных дефектов и возможностей упрощения кода.

```bash
# Проверить код
poetry run ruff check .

# Проверить форматирование
poetry run ruff format --check .

# Автоматически исправить доступные замечания
poetry run ruff check . --fix
poetry run ruff format .
```

### mypy

mypy статически проверяет аннотации типов. В `pyproject.toml` включён строгий режим, поэтому инструмент обнаруживает пропущенные типы и несовместимые аргументы до запуска приложения.

```bash
poetry run mypy src tests
```

### pytest

pytest запускает модульные и интеграционные тесты.

```bash
# Все тесты
poetry run pytest

# Подробный вывод
poetry run pytest -v

# Отдельные группы
poetry run pytest tests/unit
poetry run pytest tests/integration
```

### pre-commit

pre-commit автоматически запускает проверки перед созданием Git-коммита. Конфигурация находится в `.pre-commit-config.yaml`.

В проекте hooks выполняют следующие действия:

1. удаляют лишние пробелы и исправляют конец файла;
2. проверяют синтаксис YAML и TOML;
3. запускают Ruff;
4. запускают mypy;
5. запускают pytest.

Если проверка завершается с ошибкой, Git не создаёт коммит до исправления проблемы.

```bash
# Установить hooks в текущий Git-репозиторий
poetry run pre-commit install

# Проверить все файлы вручную
poetry run pre-commit run --all-files

# Запустить конкретную проверку
poetry run pre-commit run ruff --all-files
poetry run pre-commit run mypy --all-files
poetry run pre-commit run pytest --all-files
```

### Полная проверка качества

```bash
poetry check
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy src tests
poetry run pytest
poetry run pre-commit run --all-files
```

## 3. Интеграция виртуального окружения в Git

Виртуальное окружение содержит отдельный Python и пакеты проекта. Оно не смешивается с системными библиотеками и окружениями других проектов.

Сам каталог `.venv` не хранится в Git, потому что он занимает много места, зависит от операционной системы и полностью восстанавливается через Poetry.

В репозитории хранятся:

- `pyproject.toml` — список и настройки зависимостей;
- `poetry.lock` — их точные версии;
- `.env.example` — безопасный шаблон настроек.

В `.gitignore` добавлены:

```text
.venv/
.env
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
```

Файл `.env` может содержать локальные настройки и пароли, поэтому Git его не отслеживает. Для нового окружения используется `.env.example`.

### Создание `.venv` внутри проекта

```bash
# Настроить локальное окружение в каталоге проекта
poetry config virtualenvs.in-project true --local

# Создать окружение и установить зависимости
poetry install
```

### Команды проверки окружения и Git

```bash
# Показать путь и параметры окружения
poetry env info
poetry env info --path

# Проверить версию Python
poetry run python --version

# Показать используемый исполняемый файл Python
poetry run python -c "import sys; print(sys.executable)"

# Проверить, что Git игнорирует .venv
git check-ignore -v .venv/pyvenv.cfg

# Команда не должна вывести файлы
git ls-files .venv

# Проверить состояние репозитория
git status --short
```

Корректная интеграция означает, что Git хранит инструкции для воспроизведения окружения, но не хранит содержимое `.venv`.

## Итог

Проект получил модульную структуру, воспроизводимые зависимости и единый набор автоматических проверок. Poetry создаёт окружение, Ruff и mypy проверяют код, pytest проверяет поведение, а pre-commit запускает эти инструменты перед коммитом. Docker Compose обеспечивает одинаковый запуск API и PostgreSQL на разных машинах.
