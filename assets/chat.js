(function () {
  const API_BASE = (window.ELETROBAR_API || "").replace(/\/$/, "");
  const STORAGE_KEY = "eletrobar_chat_session_id";
  const WHATSAPP =
    "https://wa.me/5561993703294?text=" +
    encodeURIComponent("Olá! Vim pelo assistente de drinks do site e quero um orçamento.");

  const section = document.querySelector("#assistente");
  if (!section || !API_BASE) return;

  const form = section.querySelector("#chat-form");
  const input = section.querySelector("#chat-input");
  const log = section.querySelector("#chat-log");
  const leadBtn = section.querySelector("#chat-lead-btn");
  const statusEl = section.querySelector("#chat-status");
  const disclaimer = section.querySelector("#chat-disclaimer");

  function getSessionId() {
    let id = localStorage.getItem(STORAGE_KEY);
    if (!id && window.crypto?.randomUUID) {
      id = window.crypto.randomUUID();
      localStorage.setItem(STORAGE_KEY, id);
    }
    return id;
  }

  function appendMessage(role, text) {
    const item = document.createElement("div");
    item.className = `chat-bubble chat-bubble--${role}`;
    item.setAttribute("role", "article");
    const label = role === "user" ? "Você" : "Assistente";
    item.innerHTML =
      `<span class="chat-bubble-label">${label}</span>` +
      `<p class="chat-bubble-text"></p>`;
    item.querySelector(".chat-bubble-text").textContent = text;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
  }

  function setBusy(busy) {
    input.disabled = busy;
    form.querySelector("button[type=submit]").disabled = busy;
    if (leadBtn) leadBtn.disabled = busy;
    statusEl.textContent = busy ? "Enviando…" : "";
  }

  async function postJson(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data.detail || data.message || "Não foi possível conectar ao assistente.";
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  }

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    appendMessage("user", text);
    input.value = "";
    setBusy(true);
    try {
      const data = await postJson("/v1/chat", {
        message: text,
        session_id: getSessionId(),
      });
      if (data.session_id) {
        localStorage.setItem(STORAGE_KEY, data.session_id);
      }
      appendMessage("assistant", data.reply || "(sem resposta)");
    } catch (err) {
      appendMessage(
        "assistant",
        err.message ||
          "Assistente indisponível. Fale conosco no WhatsApp pelo botão abaixo."
      );
    } finally {
      setBusy(false);
      input.focus();
    }
  });

  leadBtn?.addEventListener("click", async () => {
    const sessionId = getSessionId();
    if (!sessionId) {
      appendMessage("assistant", "Envie pelo menos uma mensagem antes de solicitar orçamento.");
      return;
    }
    setBusy(true);
    try {
      const data = await postJson("/v1/lead", { session_id: sessionId });
      appendMessage("assistant", data.message || "Resumo enviado!");
      if (leadBtn) {
        leadBtn.hidden = true;
      }
      const link = document.createElement("a");
      link.className = "btn btn-primary chat-wa-fallback";
      link.href = WHATSAPP;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = "Abrir WhatsApp";
      disclaimer?.appendChild(link);
    } catch (err) {
      appendMessage(
        "assistant",
        err.message || "Não foi possível enviar. Use o WhatsApp."
      );
    } finally {
      setBusy(false);
    }
  });
})();
