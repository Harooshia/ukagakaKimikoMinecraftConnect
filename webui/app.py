"""Flask web UI for Kimiko runtime settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

try:
    from .settings_manager import (
        DEFAULT_ROLE_CONTEXTS,
        GHOSTS_DIR,
        SETTINGS_FILE,
        UPLOADS_DIR,
        get_settings_manager,
        list_voices,
        speak,
    )
except ImportError:
    try:
        from webui.settings_manager import (
            DEFAULT_ROLE_CONTEXTS,
            GHOSTS_DIR,
            SETTINGS_FILE,
            UPLOADS_DIR,
            get_settings_manager,
            list_voices,
            speak,
        )
    except ImportError:
        from settings_manager import (
            DEFAULT_ROLE_CONTEXTS,
            GHOSTS_DIR,
            SETTINGS_FILE,
            UPLOADS_DIR,
            get_settings_manager,
            list_voices,
            speak,
        )

APP_ROOT = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(APP_ROOT / "static"),
    template_folder=str(APP_ROOT / "templates"),
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

settings_manager = get_settings_manager()


def list_ghost_assets(folder: Path) -> list[str]:
    return sorted(
        [
            p.name
            for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
        ]
    )


@app.get("/settings")
def settings_page() -> str:
    return render_template("settings.html")


@app.get("/api/settings")
def get_settings() -> Any:
    settings = settings_manager.load_settings()
    return jsonify(
        {
            "settings": settings,
            "voices": list_voices(),
            "default_ghosts": list_ghost_assets(GHOSTS_DIR),
            "uploaded_ghosts": sorted([p.name for p in UPLOADS_DIR.glob("*.png")]),
            "default_role_contexts": DEFAULT_ROLE_CONTEXTS,
        }
    )


@app.post("/api/settings")
def update_settings() -> Any:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload."}), 400

    updated = settings_manager.update(payload)
    return jsonify({"ok": True, "settings": updated})


@app.post("/api/upload")
def upload_ghost() -> Any:
    if "file" not in request.files:
        return jsonify({"error": "Missing file."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected."}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".png"):
        return jsonify({"error": "Only .png uploads are supported."}), 400

    expression = str(request.form.get("expression", "happy")).lower().strip()
    if expression not in {"happy", "nervous", "worried"}:
        return jsonify({"error": "Invalid expression."}), 400

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOADS_DIR / filename
    file.save(destination)

    settings = settings_manager.get()
    settings.setdefault("model", {}).setdefault("images", {})[expression] = filename
    if expression == "happy":
        settings["model"]["ghost_image"] = filename

    updated = settings_manager.save_settings(settings)
    return jsonify({"ok": True, "filename": filename, "expression": expression, "settings": updated})


@app.post("/api/reset")
def reset_settings() -> Any:
    settings = settings_manager.reset()
    return jsonify({"ok": True, "settings": settings})


@app.post("/api/reset-modules")
def reset_modules() -> Any:
    settings = settings_manager.get()
    settings["modules"] = {
        "consciousness": [],
        "speech": {"voice": "default", "enabled": True},
        "minecraft_mode": False,
    }
    settings["role_contexts"] = DEFAULT_ROLE_CONTEXTS
    updated = settings_manager.save_settings(settings)
    return jsonify({"ok": True, "settings": updated})


@app.post("/api/delete-data")
def delete_data() -> Any:
    settings = settings_manager.get()
    settings["memory"] = {"enabled": False, "context_modules": []}
    settings["data"] = {"stored": False}
    updated = settings_manager.save_settings(settings)
    return jsonify({"ok": True, "settings": updated})


@app.get("/api/export")
def export_settings() -> Any:
    settings_manager.save_settings(settings_manager.get())
    return send_file(
        SETTINGS_FILE,
        as_attachment=True,
        download_name="settings.json",
        mimetype="application/json",
    )


@app.post("/api/import")
def import_settings() -> Any:
    if "file" not in request.files:
        return jsonify({"error": "Missing file."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected."}), 400

    try:
        payload = json.loads(file.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return jsonify({"error": "Invalid JSON file."}), 400

    if not isinstance(payload, dict):
        return jsonify({"error": "Imported content must be a JSON object."}), 400

    updated = settings_manager.save_settings(payload)
    return jsonify({"ok": True, "settings": updated})


@app.post("/api/test-voice")
def test_voice() -> Any:
    payload = request.get_json(silent=True) or {}
    speak(str(payload.get("text", "Kimiko voice test.")))
    return jsonify({"ok": True})


if __name__ == "__main__":
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
