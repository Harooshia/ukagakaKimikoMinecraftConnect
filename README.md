# ukagakaKimikoMinecraftConnect

## Local Settings Dashboard

Kimiko now includes an AIRI-style local settings dashboard.

### Run web UI directly

```bash
pip install -r requirements.txt
python -m webui.app
# or: python webui/app.py
```

Open: `http://localhost:5000/settings`

### Desktop auto-boot

When running `Kimiko/kimiko_desktop.py`, the settings server auto-starts on:
`http://127.0.0.1:5000/settings`

### Dashboard pages

- Settings (hub)
- Modules (Consciousness contexts, Speech, Minecraft)
- Model (Happy/Nervous/Worried image mapping)
- Memory (enable + context modules)
- Data (export/import/delete/reset)

All changes persist to `settings.json` and are consumed by `KimikoCore` at runtime.
