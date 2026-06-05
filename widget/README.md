# Встраиваемый виджет чата

Клиентская часть для диалога с RAG-ассистентом: плавающая кнопка и окно чата, подключаемые одной строкой на любой сайт.

Существующий код в `app/` **не изменяется** — виджет использует те же модули через отдельный HTTP-сервер в папке `widget/`.

---

## Быстрый старт

Из корня проекта (нужны `.env` с `OPENAI_API_KEY` и проиндексированная база):

```bash
pip install -r widget/requirements.txt
uvicorn widget.server:app --host 0.0.0.0 --port 8080
```

Откройте демо: [http://localhost:8080/](http://localhost:8080/)

---

## Встраивание на сайт

```html
<script
  src="http://localhost:8080/widget/embed.js"
  data-api-url="http://localhost:8080"
  data-title="Поддержка"
  data-subtitle="Задайте вопрос по услугам компании"
  data-primary-color="#0d9488"
></script>
```

| Атрибут | Описание |
|---------|----------|
| `data-api-url` | Базовый URL сервера виджета (обязателен при другом домене) |
| `data-assets-base` | URL статики, если CSS/JS отдаются с другого домена |
| `data-title` | Заголовок окна чата |
| `data-subtitle` | Подзаголовок в шапке |
| `data-welcome` | Приветственный текст в пустом чате |
| `data-primary-color` | Основной цвет (HEX) |

Стили изолированы через **Shadow DOM**, чтобы не конфликтовать с CSS сайта-хозяина.

---

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/health` | Статус и число чанков в базе |
| `POST` | `/api/chat` | Диалог: `{ "message": "...", "session_id": "..." }` |

Ответ чата:

```json
{
  "answer": "Текст ответа",
  "session_id": "uuid-сессии"
}
```

История диалога хранится на сервере по `session_id` (в браузере — `sessionStorage`).

---

## CORS

По умолчанию разрешены запросы с любого origin (`*`). Для продакшена задайте список доменов:

```bash
export WIDGET_CORS_ORIGINS="https://example.com,https://www.example.com"
```

---

## Файлы

```
widget/
├── server.py           # FastAPI: API + раздача static
├── requirements.txt    # fastapi, uvicorn
├── README.md
└── static/
    ├── embed.js        # Точка входа для <script> на сайте
    ├── widget.js       # Логика UI и запросы к API
    ├── widget.css      # Стили виджета
    └── demo.html       # Страница-пример
```

---

## Программный доступ

После загрузки доступен объект `window.RagAssistantWidget`:

```javascript
RagAssistantWidget.open();
RagAssistantWidget.close();
```
