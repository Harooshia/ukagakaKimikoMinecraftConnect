"""Flask web UI for Kimiko runtime settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

try:
    from .settings_manager import GHOSTS_DIR, SETTINGS_FILE, UPLOADS_DIR, get_settings_manager, list_voices, speak
except ImportError:
    from webui.settings_manager import GHOSTS_DIR, SETTINGS_FILE, UPLOADS_DIR, get_settings_manager, list_voices, speak

APP_ROOT = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(APP_ROOT / "static"),
    template_folder=str(APP_ROOT / "templates"),
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

settings_manager = get_settings_manager()


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
            "default_ghosts": sorted(
                [
                    p.name
                    for p in GHOSTS_DIR.iterdir()
                    if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
                ]
            ),
            "uploaded_ghosts": sorted([p.name for p in UPLOADS_DIR.glob("*.png")]),
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

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOADS_DIR / filename
    file.save(destination)

    updated = settings_manager.set("model.ghost_image", filename)
    return jsonify({"ok": True, "filename": filename, "settings": updated})


@app.post("/api/reset")
def reset_settings() -> Any:
    settings = settings_manager.reset()
    return jsonify({"ok": True, "settings": settings})


@app.post("/api/delete-data")
def delete_data() -> Any:
    # Reset all memory-related values while preserving non-data settings.
    settings = settings_manager.get()
    settings["memory"] = {"context_modules": []}
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


@app.post("/api/test-voice")
def test_voice() -> Any:
    payload = request.get_json(silent=True) or {}
    speak(str(payload.get("text", "Kimiko voice test.")))
    return jsonify({"ok": True})


if __name__ == "__main__":
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
