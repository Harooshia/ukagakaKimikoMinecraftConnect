const toastEl = document.getElementById("toast");
let state = { settings: null, voices: [] };

function toast(msg) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 1400);
}

async function fetchSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();
  state = data;
  return data.settings;
}

async function saveSettings(patch) {
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error("Failed to save settings");
  const data = await res.json();
  state.settings = data.settings;
  toast("Saved");
  return data.settings;
}

function setBarToggle(el, enabled) {
  if (!el) return;
  el.classList.toggle("on", !!enabled);
}

function exprPath(name) {
  if (!name) return "";
  if (name.startsWith("http") || name.startsWith("/") || name.startsWith("static/")) {
    return name.startsWith("/") ? name : `/${name.replace(/^\/+/, "")}`;
  }
  return `/static/uploads/${encodeURIComponent(name)}`;
}

async function initModulesPage() {
  const contextsWrap = document.getElementById("contextList");
  if (!contextsWrap) return;

  const settings = await fetchSettings();
  const modules = settings.modules || {};
  const consciousness = modules.consciousness || {};

  const speechToggle = document.getElementById("speechEnabled");
  const minecraftToggle = document.getElementById("minecraftMode");
  const voiceSelect = document.getElementById("voiceSelect");
  const testVoiceBtn = document.getElementById("testVoiceBtn");

  function renderContexts() {
    contextsWrap.innerHTML = "";
    Object.entries(state.settings.modules.consciousness || {}).forEach(([name, prompt]) => {
      const block = document.createElement("div");
      block.className = "context-item";
      block.innerHTML = `
        <div class="context-row">
          <input class="ctx-name" value="${name}">
          <button class="btn ctx-delete">Delete</button>
        </div>
        <textarea class="ctx-prompt">${prompt || ""}</textarea>
      `;

      const commit = () => {
        const next = {};
        contextsWrap.querySelectorAll(".context-item").forEach((item) => {
          const k = item.querySelector(".ctx-name").value.trim();
          const v = item.querySelector(".ctx-prompt").value;
          if (k) next[k] = v;
        });
        saveSettings({ modules: { consciousness: next } }).catch(() => toast("Save failed"));
      };

      block.querySelector(".ctx-name").addEventListener("change", commit);
      block.querySelector(".ctx-prompt").addEventListener("change", commit);
      block.querySelector(".ctx-delete").addEventListener("click", () => {
        block.remove();
        commit();
      });
      contextsWrap.appendChild(block);
    });
  }

  renderContexts();

  const addContextBtn = document.getElementById("addContextBtn");
  addContextBtn?.addEventListener("click", () => {
    const next = { ...(state.settings.modules.consciousness || {}) };
    let name = "new_context";
    let i = 1;
    while (Object.prototype.hasOwnProperty.call(next, name)) name = `new_context_${i++}`;
    next[name] = "";
    saveSettings({ modules: { consciousness: next } }).then(renderContexts);
  });

  setBarToggle(speechToggle, modules.speech?.enabled);
  speechToggle?.addEventListener("click", async () => {
    const next = !state.settings.modules.speech.enabled;
    setBarToggle(speechToggle, next);
    await saveSettings({ modules: { speech: { ...state.settings.modules.speech, enabled: next } } });
  });

  voiceSelect.innerHTML = "<option value='default'>default</option>";
  (state.voices || []).forEach((v) => {
    const o = document.createElement("option");
    o.value = v.id;
    o.textContent = v.name;
    voiceSelect.appendChild(o);
  });
  voiceSelect.value = modules.speech?.voice || "default";
  voiceSelect.addEventListener("change", () =>
    saveSettings({ modules: { speech: { ...state.settings.modules.speech, voice: voiceSelect.value } } })
  );

  testVoiceBtn?.addEventListener("click", () =>
    fetch("/api/test-voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "Kimiko voice test." }),
    })
  );

  setBarToggle(minecraftToggle, modules.minecraft_mode);
  minecraftToggle?.addEventListener("click", async () => {
    const next = !state.settings.modules.minecraft_mode;
    setBarToggle(minecraftToggle, next);
    await saveSettings({ modules: { minecraft_mode: next } });
  });
}

async function initModelPage() {
  const previewHappy = document.getElementById("preview-happy");
  if (!previewHappy) return;

  await fetchSettings();

  const expressionIds = ["happy", "nervous", "worried"];
  function render() {
    expressionIds.forEach((expr) => {
      const pathInput = document.getElementById(`path-${expr}`);
      const value = state.settings.model?.expressions?.[expr] || "";
      if (pathInput) pathInput.value = value;
      const preview = document.getElementById(`preview-${expr}`);
      if (preview) preview.src = exprPath(value);
    });
  }

  render();

  expressionIds.forEach((expr) => {
    const pathInput = document.getElementById(`path-${expr}`);
    pathInput?.addEventListener("change", async () => {
      const next = { ...(state.settings.model?.expressions || {}) };
      next[expr] = pathInput.value.trim();
      await saveSettings({ model: { expressions: next } });
      render();
    });
  });

  document.querySelectorAll(".expr-upload").forEach((input) => {
    input.addEventListener("change", async () => {
      const file = input.files[0];
      if (!file) return;
      const form = new FormData();
      form.append("file", file);
      form.append("expression", input.dataset.expression);
      const res = await fetch("/api/upload", { method: "POST", body: form });
      if (!res.ok) return toast("Upload failed");
      const data = await res.json();
      state.settings = data.settings;
      render();
      toast("Uploaded");
    });
  });
}

async function initMemoryPage() {
  const toggle = document.getElementById("memoryEnabled");
  if (!toggle) return;

  await fetchSettings();
  setBarToggle(toggle, state.settings.memory?.enabled);
  const txt = document.getElementById("memoryContexts");
  if (txt) {
    txt.textContent = Object.keys(state.settings.modules?.consciousness || {}).join("\n") || "No contexts defined.";
  }

  toggle.addEventListener("click", async () => {
    const next = !state.settings.memory.enabled;
    setBarToggle(toggle, next);
    await saveSettings({ memory: { enabled: next } });
  });
}

async function initDataPage() {
  const exportBtn = document.getElementById("exportBtn");
  if (!exportBtn) return;

  await fetchSettings();
  exportBtn.addEventListener("click", () => {
    window.location.href = "/api/export";
  });

  document.getElementById("importInput")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/import", { method: "POST", body: form });
    if (!res.ok) return toast("Import failed");
    await fetchSettings();
    toast("Imported");
  });

  document.getElementById("resetModulesBtn")?.addEventListener("click", async () => {
    await fetch("/api/reset-modules", { method: "POST" });
    toast("Modules reset");
  });

  document.getElementById("deleteBtn")?.addEventListener("click", async () => {
    await fetch("/api/delete-data", { method: "POST" });
    toast("Data deleted");
  });
}

initModulesPage();
initModelPage();
initMemoryPage();
initDataPage();
