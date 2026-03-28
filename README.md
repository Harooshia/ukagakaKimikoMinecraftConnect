# ukagakaKimikoMinecraftConnect

## Local Settings Dashboard

Run the local Flask dashboard:

```bash
pip install -r requirements.txt
python -m webui.app
```

Open `http://localhost:5000/settings`.

Pages included:
- Modules
- Model
- Memory
- Data

The dashboard persists to `settings.json` and is read dynamically by `KimikoCore`.
