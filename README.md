# RAG Ассистент

Приложение на Python с RAG (Retrieval-Augmented Generation) ассистентом. 
Отвечает на вопросы **строго** на основе локальной базы знаний, сформированной из текстовых файлов компании.

Доступны два интерфейса: **CLI** в терминале и **встраиваемый виджет** чата для сайта (`widget/`).

---

## Возможности

- 🔍 Семантический поиск по базе знаний (ChromaDB + OpenAI Embeddings)
- 🤖 Генерация ответов через GPT-4o-mini с жёстким ограничением на контекст
- 💬 Память диалога (последние N сообщений)
- ✏️ Опциональное переформулирование запроса для лучшего поиска
- ⚡ Кэш эмбеддингов (LRU + cosine similarity dedup)
- 📝 Логирование запросов и ответов
- 🌐 Встраиваемый виджет чата для сайта (Shadow DOM, HTTP API)
- 🧪 RAGAS-оценка качества (faithfulness, answer_relevancy, context_precision)

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone <repo-url>
cd rag-assistant
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Загрузить токенайзер NLTK (один раз)

```python
python -c "import nltk; nltk.download('punkt_tab')"
```

---

## Настройка `.env`

Скопируйте пример и добавьте ключ OpenAI:

```bash
cp .env.example .env
```

Откройте `.env` и заполните:

```
OPENAI_API_KEY=sk-ваш-ключ-здесь
```

---

## Добавление данных

Положите `.txt` файлы с текстами компании в папку `data/raw/`:

```
data/
└── raw/
    ├── company_info.txt
    ├── services.txt
    └── faq.txt
```

Файлы должны быть в кодировке **UTF-8**.

---

## Запуск

### CLI

```bash
python main.py
```

При первом запуске ассистент автоматически проиндексирует файлы из `data/raw/`.

### Виджет для сайта

HTTP-сервер с API и статикой виджета (из корня проекта, с настроенным `.env`):

```bash
pip install -r widget/requirements.txt
uvicorn widget.server:app --host 0.0.0.0 --port 8080
```

Демо-страница: [http://localhost:8080/](http://localhost:8080/)

Встраивание на любой сайт — одна строка:

```html
<script
  src="http://localhost:8080/widget/embed.js"
  data-api-url="http://localhost:8080"
  data-title="Поддержка"
></script>
```

Подробнее: атрибуты `data-*`, API, CORS — в [widget/README.md](widget/README.md).

### Доступные команды в режиме диалога (CLI)

| Команда  | Действие                                      |
|----------|-----------------------------------------------|
| `exit`   | Завершить работу ассистента                   |
| `reload` | Очистить и переиндексировать базу знаний      |

---

## Примеры использования

```
> Введите вопрос: Какие услуги предлагает компания?

╭─ Ответ ────────────────────────────────────────────────────────╮
│                                                                │
│  Компания предлагает следующие услуги:                         │
│  1. IT-консалтинг                                              │
│  2. Разработка программного обеспечения                        │
│  3. Техническая поддержка 24/7                                 │
│  4. Обучение сотрудников                                       │
│                                                                │
╰────────────────────────────────────────────────────────────────╯

> Введите вопрос: Где находится офис?

╭─ Ответ ────────────────────────────────────────────────────────╮
│  Главный офис расположен в Москве по адресу:                   │
│  ул. Тверская, д. 10, оф. 500.                                 │
╰────────────────────────────────────────────────────────────────╯

> Введите вопрос: Кто такой Илон Маск?

╭─ Ответ ────────────────────────────────────────────────────────╮
│  Я не нашёл информации по этому вопросу в базе знаний.         │
╰────────────────────────────────────────────────────────────────╯
```

---

## Структура проекта

```
rag-assistant/
│
├── app/
│   ├── cli/
│   │   └── interface.py        # CLI интерфейс (Rich)
│   ├── ingestion/
│   │   ├── chunker.py          # Разбивка текста на чанки
│   │   ├── loader.py           # Загрузка .txt файлов
│   │   └── pipeline.py         # Оркестрация: load → chunk → embed → store
│   ├── retrieval/
│   │   ├── retriever.py        # Поиск релевантных чанков
│   │   └── vectorstore.py      # ChromaDB обёртка
│   ├── generation/
│   │   ├── embedder.py         # OpenAI эмбеддинги + кэш
│   │   ├── generator.py        # ChatGPT генерация + rewrite
│   │   └── prompts.py          # Все промпты
│   ├── memory/
│   │   └── memory.py           # История диалога (deque)
│   ├── config/
│   │   └── settings.py         # Pydantic конфигурация из YAML
│   └── utils/
│       ├── cache.py            # LRU + cosine similarity кэш
│       └── logger.py           # Логирование запросов/ответов
│
├── data/
│   └── raw/                    # Исходные .txt файлы базы знаний
│
├── chroma_db/                  # Локальная векторная БД (создаётся автоматически)
├── logs/                       # Логи взаимодействий (создаётся автоматически)
│
├── tests/
│   ├── test_core.py            # Unit-тесты (pytest)
│   └── ragas_eval.py           # RAGAS оценка качества
│
├── widget/                     # Встраиваемый чат-виджет + HTTP API
│   ├── server.py               # FastAPI: /api/chat, раздача static
│   ├── requirements.txt        # fastapi, uvicorn
│   └── static/
│       ├── embed.js            # Точка входа для <script> на сайте
│       ├── widget.js           # UI и запросы к API
│       ├── widget.css
│       └── demo.html           # Демо-страница
│
├── config.yaml                 # Основная конфигурация
├── .env.example                # Пример переменных окружения
├── requirements.txt
└── main.py                     # Точка входа
```

---

## Конфигурация (`config.yaml`)

```yaml
llm:
  model: gpt-4o-mini       # Модель OpenAI
  temperature: 0.2          # Низкая температура = строгие ответы
  max_tokens: 800

embedding:
  model: text-embedding-3-small

retrieval:
  top_k: 5                  # Количество релевантных чанков

chunking:
  min_chunk_size: 300
  max_chunk_size: 1000
  overlap: 100              # Перекрытие между чанками

memory:
  max_history: 5            # Глубина истории диалога

cache:
  similarity_threshold: 0.92  # Порог cosine similarity для dedup
  max_size: 512               # Максимум записей в LRU кэше
```

---

## Тестирование

### Unit-тесты

```bash
pytest tests/test_core.py -v
```

### RAGAS оценка

```bash
python tests/ragas_eval.py
```

Результаты сохраняются в `tests/ragas_results.json`.

Метрики:
- **faithfulness** — ответ подкреплён контекстом
- **answer_relevancy** — ответ релевантен вопросу
- **context_precision** — точность retrieved контекста

---

## Расширяемость

Архитектура позволяет легко добавить:

| Расширение          | Где добавить                              |
|---------------------|-------------------------------------------|
| Telegram-бот        | Новый модуль `app/bot/`                   |
| Доработка виджета   | `widget/static/`, `widget/server.py`      |
| PDF / HTML файлы    | `app/ingestion/loader.py`                 |
| API как источник    | `app/ingestion/loader.py`                 |
| Веб-скрейпинг       | `app/ingestion/loader.py`                 |
| Другой LLM          | `app/generation/generator.py`             |

---

## Логирование

Логи сохраняются в `logs/assistant.log` в формате JSON (одна строка — одно взаимодействие):

```json
{"ts": "2024-01-15T10:30:00", "query": "Вопрос пользователя", "answer": "Ответ ассистента"}
```

Retrieved chunks намеренно **не логируются**.

---

## Требования

- Python 3.11+
- OpenAI API ключ
- ~500 MB дискового пространства для ChromaDB
