from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# STATE MEMORY
# =========================

last_biome = None
last_is_night = False

# =========================
# HELPER FUNCTIONS
# =========================

def clean_biome(biome):
    if biome is None:
        return "Unknown"
    return biome.replace("minecraft:", "").replace("_", " ").title()


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

    packet = request.json

    biome = packet.get("biome")
    daytime = packet.get("daytime", 0)

    # Detect events

    if detect_biome_change(biome):

        prompt = f"""
The player just entered a new biome: {clean_biome(biome)}.
"""
        send_to_ai(prompt)

    if detect_night_start(daytime):

        prompt = """
Night has just begun in Minecraft.
Hostile mobs may start spawning.
"""
        send_to_ai(prompt)

    # Normal packet handling

    prompt = build_context(packet)

    response = send_to_ai(prompt)

    return jsonify({
        "status": "ok",
        "response": response
    })


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    print("Minecraft AI Companion server running...")
    app.run(port=5001)