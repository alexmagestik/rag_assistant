(function () {
  "use strict";

  var script = document.currentScript;
  if (!script) {
    console.error("[RAG Widget] embed.js must be loaded with a <script> tag.");
    return;
  }

  var scriptUrl = new URL(script.src, window.location.href);
  var assetsBase = script.getAttribute("data-assets-base") || scriptUrl.origin;
  var apiUrlAttr = script.getAttribute("data-api-url");
  var apiUrl = apiUrlAttr && apiUrlAttr.trim() ? apiUrlAttr.trim() : assetsBase;

  var config = {
    apiUrl: apiUrl,
    assetsBase: assetsBase,
    title: script.getAttribute("data-title") || "Ассистент",
    subtitle: script.getAttribute("data-subtitle") || "Отвечаю по базе знаний компании",
    welcome: script.getAttribute("data-welcome") || undefined,
    primaryColor: script.getAttribute("data-primary-color") || undefined,
  };

  function loadWidget() {
    if (window.RagWidget) {
      window.RagWidget.mount(config);
      return;
    }
    var widgetScript = document.createElement("script");
    widgetScript.src = assetsBase.replace(/\/$/, "") + "/widget/widget.js";
    widgetScript.async = true;
    widgetScript.onload = function () {
      window.RagWidget.mount(config);
    };
    widgetScript.onerror = function () {
      console.error("[RAG Widget] Failed to load widget.js from", widgetScript.src);
    };
    document.head.appendChild(widgetScript);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadWidget);
  } else {
    loadWidget();
  }
})();
