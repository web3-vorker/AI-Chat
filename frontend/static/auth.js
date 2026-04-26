/* eslint-disable no-console */

const $ = (sel) => document.querySelector(sel);

const ui = {
  loginTab: $("#loginTab"),
  registerTab: $("#registerTab"),
  authForm: $("#authForm"),
  emailInput: $("#emailInput"),
  passwordInput: $("#passwordInput"),
  submitBtn: $("#submitBtn"),
  authError: $("#authError"),
};

let isLoginMode = true;

function apiBase() {
  const saved = (localStorage.getItem("apiBase") || "").trim();
  if (saved) return saved.replace(/\/+$/, "");
  const isLocalhost =
    location.hostname === "127.0.0.1" || location.hostname === "localhost";
  if (isLocalhost) {
    if (location.port === "8000") return "";
    return "http://127.0.0.1:8000";
  }
  if (window.APP_CONFIG && window.APP_CONFIG.BACKEND_URL) {
    return window.APP_CONFIG.BACKEND_URL.replace(/\/+$/, "");
  }
  return "";
}

function apiPrefix() {
  const saved = (localStorage.getItem("apiBase") || "").trim();
  if (saved) return "";
  const isLocalhost =
    location.hostname === "127.0.0.1" || location.hostname === "localhost";
  if (isLocalhost && location.port === "8000") return "/api";
  if (isLocalhost) return "";
  return "/api";
}

function showError(message) {
  ui.authError.textContent = message;
  ui.authError.classList.add("auth-error--visible");
}

function hideError() {
  ui.authError.classList.remove("auth-error--visible");
}

function setLoading(loading) {
  ui.submitBtn.disabled = loading;
  ui.emailInput.disabled = loading;
  ui.passwordInput.disabled = loading;
  ui.submitBtn.querySelector(".btn__text").textContent = loading
    ? "Загрузка..."
    : isLoginMode
    ? "Войти"
    : "Зарегистрироваться";
}

function switchMode(login) {
  isLoginMode = login;
  ui.loginTab.classList.toggle("auth-tab--active", login);
  ui.registerTab.classList.toggle("auth-tab--active", !login);
  ui.submitBtn.querySelector(".btn__text").textContent = login
    ? "Войти"
    : "Зарегистрироваться";
  ui.passwordInput.setAttribute("autocomplete", login ? "current-password" : "new-password");
  hideError();
}

async function handleSubmit(e) {
  e.preventDefault();
  hideError();

  const email = ui.emailInput.value.trim();
  const password = ui.passwordInput.value;

  if (!email || !password) {
    showError("Заполните все поля");
    return;
  }

  if (password.length < 8) {
    showError("Пароль должен быть минимум 8 символов");
    return;
  }

  setLoading(true);

  try {
    const endpoint = isLoginMode ? "/auth/login" : "/auth/register";
    const res = await fetch(`${apiBase()}${apiPrefix()}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      credentials: "include",
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || `${res.status} ${res.statusText}`);
    }

    if (isLoginMode) {
      // Сохраняем токен
      if (data.access_token) {
        localStorage.setItem("accessToken", data.access_token);
      }
      // Перенаправляем на главную
      window.location.href = "/";
    } else {
      // После регистрации переключаемся на логин
      showError("✅ Регистрация успешна! Теперь войдите.");
      switchMode(true);
      ui.passwordInput.value = "";
    }
  } catch (err) {
    console.error(err);
    showError(err.message || "Ошибка соединения");
  } finally {
    setLoading(false);
  }
}

ui.loginTab.addEventListener("click", () => switchMode(true));
ui.registerTab.addEventListener("click", () => switchMode(false));
ui.authForm.addEventListener("submit", handleSubmit);

// Проверяем, авторизован ли уже
const token = localStorage.getItem("accessToken");
if (token) {
  window.location.href = "/";
}
