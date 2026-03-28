# ukagakaKimikoMinecraftConnect

## Local Settings Dashboard

A local web settings system is now included.

### Run

```bash
pip install -r requirements.txt
python -m webui.app
# or: python webui/app.py
```

Open: `http://localhost:5000/settings`

### Features

- Module settings (consciousness list, speech on/off + voice, minecraft mode)
- Model ghost selector (text-based default SVG ghosts) + PNG upload
- Memory context modules
- Data actions: export, delete, reset
- Settings are persisted to `settings.json` and used by `KimikoCore` at runtime.

### Runtime integration

`Kimiko/kimiko_core.py` now reads shared settings from `webui/settings_manager.py` on each response.
Minecraft mode, context modules, consciousness modules, and pyttsx3 voice output are applied dynamically.


Desktop app now auto-starts the settings server on http://127.0.0.1:5000/settings when Kimiko launches.
