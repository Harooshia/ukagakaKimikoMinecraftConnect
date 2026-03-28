const state = {
  settings: null,
  defaultGhosts: [],
  uploadedGhosts: [],
  voices: [],
};

const el = {
  consciousnessInput: document.getElementById("consciousnessInput"),
  speechEnabled: document.getElementById("speechEnabled"),
  voiceSelect: document.getElementById("voiceSelect"),
  testVoiceBtn: document.getElementById("testVoiceBtn"),
  minecraftMode: document.getElementById("minecraftMode"),
  memoryInput: document.getElementById("memoryInput"),
  roleWork: document.getElementById("roleWork"),
  roleTherapy: document.getElementById("roleTherapy"),
  roleCompanion: document.getElementById("roleCompanion"),
  roleMinecraft: document.getElementById("roleMinecraft"),
  saveRolesBtn: document.getElementById("saveRolesBtn"),
  ghostPreview: document.getElementById("ghostPreview"),
  ghostGrid: document.getElementById("ghostGrid"),
  ghostUpload: document.getElementById("ghostUpload"),
  exportBtn: document.getElementById("exportBtn"),
  deleteBtn: document.getElementById("deleteBtn"),
  resetBtn: document.getElementById("resetBtn"),
  toast: document.getElementById("toast"),
};

const toList = (value) => value.split(",").map((x) => x.trim()).filter(Boolean);

function toast(message) {
  el.toast.textContent = message;
  el.toast.classList.add("show");
  setTimeout(() => el.toast.classList.remove("show"), 1700);
}

function ghostPath(file) {
  const inDefaults = state.defaultGhosts.includes(file);
  const folder = inDefaults ? "ghosts" : "uploads";
  return `/static/${folder}/${encodeURIComponent(file)}`;
}

function renderGhosts() {
  const all = [...state.defaultGhosts, ...state.uploadedGhosts];
  const selected = state.settings.model.ghost_image;
  el.ghostGrid.innerHTML = "";

  all.forEach((file) => {
    const btn = document.createElement("button");
    btn.className = `ghost-option ${selected === file ? "selected" : ""}`;
    btn.title = file;
    btn.innerHTML = `<img src="${ghostPath(file)}" alt="${file}">`;
    btn.onclick = async () => {
      state.settings.model.ghost_image = file;
      await saveSettings({ model: { ghost_image: file } });
      render();
    };
    el.ghostGrid.appendChild(btn);
  });

  el.ghostPreview.src = ghostPath(selected);
}

function renderVoices() {
  const selected = state.settings.modules.speech.voice;
  el.voiceSelect.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "default";
  defaultOption.textContent = "default";
  el.voiceSelect.appendChild(defaultOption);

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
  el.speechEnabled.checked = !!state.settings.modules.speech.enabled;
  el.minecraftMode.checked = !!state.settings.modules.minecraft_mode;
  el.memoryInput.value = state.settings.memory.context_modules.join(", ");
  const rc = state.settings.role_contexts || {};
  el.roleWork.value = rc.work || "";
  el.roleTherapy.value = rc.therapy || "";
  el.roleCompanion.value = rc.companion || "";
  el.roleMinecraft.value = rc.minecraft || "";
  renderVoices();
  renderGhosts();
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
  toast("Saved");
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();
  state.settings = data.settings;
  state.voices = data.voices;
  state.defaultGhosts = data.default_ghosts;
  state.uploadedGhosts = data.uploaded_ghosts;
  render();
}

function bindEvents() {
  el.consciousnessInput.addEventListener("change", () =>
    saveSettings({ modules: { consciousness: toList(el.consciousnessInput.value) } })
  );
  el.speechEnabled.addEventListener("change", () =>
    saveSettings({ modules: { speech: { ...state.settings.modules.speech, enabled: el.speechEnabled.checked } } })
  );
  el.voiceSelect.addEventListener("change", () =>
    saveSettings({ modules: { speech: { ...state.settings.modules.speech, voice: el.voiceSelect.value } } })
  );
  el.minecraftMode.addEventListener("change", () =>
    saveSettings({ modules: { minecraft_mode: el.minecraftMode.checked } })
  );
  el.memoryInput.addEventListener("change", () =>
    saveSettings({ memory: { context_modules: toList(el.memoryInput.value) } })
  );


  el.saveRolesBtn.addEventListener("click", () =>
    saveSettings({
      role_contexts: {
        work: el.roleWork.value,
        therapy: el.roleTherapy.value,
        companion: el.roleCompanion.value,
        minecraft: el.roleMinecraft.value,
      },
    })
  );

  el.testVoiceBtn.addEventListener("click", async () => {
    await fetch("/api/test-voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "Kimiko settings voice test." }),
    });
    toast("Played voice test");
  });

  el.ghostUpload.addEventListener("change", async () => {
    const file = el.ghostUpload.files[0];
    if (!file) return;

    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: form });
    if (!res.ok) return toast("Upload failed");

    const data = await res.json();
    if (!state.uploadedGhosts.includes(data.filename)) {
      state.uploadedGhosts.push(data.filename);
    }
    state.settings = data.settings;
    render();
    toast("Ghost uploaded");
  });

  el.exportBtn.addEventListener("click", () => {
    window.location.href = "/api/export";
  });

  el.deleteBtn.addEventListener("click", async () => {
    await fetch("/api/delete-data", { method: "POST" });
    await loadSettings();
    toast("Data deleted");
  });

  el.resetBtn.addEventListener("click", async () => {
    await fetch("/api/reset", { method: "POST" });
    await loadSettings();
    toast("Settings reset");
  });
}

bindEvents();
loadSettings();
