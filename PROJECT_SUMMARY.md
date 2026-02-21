# Полное описание проекта: Виртуальный помощник для изучения казахского языка

Дипломный проект — веб-приложение для интерактивного изучения казахского языка с виртуальным помощником, уроками, упражнениями, тестами и словарём.

---

## 1. Технологический стек

| Слой | Технологии |
|------|------------|
| **Backend** | Python, FastAPI, SQLAlchemy 2.0, Alembic |
| **Frontend** | HTML, CSS, JavaScript (vanilla, SPA) |
| **БД** | SQLite (локально) / PostgreSQL (продакшен) |
| **Auth** | JWT, python-jose, passlib (bcrypt) |

---

## 2. Структура проекта

```
/app
  /auth         — регистрация, логин, JWT
  /users        — профиль пользователя
  /lessons      — уроки, prerequisite-цепочки
  /exercises    — упражнения по урокам
  /tests        — тесты, попытки, вопросы
  /assistant    — rule-based виртуальный помощник
  /vocabulary   — личный словарь, игра
  /progress     — сводка прогресса
  /recommendations — рекомендации
  /logging_mod  — логи действий (admin)
  /files        — импорт/экспорт контента
  /core         — config, DB, security, deps
  /models       — User, Lesson, Exercise, Test, Vocabulary и др.
frontend/       — HTML, CSS, JS
scripts/        — seed_data, seed_content, create_admin и др.
data/           — vocabulary.csv, JSON для загрузки
```

---

## 3. Роли и доступ

| Роль | Возможности |
|------|-------------|
| **student** | Уроки, упражнения, тесты, помощник, словарь, прогресс |
| **teacher** | Всё то же + создание/редактирование уроков, упражнений, тестов, импорт контента |
| **admin** | Всё то же + просмотр логов |

---

## 4. Модели данных

### User
- email, hashed_password, full_name
- role: student | teacher | admin
- language_level, interface_language
- is_active, created_at, updated_at

### Lesson
- title, level (A1/A2/B1), topic, content (текст Markdown-подобный)
- order_index
- LessonPrerequisite — связи «урок X требует урок Y»
- LessonCompletion — отметки о прохождении

### Exercise
- lesson_id, title, description
- content (JSON: тип, вопрос, правильный ответ)
- order_index
- ExerciseAttempt — попытки с user_answer, is_correct

### Test
- lesson_id, title, description
- passing_score (%), is_final (итоговый тест урока)
- TestQuestion — вопрос, content (JSON: options, correct_answer)
- TestAttempt, TestAttemptAnswer — прохождение теста

### Vocabulary
- word_kz, translation_ru, transcription, example_sentence
- UserVocabulary — личный словарь: status (learning/learned), mastery

### Recommendation
- user_id, recommendation_type, title, description
- target_lesson_id, target_exercise_id

### Log
- user_id, action, entity_type, entity_id, details, created_at

---

## 5. API (основные эндпоинты)

### Auth
- `POST /api/auth/login` — вход
- `POST /api/auth/register` — регистрация

### Users
- `GET /api/users/me` — текущий пользователь
- `PATCH /api/users/me` — обновление профиля

### Lessons
- `GET /api/lessons/` — список уроков с is_locked
- `GET /api/lessons/{id}` — урок
- `GET /api/lessons/{id}/next` — следующий урок
- `POST /api/lessons/{id}/complete` — отметить урок пройденным (с проверкой итогового теста)
- `POST /api/lessons/` — создать урок (teacher/admin)
- `PUT /api/lessons/{id}` — обновить урок
- `DELETE /api/lessons/{id}` — удалить урок

### Exercises
- `GET /api/exercises/?lesson_id=` — список упражнений
- `GET /api/exercises/{id}` — упражнение
- `POST /api/exercises/{id}/attempt` — отправить ответ
- `POST /api/exercises/` — создать (teacher/admin)
- `PUT`, `DELETE` — обновить/удалить

### Tests
- `GET /api/tests/?lesson_id=` — список тестов
- `GET /api/tests/{id}` — тест
- `GET /api/tests/{id}/questions` — вопросы теста
- `POST /api/tests/{id}/attempt` — начать попытку
- `POST /api/tests/attempts/{id}/submit` — отправить ответы
- `GET /api/tests/attempts/{id}` — детали попытки
- `POST /api/tests/` — создать тест (teacher/admin)
- `PUT`, `DELETE` — обновить/удалить тест

### Assistant
- `POST /api/assistant/chat` — чат с помощником (message, context)

### Vocabulary
- `GET /api/vocabulary/` — личный словарь
- `POST /api/vocabulary/` — добавить слово
- `PATCH /api/vocabulary/{id}` — обновить статус
- `DELETE /api/vocabulary/{id}` — удалить
- `GET /api/vocabulary/game/next` — следующий вопрос для игры
- `POST /api/vocabulary/game/answer` — ответ в игре

### Progress
- `GET /api/progress/summary` — сводка (уроки, упражнения, тесты, словарь)

### Recommendations
- `GET /api/recommendations/` — список рекомендаций
- `PATCH /api/recommendations/{id}/read` — отметить прочитанным

### Files (teacher/admin)
- `POST /api/files/import/lessons` — импорт уроков (JSON)
- `POST /api/files/import/vocabulary` — импорт словаря (CSV)
- `GET /api/files/export/lessons` — экспорт уроков

### Logs (admin)
- `GET /api/logs/` — список логов действий

---

## 6. Frontend (SPA)

### Страницы
- `/login`, `/register` — вход и регистрация
- `/dashboard` — приветствие, статистика, быстрые действия
- `/lessons` — список уроков с блокировкой по prerequisite
- `/lesson/{id}` — содержимое урока, кнопка «Завершить»
- `/exercises` — список упражнений по урокам
- `/tests` — список тестов
- `/chat` — чат с виртуальным помощником
- `/vocabulary` — личный словарь, игра
- `/progress` — прогресс и статистика
- `/admin` — панель преподавателя (ссылка на API docs)

### Навигация
- Одна HTML-страница `dashboard.html`, роутинг на стороне клиента
- JWT в localStorage, проверка при загрузке
- Отображение ссылки «Админ» только для teacher/admin

### API-клиент (`frontend/js/api.js`)
- Методы для auth, users, lessons, exercises, tests, assistant, vocabulary, progress, recommendations
- Bearer token в заголовках

---

## 7. Виртуальный помощник (rule-based)

**Принцип:** без LLM, только данные платформы. Логика объяснима, подходит для дипломной защиты.

### Источники знаний
- Словарь платформы (поиск по word_kz, translation_ru)
- Контент уроков (цель, грамматика, частые ошибки)
- Правила A1 (порядок слов, аффиксы, формальность, настоящее время)

### Интенты
1. **vocabulary_question** — перевод слова
2. **grammar_question** — грамматические вопросы
3. **error_explanation** — объяснение ошибки (из урока или общее)
4. **general_help** — приветствие, помощь
5. **unknown** — отказ, предложение задать конкретный вопрос

### Режимы контекста
- `free` — свободный чат
- `lesson` — учёт lesson_id, ответы с учётом контента урока
- `vocabulary` — игра со словами
- `test` — **не даёт переводов и ответов**, только подсказки

### Функции
- Нормализация написания (рахмет→рақмет, салем→сәлем)
- Извлечение слова из кавычек
- Подсказки (добавить в словарь, перечитать урок, игра)

Подробности: `VIRTUAL_ASSISTANT_REPORT.md`, `ASSISTANT_QA_REPORT.md`

---

## 8. Скрипты

| Скрипт | Описание |
|--------|----------|
| `scripts/seed_data` | Админ admin@example.com / admin123, пример урока |
| `scripts/seed_content` | ~3000 слов, 60 уроков, 600+ упражнений, 60 тестов |
| `scripts/create_admin` | Создание админа |
| `scripts/create_vocabulary_bulk` | Расширение словаря |
| `scripts/expand_vocabulary_extended` | Дополнительный словарь |
| `scripts/test_assistant` | Тесты помощника |

---

## 9. Установка и запуск

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_data
python -m scripts.seed_content   # полный контент
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Приложение: http://localhost:8000  
API docs: http://localhost:8000/docs

---

## 10. Текущее состояние админ-панели

- Эндпоинты для создания уроков и тестов (teacher/admin) реализованы в API
- Импорт уроков и словаря через `/api/files/import/*`
- В UI `/admin` пока только карточка со ссылкой на Swagger docs
- Формы «Добавить урок» и «Добавить тест» можно реализовать через Swagger или отдельный UI

---

## 11. Резюме

Реализована полнофункциональная платформа изучения казахского языка:

- **Авторизация** — регистрация, логин, JWT, роли
- **Уроки** — цепочки с prerequisite, отметка о прохождении, итоговые тесты
- **Упражнения** — попытки, учёт правильности
- **Тесты** — вопросы, попытки, проходной балл, итоговые тесты
- **Словарь** — личный словарь, игра на запоминание
- **Виртуальный помощник** — rule-based, без LLM, с контекстом урока и режима теста
- **Прогресс** — сводка по урокам, упражнениям, тестам, словарю
- **Рекомендации** — система рекомендаций
- **Логи** — просмотр действий (admin)
- **Импорт/экспорт** — уроки (JSON), словарь (CSV)
