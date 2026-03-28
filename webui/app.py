"""Flask app for Kimiko settings dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

try:
    from .settings_manager import UPLOADS_DIR, SETTINGS_FILE, get_settings_manager, list_voices, speak, DEFAULT_SETTINGS
except ImportError:
    try:
        from webui.settings_manager import UPLOADS_DIR, SETTINGS_FILE, get_settings_manager, list_voices, speak, DEFAULT_SETTINGS
    except ImportError:
        from settings_manager import UPLOADS_DIR, SETTINGS_FILE, get_settings_manager, list_voices, speak, DEFAULT_SETTINGS

APP_ROOT = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(APP_ROOT / "static"),
    template_folder=str(APP_ROOT / "templates"),
)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

settings_manager = get_settings_manager()
MEMORY_FILES = [APP_ROOT.parent / "connectai_memory.json", APP_ROOT.parent / "memory.json"]


@app.get("/settings")
def settings_hub() -> str:
    return render_template("settings.html", page="settings")


@app.get("/settings/modules")
def settings_modules() -> str:
    return render_template("modules.html", page="modules")


@app.get("/settings/model")
def settings_model() -> str:
    return render_template("model.html", page="model")


@app.get("/settings/memory")
def settings_memory() -> str:
    return render_template("memory.html", page="memory")


@app.get("/settings/data")
def settings_data() -> str:
    return render_template("data.html", page="data")


@app.get("/api/settings")
def api_get_settings() -> Any:
    return jsonify({"settings": settings_manager.load_settings(), "voices": list_voices()})


@app.post("/api/settings")
def api_update_settings() -> Any:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400
    return jsonify({"ok": True, "settings": settings_manager.update(payload)})


@app.post("/api/upload")
def api_upload() -> Any:
    uploaded = request.files.get("file")
    expression = str(request.form.get("expression", "happy")).lower().strip()

    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "No file selected"}), 400
    if not uploaded.filename.lower().endswith(".png"):
        return jsonify({"error": "Only PNG files are supported"}), 400
    if expression not in {"happy", "nervous", "worried"}:
        return jsonify({"error": "Invalid expression"}), 400

    filename = secure_filename(uploaded.filename)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    uploaded.save(UPLOADS_DIR / filename)

    settings = settings_manager.get()
    settings.setdefault("model", {}).setdefault("expressions", {})[expression] = filename
    saved = settings_manager.save_settings(settings)
    return jsonify({"ok": True, "settings": saved, "filename": filename, "expression": expression})


@app.get("/api/export")
def api_export() -> Any:
    settings = settings_manager.get()
    memory_payload: dict[str, Any] = {}
    for mem_file in MEMORY_FILES:
        if mem_file.exists():
            try:
                memory_payload[mem_file.name] = json.loads(mem_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                memory_payload[mem_file.name] = {}

    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    export_path = downloads / "kimiko_data.txt"
    export_path.write_text(
        json.dumps({"settings": settings, "memory": memory_payload}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return send_file(export_path, as_attachment=True, download_name="kimiko_data.txt", mimetype="text/plain")


@app.post("/api/import")
def api_import() -> Any:
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "No file selected"}), 400

    try:
        data = json.loads(uploaded.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return jsonify({"error": "Invalid JSON file"}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "JSON must be an object"}), 400

    return jsonify({"ok": True, "settings": settings_manager.save_settings(data)})


@app.post("/api/reset-modules")
def api_reset_modules() -> Any:
    settings = settings_manager.get()
    settings["modules"] = DEFAULT_SETTINGS["modules"]
    return jsonify({"ok": True, "settings": settings_manager.save_settings(settings)})


@app.post("/api/reset")
def api_reset_all() -> Any:
    return jsonify({"ok": True, "settings": settings_manager.reset()})


@app.post("/api/delete-data")
def api_delete_data() -> Any:
    for mem_file in MEMORY_FILES:
        try:
            mem_file.write_text("{}", encoding="utf-8")
        except OSError:
            continue

    reset = settings_manager.reset()
    return jsonify({"ok": True, "settings": reset})


@app.post("/api/test-voice")
def api_test_voice() -> Any:
    payload = request.get_json(silent=True) or {}
    speak(str(payload.get("text", "Kimiko voice test")))
    return jsonify({"ok": True})


if __name__ == "__main__":
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
