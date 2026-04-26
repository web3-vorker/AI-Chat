/* eslint-disable no-console */

const $ = (sel) => document.querySelector(sel);

const ui = {
  chatList: $("#chatList"),
  chatListSkeleton: $("#chatListSkeleton"),
  chatSearch: $("#chatSearch"),
  newChatBtn: $("#newChatBtn"),
  refreshBtn: $("#refreshBtn"),
  deleteChatBtn: $("#deleteChatBtn"),
  thread: $("#thread"),
  threadEmpty: $("#threadEmpty"),
  chatTitle: $("#chatTitle"),
  chatMeta: $("#chatMeta"),
  messageInput: $("#messageInput"),
  sendBtn: $("#sendBtn"),
  counter: $("#counter"),
  status: $("#status"),
  statusText: $("#statusText"),
  settingsBtn: $("#settingsBtn"),
  settingsDlg: $("#settingsDlg"),
  logoutBtn: $("#logoutBtn"),
  sidebarToggle: $("#sidebarToggle"),
  sidebarOverlay: $("#sidebarOverlay"),
  side: $(".side"),
};

const store = {
  get(key, fallback = null) {
    try {
      const v = localStorage.getItem(key);
      return v === null ? fallback : v;
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, String(value));
    } catch {
      // ignore
    }
  },
  del(key) {
    try {
      localStorage.removeItem(key);
    } catch {
      // ignore
    }
  },
};

const state = {
  chats: [],
  activeChatId: Number(store.get("activeChatId", "0")) || null,
  loading: false,
  sending: false,
  accessToken: store.get("accessToken", null),
};

// Initialize application
async function boot() {
  const token = store.get("accessToken");
  if (token) {
    state.accessToken = token;
  }

  try {
    setStatus("busy", "Загружаю чаты…");
    await loadChats({ keepActive: true });

    if (state.activeChatId) {
      const chat = state.chats.find((c) => c.id === state.activeChatId);
      if (chat) {
        await loadMessages(state.activeChatId);
      }
    }

    setStatus("ok", "Готово");
  } catch (e) {
    console.error("Failed to load chats on boot:", e);
    if (e?.status === 401) {
      store.del("accessToken");
      state.accessToken = null;
      window.location.href = "/login.html";
      return;
    }
    setStatus("err", e.message || "Ошибка загрузки чатов");
  } finally {
    updateComposer();
  }
}

function apiBase() {
  const saved = (store.get("apiBase", "") || "").trim();
  if (saved) return saved.replace(/\/+$/, "");
  const isLocalhost =
    location.hostname === "127.0.0.1" || location.hostname === "localhost";
  if (isLocalhost) {
    if (location.port === "8000") return "";
    return "http://127.0.0.1:8000";
  }
  // Production: use config from window.APP_CONFIG if available and not a placeholder
  if (
    window.APP_CONFIG &&
    window.APP_CONFIG.BACKEND_URL &&
    window.APP_CONFIG.BACKEND_URL !== "__BACKEND_URL__"
  ) {
    return window.APP_CONFIG.BACKEND_URL.replace(/\/+$/, "");
  }
  // Fallback: use same-origin proxy (/api/*) by default
  return "";
}

function apiPrefix() {
  const saved = (store.get("apiBase", "") || "").trim();
  if (saved) return "";
  const isLocalhost =
    location.hostname === "127.0.0.1" || location.hostname === "localhost";
  if (isLocalhost && location.port === "8000") return "/api";
  if (isLocalhost) return "";
  return "/api";
}

async function apiFetch(path, { method = "GET", json = null } = {}) {
  const headers = {};
  if (json !== null) headers["Content-Type"] = "application/json";
  if (state.accessToken) headers["Authorization"] = `Bearer ${state.accessToken}`;

  const res = await fetch(`${apiBase()}${apiPrefix()}${path}`, {
    method,
    headers,
    body: json !== null ? JSON.stringify(json) : null,
    credentials: "include",
  });

  if (!res.ok) {
    // Если 401 - перенаправляем на логин
    if (res.status === 401) {
      store.del("accessToken");
      window.location.href = "/login.html";
      return;
    }

    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data && data.detail) detail = data.detail;
    } catch {
      // ignore
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return await res.json();
  return await res.text();
}

function setStatus(kind, text) {
  ui.status.classList.remove("status--busy", "status--ok", "status--err");
  if (kind) ui.status.classList.add(`status--${kind}`);
  ui.statusText.textContent = text;
}

function fmtDate(s) {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return String(s);
  return d.toLocaleString(undefined, { hour12: false });
}

function clampTitle(t) {
  const title = (t || "").trim() || "New chat";
  return title.length > 64 ? `${title.slice(0, 61)}…` : title;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

function renderLightMarkdown(text) {
  const raw = String(text ?? "");
  const escaped = escapeHtml(raw);

  // code blocks ```...```
  const parts = escaped.split(/```/);
  let html = "";
  for (let i = 0; i < parts.length; i++) {
    const chunk = parts[i];
    if (i % 2 === 1) {
      html += `<pre><code>${chunk}</code></pre>`;
    } else {
      // inline code `...`
      const inline = chunk.replace(/`([^`]+)`/g, (_m, g1) => `<code>${g1}</code>`);
      // links (very light) https://...
      const linked = inline.replace(
        /(https?:\/\/[^\s<]+)/g,
        (m) => `<a href="${m}" target="_blank" rel="noreferrer noopener">${m}</a>`,
      );
      html += linked.replace(/\n/g, "<br/>");
    }
  }
  return html;
}

function clearThread() {
  [...ui.thread.querySelectorAll(".msg")].forEach((n) => n.remove());
}

function addMessage({ role, content, created_at }) {
  const el = document.createElement("article");
  el.className = "msg";

  const top = document.createElement("div");
  top.className = "msg__top";

  const pill = document.createElement("div");
  const isUser = role === "user";
  const isAssistant = role === "assistant";
  pill.className = `pill ${isUser ? "pill--user" : isAssistant ? "pill--assistant" : ""}`;
  pill.innerHTML = `<span class="pill__dot"></span><span>${role}</span>`;

  const ts = document.createElement("div");
  ts.className = "ts";
  ts.textContent = fmtDate(created_at);

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = renderLightMarkdown(content);

  top.appendChild(pill);
  top.appendChild(ts);
  el.appendChild(top);
  el.appendChild(bubble);

  ui.thread.appendChild(el);
}

function scrollToBottom() {
  ui.thread.scrollTop = ui.thread.scrollHeight;
}

function setActiveChat(chat) {
  state.activeChatId = chat ? chat.id : null;
  store.set("activeChatId", state.activeChatId || "");

  ui.deleteChatBtn.disabled = !state.activeChatId;
  ui.chatTitle.textContent = chat ? clampTitle(chat.title) : "Выберите чат";
  ui.chatMeta.textContent = chat ? `#${chat.id} • обновлён: ${fmtDate(chat.updated_at)}` : "—";
}

function renderChatList() {
  const q = (ui.chatSearch.value || "").trim().toLowerCase();
  ui.chatList.innerHTML = "";

  const chats = state.chats.filter((c) => {
    if (!q) return true;
    return String(c.title || "").toLowerCase().includes(q) || String(c.id).includes(q);
  });

  if (!chats.length) {
    const empty = document.createElement("div");
    empty.className = "hint";
    empty.innerHTML =
      '<div class="hint__dot"></div><div class="hint__text">Чаты не найдены. Создайте новый чат.</div>';
    ui.chatList.appendChild(empty);
    return;
  }

  for (const c of chats) {
    const item = document.createElement("div");
    item.className = `chatitem ${state.activeChatId === c.id ? "chatitem--active" : ""}`;
    item.dataset.chatId = String(c.id);

    const left = document.createElement("div");
    const title = document.createElement("div");
    title.className = "chatitem__title";
    title.textContent = clampTitle(c.title);

    const meta = document.createElement("div");
    meta.className = "chatitem__meta";
    meta.innerHTML = `<span class="chatitem__id">#${c.id}</span><span class="chatitem__time">${fmtDate(
      c.updated_at,
    )}</span>`;

    left.appendChild(title);
    left.appendChild(meta);

    const badge = document.createElement("div");
    badge.className = "chatitem__badge";
    badge.textContent = "chat";

    item.appendChild(left);
    item.appendChild(badge);

    item.addEventListener("click", async () => {
      await openChat(c.id);
    });

    ui.chatList.appendChild(item);
  }
}

async function loadChats({ keepActive = true } = {}) {
  ui.chatListSkeleton.style.display = "block";
  try {
    const chats = await apiFetch("/chats");
    state.chats = Array.isArray(chats) ? chats : [];

    if (!keepActive) state.activeChatId = null;

    if (state.activeChatId && !state.chats.some((c) => c.id === state.activeChatId)) {
      state.activeChatId = null;
    }

    renderChatList();
  } finally {
    ui.chatListSkeleton.style.display = "none";
  }
}

async function loadMessages(chatId) {
  const msgs = await apiFetch(`/chats/${chatId}/messages`);
  clearThread();
  ui.threadEmpty.style.display = "none";
  for (const m of msgs || []) addMessage(m);
  scrollToBottom();
}

async function openChat(chatId) {
  const chat = state.chats.find((c) => c.id === chatId) || null;
  setActiveChat(chat);
  renderChatList();
  await loadMessages(chatId);

  // Закрываем сайдбар на мобильных после выбора чата
  if (window.innerWidth < 768) {
    toggleSidebar(false);
  }
}

async function createChat() {
  setStatus("busy", "Создаю чат…");
  const chat = await apiFetch("/chats", { method: "POST" });
  await loadChats({ keepActive: false });
  setActiveChat(chat);
  renderChatList();
  clearThread();
  ui.threadEmpty.style.display = "none";
  scrollToBottom();
  setStatus("ok", "Чат создан");
  return chat;
}

async function deleteActiveChat() {
  if (!state.activeChatId) return;
  const id = state.activeChatId;
  const ok = confirm(`Удалить чат #${id}? Это удалит всю историю.`);
  if (!ok) return;

  setStatus("busy", "Удаляю чат…");
  await apiFetch(`/chats/${id}`, { method: "DELETE" });
  state.activeChatId = null;
  clearThread();
  ui.threadEmpty.style.display = "grid";
  await loadChats({ keepActive: false });
  setActiveChat(null);
  setStatus("ok", "Чат удалён");
}

function canSend() {
  return !state.sending && !!state.activeChatId && (ui.messageInput.value || "").trim().length > 0;
}

function updateComposer() {
  const len = (ui.messageInput.value || "").length;
  ui.counter.textContent = `${len} / 4000`;
  ui.sendBtn.disabled = !canSend();

  // auto grow textarea
  ui.messageInput.style.height = "auto";
  ui.messageInput.style.height = `${Math.min(ui.messageInput.scrollHeight, 180)}px`;
}

async function sendMessage() {
  if (!canSend()) return;
  const chatId = state.activeChatId;
  const content = (ui.messageInput.value || "").trim();
  if (!content) return;

  state.sending = true;
  updateComposer();
  setStatus("busy", "Думаю…");

  // optimistic add user message
  ui.threadEmpty.style.display = "none";
  addMessage({ role: "user", content, created_at: new Date().toISOString() });
  scrollToBottom();

  ui.messageInput.value = "";
  updateComposer();

  try {
    const result = await apiFetch(`/chats/${chatId}/messages`, { method: "POST", json: { content } });
    addMessage({ role: "assistant", content: result.ai_response, created_at: new Date().toISOString() });
    scrollToBottom();
    setStatus("ok", "Готово");
    await loadChats({ keepActive: true });
    const updated = state.chats.find((c) => c.id === chatId) || null;
    setActiveChat(updated);
    renderChatList();
  } catch (e) {
    console.error(e);
    addMessage({
      role: "system",
      content: `Ошибка: ${e.message || String(e)}`,
      created_at: new Date().toISOString(),
    });
    scrollToBottom();
    setStatus("err", "Ошибка");
  } finally {
    state.sending = false;
    updateComposer();
  }
}

function openSettings() {
  ui.settingsDlg.showModal();
}

ui.newChatBtn.addEventListener("click", async () => {
  try {
    const chat = await createChat();
    setActiveChat(chat);
    renderChatList();
    ui.messageInput.focus();
  } catch (e) {
    setStatus("err", e.message || "Ошибка");
  }
});

ui.refreshBtn.addEventListener("click", async () => {
  try {
    setStatus("busy", "Обновляю…");
    await loadChats({ keepActive: true });
    if (state.activeChatId) await loadMessages(state.activeChatId);
    setStatus(null, "Готов");
  } catch (e) {
    setStatus("err", e.message || "Ошибка");
  }
});

ui.deleteChatBtn.addEventListener("click", () => {
  deleteActiveChat().catch((e) => setStatus("err", e.message || "Ошибка"));
});

ui.chatSearch.addEventListener("input", renderChatList);

ui.messageInput.addEventListener("input", updateComposer);
ui.messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage().catch(console.error);
  }
});

ui.sendBtn.addEventListener("click", () => {
  sendMessage().catch(console.error);
});

ui.settingsBtn.addEventListener("click", openSettings);

ui.logoutBtn.addEventListener("click", () => {
  const ok = confirm("Выйти из аккаунта?");
  if (!ok) return;
  store.del("accessToken");
  ui.settingsDlg.close();
  window.location.href = "/login.html";
});

function toggleSidebar(open) {
  if (open === undefined) {
    open = !ui.side.classList.contains("side--open");
  }
  ui.side.classList.toggle("side--open", open);
  ui.sidebarOverlay.classList.toggle("sidebar-overlay--visible", open);
}

ui.sidebarToggle.addEventListener("click", () => toggleSidebar());
ui.sidebarOverlay.addEventListener("click", () => toggleSidebar(false));

// Initialize the application
updateComposer();
boot().catch((e) => {
  console.error(e);
  setStatus("err", e.message || "Ошибка загрузки");
});
