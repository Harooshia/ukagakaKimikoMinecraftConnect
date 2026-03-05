from collections import deque
import time

from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# STATE MEMORY
# =========================

last_biome = None
last_is_night = False
last_packet_signature = None

recent_events = deque(maxlen=200)
event_counter = 0

# =========================
# HELPER FUNCTIONS
# =========================

def clean_biome(biome):
    if biome is None:
        return "Unknown"
    return biome.replace("minecraft:", "").replace("_", " ").title()


def describe_biome(biome):
    return clean_biome(biome)


def clean_dimension(dim):
    if dim is None:
        return "Unknown"
    return dim.replace("minecraft:", "").title()


def describe_time(tick):

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


def describe_weather(rain, thunder):

    if thunder:
        return "a thunderstorm"

    if rain:
        return "rain"

    return "clear weather"


def detect_night_start(daytime):

    global last_is_night

    now = daytime >= 13000

    if now and not last_is_night:
        last_is_night = True
        return True

    if not now:
        last_is_night = False

    return False


def detect_biome_change(biome):

    global last_biome

    if last_biome is None:
        last_biome = biome
        return False

    if biome != last_biome:
        last_biome = biome
        return True

    return False


def describe_player_state(packet):

    states = []

    if packet.get("elytra_flying"):
        states.append("flying with an elytra")

    if packet.get("underwater"):
        states.append("underwater")

    if packet.get("passenger"):
        states.append("riding an entity")

    if packet.get("on_ground"):
        states.append("standing on the ground")

    if len(states) == 0:
        return ""

    return "The player is currently " + ", ".join(states) + "."


def packet_signature(packet):
    keys = [
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
    ]
    return tuple(packet.get(key) for key in keys)


def add_event(kind, text):
    global event_counter

    event_counter += 1
    recent_events.append(
        {
            "id": event_counter,
            "kind": kind,
            "text": text.strip(),
            "timestamp": time.time(),
        }
    )


def build_event_updates(packet):
    global last_packet_signature

    updates = []

    biome = packet.get("biome")
    daytime = packet.get("daytime", 0)

    if detect_biome_change(biome):
        updates.append(("biome_change", f"You just entered a new biome: {clean_biome(biome)}."))

    if detect_night_start(daytime):
        updates.append(
            (
                "night_start",
                "Night has just begun in Minecraft. Hostile mobs may start spawning, so stay alert.",
            )
        )

    signature = packet_signature(packet)
    if signature != last_packet_signature:
        last_packet_signature = signature
        updates.append(("state_update", build_context(packet)))

    return updates


# =========================
# CONTEXT BUILDER
# =========================

def build_context(packet):

    biome = clean_biome(packet.get("biome"))
    dimension = clean_dimension(packet.get("dimension"))

    daytime = packet.get("daytime", 0)

    weather = describe_weather(
        packet.get("is_raining"),
        packet.get("is_thundering")
    )

    time_desc = describe_time(daytime)

    player_state = describe_player_state(packet)

    context = f"""
Minecraft Environment
Dimension: {dimension}
Biome: {biome}
Time: {time_desc}
Weather: {weather}
Players online: {packet.get("players_online")}
"""

    if player_state:
        context += "\n" + player_state + "\n"

    reason = packet.get("reason")

    # =========================
    # CHAT
    # =========================

    if reason == "chat":

        context += f"""

The player said:
"{packet.get("message")}"

Respond naturally as the AI companion.
"""

    # =========================
    # LOW HEALTH
    # =========================

    elif reason == "low_health":

        context += f"""

The player's health is critically low.

Health: {packet.get("health")}

Offer advice or concern.
"""

    # =========================
    # LOW FOOD
    # =========================

    elif reason == "low_food":

        context += f"""

The player is getting hungry.

Food level: {packet.get("food")}

Suggest eating food.
"""

    return context.strip()


# =========================
# AI CALL (stub)
# =========================

def send_to_ai(prompt):

    print("\n================ AI PROMPT ================\n")
    print(prompt)
    print("\n==========================================\n")

    # Replace this with your KimikoCore call
    # response = kimiko.send(prompt)

    return "..."


# =========================
# MAIN ENDPOINT
# =========================

@app.route("/logs", methods=["POST"])
def logs():
    packet = request.json or {}
    updates = build_event_updates(packet)

    for kind, text in updates:
        add_event(kind, text)
        send_to_ai(text)

    response = updates[-1][1] if updates else "No significant change detected."

    return jsonify({
        "status": "ok",
        "response": response,
        "events": [event for event in list(recent_events)[-len(updates):]],
    })


@app.route("/events/recent", methods=["GET"])
def events_recent():
    after_id = request.args.get("after_id", default=0, type=int)
    events = [event for event in recent_events if int(event.get("id", 0)) > after_id]
    return jsonify({"status": "ok", "events": events})


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    print("Minecraft AI Companion server running...")
    app.run(port=5001)
