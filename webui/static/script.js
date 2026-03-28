const state = {
  settings: null,
  defaultGhosts: [],
  uploadedGhosts: [],
  voices: [],
  page: "hub",
};

const pages = ["hub", "modules", "model", "memory", "data"];

const el = {
  pageTitle: document.getElementById("pageTitle"),
  backBtn: document.getElementById("backBtn"),

  consciousnessInput: document.getElementById("consciousnessInput"),
  contextList: document.getElementById("contextList"),
  addContextBtn: document.getElementById("addContextBtn"),

  speechEnabled: document.getElementById("speechEnabled"),
  voiceSelect: document.getElementById("voiceSelect"),
  testVoiceBtn: document.getElementById("testVoiceBtn"),

  minecraftMode: document.getElementById("minecraftMode"),

  memoryEnabled: document.getElementById("memoryEnabled"),
  memoryInput: document.getElementById("memoryInput"),

  previewHappy: document.getElementById("preview-happy"),
  previewNervous: document.getElementById("preview-nervous"),
  previewWorried: document.getElementById("preview-worried"),

  exportBtn: document.getElementById("exportBtn"),
  importInput: document.getElementById("importInput"),
  deleteBtn: document.getElementById("deleteBtn"),
  resetModulesBtn: document.getElementById("resetModulesBtn"),
  resetBtn: document.getElementById("resetBtn"),

  toast: document.getElementById("toast"),
};

const pageLabels = { hub: "Hub", modules: "Modules", model: "Model", memory: "Memory", data: "Data" };
const toList = (value) => value.split(",").map((x) => x.trim()).filter(Boolean);

function toast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("show");
  setTimeout(() => el.toast.classList.remove("show"), 1500);
}

function ghostPath(file) {
  const folder = state.defaultGhosts.includes(file) ? "ghosts" : "uploads";
  return `/static/${folder}/${encodeURIComponent(file)}`;
}

function switchPage(page) {
  state.page = page;
  pages.forEach((name) => {
    document.getElementById(`page-${name}`).classList.toggle("active", name === page);
  });
  el.pageTitle.textContent = pageLabels[page];
  el.backBtn.hidden = page === "hub";
}

function setToggle(button, on) {
  button.classList.toggle("on", !!on);
  button.setAttribute("aria-pressed", on ? "true" : "false");
}

async function saveSettings(partial) {
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(partial),
  });
  if (!res.ok) throw new Error("save failed");
  const data = await res.json();
  state.settings = data.settings;
  render();
  toast("Saved");
}

function buildContextList() {
  const rc = state.settings.role_contexts || {};
  el.contextList.innerHTML = "";

  Object.entries(rc).forEach(([name, prompt]) => {
    const row = document.createElement("div");
    row.className = "context-item";
    row.innerHTML = `
      <div class="context-head">
        <input class="ctx-name" value="${name}" />
        <button class="context-delete">Delete</button>
      </div>
      <textarea class="ctx-prompt">${prompt || ""}</textarea>
    `;

    const nameInput = row.querySelector(".ctx-name");
    const promptInput = row.querySelector(".ctx-prompt");
    const delBtn = row.querySelector(".context-delete");

    let saveTimer;
    const scheduleSave = () => {
      clearTimeout(saveTimer);
      saveTimer = setTimeout(() => {
        const updated = {};
        el.contextList.querySelectorAll(".context-item").forEach((item) => {
          const n = item.querySelector(".ctx-name").value.trim();
          const p = item.querySelector(".ctx-prompt").value;
          if (n) updated[n] = p;
        });
        saveSettings({ role_contexts: updated });
      }, 200);
    };

    nameInput.addEventListener("input", scheduleSave);
    promptInput.addEventListener("input", scheduleSave);
    delBtn.addEventListener("click", () => {
      row.remove();
      scheduleSave();
    });

    el.contextList.appendChild(row);
  });
}

function renderModelPreviews() {
  const images = state.settings.model.images || {};
  const allImages = [...state.defaultGhosts, ...state.uploadedGhosts];
  const map = {
    happy: { preview: el.previewHappy, current: images.happy || "default.svg" },
    nervous: { preview: el.previewNervous, current: images.nervous || "nervous.svg" },
    worried: { preview: el.previewWorried, current: images.worried || "worried.svg" },
  };

  Object.entries(map).forEach(([expression, cfg]) => {
    cfg.preview.src = ghostPath(cfg.current);
    const select = document.querySelector(`.expr-select[data-expression="${expression}"]`);
    if (!select) return;
    select.innerHTML = allImages.map((name) => `<option value="${name}">${name}</option>`).join("");
    if (allImages.includes(cfg.current)) {
      select.value = cfg.current;
    }
  });
}

function renderVoices() {
  const selected = state.settings.modules.speech.voice;
  el.voiceSelect.innerHTML = "<option value='default'>default</option>";
  state.voices.forEach((voice) => {
    const opt = document.createElement("option");
    opt.value = voice.id;
    opt.textContent = voice.name;
    el.voiceSelect.appendChild(opt);
  });
  el.voiceSelect.value = selected;
}

function render() {
  if (!state.settings) return;
  el.consciousnessInput.value = state.settings.modules.consciousness.join(", ");
  el.memoryInput.value = state.settings.memory.context_modules.join(", ");

  setToggle(el.speechEnabled, !!state.settings.modules.speech.enabled);
  setToggle(el.minecraftMode, !!state.settings.modules.minecraft_mode);
  setToggle(el.memoryEnabled, !!state.settings.memory.enabled);

  renderVoices();
  buildContextList();
  renderModelPreviews();
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();
  state.settings = data.settings;
  state.voices = data.voices || [];
  state.defaultGhosts = data.default_ghosts || [];
  state.uploadedGhosts = data.uploaded_ghosts || [];
  render();
}

function bindEvents() {
  document.querySelectorAll(".nav-card").forEach((card) => {
    card.addEventListener("click", () => switchPage(card.dataset.target));
  });
  el.backBtn.addEventListener("click", () => switchPage("hub"));

  el.consciousnessInput.addEventListener("change", () =>
    saveSettings({ modules: { consciousness: toList(el.consciousnessInput.value) } })
  );

  el.addContextBtn.addEventListener("click", () => {
    const rc = state.settings.role_contexts || {};
    let candidate = "new_context";
    let i = 1;
    while (rc[candidate]) {
      candidate = `new_context_${i++}`;
    }
    rc[candidate] = "";
    saveSettings({ role_contexts: rc });
  });

  el.speechEnabled.addEventListener("click", () =>
    saveSettings({ modules: { speech: { ...state.settings.modules.speech, enabled: !state.settings.modules.speech.enabled } } })
  );

  el.voiceSelect.addEventListener("change", () =>
    saveSettings({ modules: { speech: { ...state.settings.modules.speech, voice: el.voiceSelect.value } } })
  );

  el.testVoiceBtn.addEventListener("click", async () => {
    await fetch("/api/test-voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "Kimiko settings voice test." }),
    });
    toast("Played voice test");
  });

  el.minecraftMode.addEventListener("click", () =>
    saveSettings({ modules: { minecraft_mode: !state.settings.modules.minecraft_mode } })
  );

  el.memoryEnabled.addEventListener("click", () =>
    saveSettings({ memory: { ...state.settings.memory, enabled: !state.settings.memory.enabled } })
  );

  el.memoryInput.addEventListener("change", () =>
    saveSettings({ memory: { ...state.settings.memory, context_modules: toList(el.memoryInput.value) } })
  );

  document.querySelectorAll(".expr-select").forEach((select) => {
    select.addEventListener("change", () => {
      const expression = select.dataset.expression;
      const settings = { ...state.settings };
      settings.model.images[expression] = select.value;
      if (expression === "happy") {
        settings.model.ghost_image = select.value;
      }
      saveSettings({ model: settings.model });
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
      toast(`Updated ${data.expression}`);
    });
  });

  el.exportBtn.addEventListener("click", () => {
    window.location.href = "/api/export";
  });

  el.importInput.addEventListener("change", async () => {
    const file = el.importInput.files[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/import", { method: "POST", body: form });
    if (!res.ok) return toast("Import failed");
    await loadSettings();
    toast("Imported settings");
  });

  el.deleteBtn.addEventListener("click", async () => {
    await fetch("/api/delete-data", { method: "POST" });
    await loadSettings();
    toast("Data deleted");
  });

  el.resetModulesBtn.addEventListener("click", async () => {
    await fetch("/api/reset-modules", { method: "POST" });
    await loadSettings();
    toast("Modules reset");
  });

  el.resetBtn.addEventListener("click", async () => {
    await fetch("/api/reset", { method: "POST" });
    await loadSettings();
    toast("Everything reset");
  });
}

bindEvents();
switchPage("hub");
loadSettings();
