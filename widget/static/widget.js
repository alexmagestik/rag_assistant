(function (global) {
  "use strict";

  const SESSION_KEY = "rag_widget_session_id";

  function getSessionId() {
    try {
      let id = sessionStorage.getItem(SESSION_KEY);
      if (!id) {
        id = crypto.randomUUID();
        sessionStorage.setItem(SESSION_KEY, id);
      }
      return id;
    } catch {
      return crypto.randomUUID();
    }
  }

  function icons() {
    return {
      chat: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>',
      close: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12"/></svg>',
      send: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>',
    };
  }

  function createWidget(root, options) {
    const {
      apiUrl,
      assetsBase,
      title = "Ассистент",
      subtitle = "Отвечаю по базе знаний компании",
      welcome = "Задайте вопрос — я найду ответ в документах компании.",
      primaryColor,
    } = options;

    if (primaryColor) {
      root.style.setProperty("--rag-primary", primaryColor);
      root.style.setProperty("--rag-user-bubble", primaryColor);
    }

    const container = document.createElement("div");
    container.className = "rag-widget";
    container.innerHTML = `
      <div class="rag-widget__panel" role="dialog" aria-label="${title}">
        <header class="rag-widget__header">
          <div>
            <h2 class="rag-widget__title">${escapeHtml(title)}</h2>
            <p class="rag-widget__subtitle">${escapeHtml(subtitle)}</p>
          </div>
          <button type="button" class="rag-widget__close" aria-label="Закрыть чат">${icons().close}</button>
        </header>
        <div class="rag-widget__messages" aria-live="polite"></div>
        <footer class="rag-widget__footer">
          <textarea class="rag-widget__input" rows="1" placeholder="Введите вопрос…" aria-label="Сообщение"></textarea>
          <button type="button" class="rag-widget__send" aria-label="Отправить">${icons().send}</button>
        </footer>
      </div>
      <button type="button" class="rag-widget__launcher" aria-label="Открыть чат">${icons().chat}</button>
    `;

    root.appendChild(container);

    const panel = container.querySelector(".rag-widget__panel");
    const messagesEl = container.querySelector(".rag-widget__messages");
    const input = container.querySelector(".rag-widget__input");
    const sendBtn = container.querySelector(".rag-widget__send");
    const launcher = container.querySelector(".rag-widget__launcher");
    const closeBtn = container.querySelector(".rag-widget__close");

    let isOpen = false;
    let isLoading = false;

    showWelcome();

    function escapeHtml(text) {
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }

    function showWelcome() {
      if (messagesEl.children.length > 0) return;
      const el = document.createElement("div");
      el.className = "rag-widget__welcome";
      el.textContent = welcome;
      messagesEl.appendChild(el);
    }

    function setOpen(open) {
      isOpen = open;
      panel.classList.toggle("rag-widget__panel--open", open);
      launcher.setAttribute("aria-expanded", String(open));
      if (open) {
        input.focus();
      }
    }

    function appendMessage(text, role) {
      const welcome = messagesEl.querySelector(".rag-widget__welcome");
      if (welcome) welcome.remove();

      const el = document.createElement("div");
      el.className = `rag-widget__message rag-widget__message--${role}`;
      el.textContent = text;
      messagesEl.appendChild(el);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return el;
    }

    function showTyping() {
      const el = document.createElement("div");
      el.className = "rag-widget__typing";
      el.setAttribute("data-typing", "1");
      el.innerHTML = "<span></span><span></span><span></span>";
      messagesEl.appendChild(el);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return el;
    }

    function hideTyping() {
      const el = messagesEl.querySelector("[data-typing]");
      if (el) el.remove();
    }

    function setLoading(loading) {
      isLoading = loading;
      sendBtn.disabled = loading;
      input.disabled = loading;
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text || isLoading) return;

      input.value = "";
      input.style.height = "auto";
      appendMessage(text, "user");
      setLoading(true);
      const typing = showTyping();

      try {
        const res = await fetch(`${apiUrl.replace(/\/$/, "")}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            session_id: getSessionId(),
          }),
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          const detail = data.detail;
          let msg = "Ошибка сервера";
          if (typeof detail === "string") {
            msg = detail;
          } else if (Array.isArray(detail) && detail[0]?.msg) {
            msg = detail[0].msg;
          }
          throw new Error(msg);
        }

        if (data.session_id) {
          try {
            sessionStorage.setItem(SESSION_KEY, data.session_id);
          } catch {
            /* ignore */
          }
        }

        appendMessage(data.answer, "bot");
      } catch (err) {
        appendMessage(
          err.message || "Не удалось получить ответ. Проверьте подключение.",
          "error"
        );
      } finally {
        hideTyping();
        setLoading(false);
      }
    }

    launcher.addEventListener("click", () => setOpen(!isOpen));
    closeBtn.addEventListener("click", () => setOpen(false));

    sendBtn.addEventListener("click", sendMessage);

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && isOpen) setOpen(false);
    });

    return { open: () => setOpen(true), close: () => setOpen(false) };
  }

  function mount(options) {
    const host = document.createElement("div");
    host.id = "rag-assistant-widget-host";
    document.body.appendChild(host);

    const shadow = host.attachShadow({ mode: "open" });
    const root = document.createElement("div");
    root.className = "rag-widget-root";
    shadow.appendChild(root);

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${options.assetsBase.replace(/\/$/, "")}/widget/widget.css`;
    shadow.appendChild(link);

    const api = createWidget(root, options);
    global.RagAssistantWidget = api;
    return api;
  }

  global.RagWidget = { mount, createWidget };
})(window);
