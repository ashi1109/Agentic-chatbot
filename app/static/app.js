const API_BASE = ""; // same origin

let token = localStorage.getItem("token") || null;
let currentUser = null;
let currentProjectId = null;
let projects = [];

// ---------- helpers ----------
function authHeaders() {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    ...options,
    headers: { ...(options.headers || {}), ...authHeaders() },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function show(el) { el.classList.remove("hidden"); }
function hide(el) { el.classList.add("hidden"); }

// ---------- auth screen wiring ----------
const authSection = document.getElementById("auth-section");
const appSection = document.getElementById("app-section");
const authError = document.getElementById("auth-error");

document.getElementById("tab-login").onclick = () => switchTab("login");
document.getElementById("tab-register").onclick = () => switchTab("register");

function switchTab(which) {
  const isLogin = which === "login";
  document.getElementById("tab-login").classList.toggle("active", isLogin);
  document.getElementById("tab-register").classList.toggle("active", !isLogin);
  document.getElementById("login-form").classList.toggle("hidden", !isLogin);
  document.getElementById("register-form").classList.toggle("hidden", isLogin);
  hide(authError);
}

document.getElementById("login-form").onsubmit = async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  try {
    const form = new URLSearchParams();
    form.set("username", email); // OAuth2PasswordRequestForm expects "username"
    form.set("password", password);
    const data = await api("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    token = data.access_token;
    localStorage.setItem("token", token);
    await enterApp();
  } catch (err) {
    authError.textContent = err.message;
    show(authError);
  }
};

document.getElementById("register-form").onsubmit = async (e) => {
  e.preventDefault();
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;
  try {
    await api("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    // auto-login after registering
    document.getElementById("login-email").value = email;
    document.getElementById("login-password").value = password;
    switchTab("login");
    document.getElementById("login-form").requestSubmit();
  } catch (err) {
    authError.textContent = err.message;
    show(authError);
  }
};

document.getElementById("logout-btn").onclick = () => {
  token = null;
  localStorage.removeItem("token");
  location.reload();
};

// ---------- app screen ----------
async function enterApp() {
  currentUser = await api("/auth/me");
  document.getElementById("user-email").textContent = currentUser.email;
  hide(authSection);
  show(appSection);
  await refreshProjects();
}

async function refreshProjects() {
  projects = await api("/projects");
  const list = document.getElementById("project-list");
  list.innerHTML = "";
  projects.forEach((p) => {
    const li = document.createElement("li");
    li.textContent = p.name;
    li.className = p.id === currentProjectId ? "active" : "";
    li.onclick = () => selectProject(p.id);
    list.appendChild(li);
  });
}

document.getElementById("new-project-form").onsubmit = async (e) => {
  e.preventDefault();
  const nameInput = document.getElementById("new-project-name");
  const name = nameInput.value.trim();
  if (!name) return;
  const project = await api("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  nameInput.value = "";
  await refreshProjects();
  selectProject(project.id);
};

async function selectProject(id) {
  currentProjectId = id;
  await refreshProjects();
  const project = projects.find((p) => p.id === id);
  hide(document.getElementById("no-project"));
  show(document.getElementById("project-view"));
  document.getElementById("project-name-input").value = project.name;
  document.getElementById("project-prompt-input").value = project.system_prompt;
  await loadMessages();
}

document.getElementById("save-project-btn").onclick = async () => {
  const name = document.getElementById("project-name-input").value;
  const system_prompt = document.getElementById("project-prompt-input").value;
  await api(`/projects/${currentProjectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, system_prompt }),
  });
  await refreshProjects();
};

document.getElementById("delete-project-btn").onclick = async () => {
  if (!confirm("Delete this project and all its messages?")) return;
  await api(`/projects/${currentProjectId}`, { method: "DELETE" });
  currentProjectId = null;
  hide(document.getElementById("project-view"));
  show(document.getElementById("no-project"));
  await refreshProjects();
};

async function loadMessages() {
  const messages = await api(`/projects/${currentProjectId}/messages`);
  const box = document.getElementById("messages");
  box.innerHTML = "";
  messages.forEach((m) => appendMessage(m.role, m.content));
  box.scrollTop = box.scrollHeight;
}

function appendMessage(role, content, pending = false) {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = `msg ${role}${pending ? " pending" : ""}`;
  div.textContent = content;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

document.getElementById("chat-form").onsubmit = async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text || !currentProjectId) return;
  input.value = "";
  appendMessage("user", text);
  const pendingDiv = appendMessage("assistant", "Thinking...", true);
  try {
    const res = await api(`/projects/${currentProjectId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    pendingDiv.textContent = res.reply;
    pendingDiv.classList.remove("pending");
  } catch (err) {
    pendingDiv.textContent = `Error: ${err.message}`;
  }
};

// ---------- boot ----------
(async function init() {
  if (token) {
    try {
      await enterApp();
      return;
    } catch {
      token = null;
      localStorage.removeItem("token");
    }
  }
  show(authSection);
})();
