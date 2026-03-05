from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import threading
import time
from typing import Any

from flask import Flask, jsonify, request
from werkzeug.serving import make_server


@dataclass
class MinecraftEventService:
    last_biome: str | None = None
    last_is_night: bool = False
    last_packet_signature: tuple[Any, ...] | None = None
    recent_events: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=200))
    event_counter: int = 0

    def reset(self) -> None:
        self.last_biome = None
        self.last_is_night = False
        self.last_packet_signature = None
        self.recent_events.clear()
        self.event_counter = 0

    @staticmethod
    def clean_biome(biome: str | None) -> str:
        if biome is None:
            return "Unknown"
        return biome.replace("minecraft:", "").replace("_", " ").title()

    @staticmethod
    def clean_dimension(dim: str | None) -> str:
        if dim is None:
            return "Unknown"
        return dim.replace("minecraft:", "").title()

    @staticmethod
    def describe_time(tick: int) -> str:
        if tick < 2000:
            return "sunrise"
        if tick < 6000:
            return "morning"
        if tick < 12000:
            return "afternoon"
        if tick < 13000:
            return "sunset"
        if tick < 18000:
            return "night"
        if tick < 22000:
            return "late night"
        return "approaching sunrise"

    @staticmethod
    def describe_weather(rain: bool | None, thunder: bool | None) -> str:
        if thunder:
            return "a thunderstorm"
        if rain:
            return "rain"
        return "clear weather"

    def detect_night_start(self, daytime: int) -> bool:
        now_is_night = daytime >= 13000
        if now_is_night and not self.last_is_night:
            self.last_is_night = True
            return True
        if not now_is_night:
            self.last_is_night = False
        return False

    def detect_biome_change(self, biome: str | None) -> bool:
        if self.last_biome is None:
            self.last_biome = biome
            return False
        if biome != self.last_biome:
            self.last_biome = biome
            return True
        return False

    @staticmethod
    def describe_player_state(packet: dict[str, Any]) -> str:
        states: list[str] = []
        if packet.get("elytra_flying"):
            states.append("flying with an elytra")
        if packet.get("underwater"):
            states.append("underwater")
        if packet.get("passenger"):
            states.append("riding an entity")
        if packet.get("on_ground"):
            states.append("standing on the ground")
        if not states:
            return ""
        return "The player is currently " + ", ".join(states) + "."

    @staticmethod
    def packet_signature(packet: dict[str, Any]) -> tuple[Any, ...]:
        keys = (
            "biome",
            "dimension",
            "daytime",
            "is_raining",
            "is_thundering",
            "elytra_flying",
            "underwater",
            "passenger",
            "on_ground",
            "players_online",
            "health",
            "food",
            "reason",
        )
        return tuple(packet.get(key) for key in keys)

    def add_event(self, kind: str, text: str) -> dict[str, Any]:
        self.event_counter += 1
        event = {
            "id": self.event_counter,
            "kind": kind,
            "text": (text or "").strip(),
            "timestamp": time.time(),
        }
        self.recent_events.append(event)
        return event

    def build_context(self, packet: dict[str, Any]) -> str:
        biome = self.clean_biome(packet.get("biome"))
        dimension = self.clean_dimension(packet.get("dimension"))
        daytime = int(packet.get("daytime", 0) or 0)
        weather = self.describe_weather(packet.get("is_raining"), packet.get("is_thundering"))
        time_desc = self.describe_time(daytime)
        player_state = self.describe_player_state(packet)

        context = (
            "Minecraft Environment\n"
            f"Dimension: {dimension}\n"
            f"Biome: {biome}\n"
            f"Time: {time_desc}\n"
            f"Weather: {weather}\n"
            f"Players online: {packet.get('players_online')}\n"
        )

        if player_state:
            context += f"\n{player_state}\n"

        reason = packet.get("reason")
        if reason == "chat":
            context += (
                f"\nThe player said:\n\"{packet.get('message')}\"\n"
                "Respond naturally as the AI companion.\n"
            )
        elif reason == "low_health":
            context += (
                "\nThe player's health is critically low.\n"
                f"Health: {packet.get('health')}\n"
                "Offer advice or concern.\n"
            )
        elif reason == "low_food":
            context += (
                "\nThe player is getting hungry.\n"
                f"Food level: {packet.get('food')}\n"
                "Suggest eating food.\n"
            )

        return context.strip()

    def build_event_updates(self, packet: dict[str, Any]) -> list[tuple[str, str]]:
        updates: list[tuple[str, str]] = []
        biome = packet.get("biome")
        daytime = int(packet.get("daytime", 0) or 0)

        if self.detect_biome_change(biome):
            updates.append(("biome_change", f"You just entered a new biome: {self.clean_biome(biome)}."))

        if self.detect_night_start(daytime):
            updates.append(
                (
                    "night_start",
                    "Night has just begun in Minecraft. Hostile mobs may start spawning, so stay alert.",
                )
            )

        signature = self.packet_signature(packet)
        if signature != self.last_packet_signature:
            self.last_packet_signature = signature
            updates.append(("state_update", self.build_context(packet)))

        return updates


def create_app(service: MinecraftEventService | None = None) -> Flask:
    service = service or MinecraftEventService()
    app = Flask(__name__)

    @app.route("/logs", methods=["POST"])
    def logs():
        packet = request.json or {}
        updates = service.build_event_updates(packet)
        events = [service.add_event(kind, text) for kind, text in updates]
        response_text = updates[-1][1] if updates else "No significant change detected."
        return jsonify({"status": "ok", "response": response_text, "events": events})

    @app.route("/events/recent", methods=["GET"])
    def events_recent():
        after_id = request.args.get("after_id", default=0, type=int)
        events = [event for event in service.recent_events if int(event.get("id", 0)) > after_id]
        return jsonify({"status": "ok", "events": events})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    return app


class MinecraftEventServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 5001) -> None:
        self.host = host
        self.port = port
        self.service = MinecraftEventService()
        self.app = create_app(self.service)
        self._thread: threading.Thread | None = None
        self._http_server = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            return

        self.service.reset()
        self._http_server = make_server(self.host, self.port, self.app)
        self._thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None

        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None


if __name__ == "__main__":
    server = MinecraftEventServer(host="0.0.0.0", port=5001)
    print("Minecraft AI Companion server running...")
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
