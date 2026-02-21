# Виртуальный помощник для интерактивного изучения казахского языка

Дипломный проект. Веб-приложение для изучения казахского языка с виртуальным помощником, уроками, упражнениями и тестами.

## Быстрый старт (в Cursor)

Открой проект в Cursor и в чате напиши:

**«Установи зависимости и запусти проект»**

Cursor установит пакеты из `requirements.txt` и запустит сервер. Открой в браузере: **http://127.0.0.1:8000**

Либо запусти вручную из корня проекта:

- **Windows:** `.\run.ps1`
- **Mac/Linux:** `chmod +x run.sh && ./run.sh`

## Технологии

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, JWT
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **БД:** SQLite (локально) / PostgreSQL (продакшен)

## Установка и запуск

### 1. Виртуальное окружение

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Зависимости

```bash
pip install -r requirements.txt
```

### 3. База данных

Таблицы создаются автоматически при запуске. Для миграций Alembic:

```bash
alembic upgrade head
```

### 4. Начальные данные (опционально)

```bash
# Админ + пример
python -m scripts.seed_data
```

Создаётся: админ `admin@example.com` / `admin123`, пример урока.

### 5. Полный контент для обучения (рекомендуется)

```bash
# Создать расширенный словарь (опционально, для ~3000 слов)
python -m scripts.create_vocabulary_bulk

# Загрузить уроки, упражнения, тесты и словарь
python -m scripts.seed_content
```

Создаётся:
- ~1400+ слов словаря (казахский–русский)
- 60 уроков (A1: 20, A2: 20, B1: 20)
- 600+ упражнений
- 60 тестов с вопросами

Скрипты идемпотентны — безопасно запускать несколько раз

### 6. Запуск сервера

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Приложение: http://localhost:8000  
API docs: http://localhost:8000/docs

## Роли

- **student** — доступ к урокам, упражнениям, тестам, помощнику, словарю
- **teacher** — то же + создание и редактирование контента
- **admin** — полный доступ + просмотр логов

## Структура проекта

```
/app
  /auth      — аутентификация
  /users     — профиль пользователя
  /lessons   — уроки
  /exercises — упражнения
  /tests     — тесты
  /assistant — виртуальный помощник (rule-based)
  /vocabulary — личный словарь
  /progress  — прогресс и статистика
  /recommendations — рекомендации
  /logging_mod — логирование действий
  /files     — импорт/экспорт контента
  /core      — конфиг, БД, безопасность
main.py
frontend/    — HTML, CSS, JS
```
