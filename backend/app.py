
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import requests
import math

from database import (
    create_tables,
    register_player,
    get_players,
    get_player,
    save_session,
    get_sessions,
    get_player_sessions
)

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTEND_FOLDER = os.path.join(BASE_DIR, "frontend")
GAME_BUILD_FOLDER = os.path.join(BASE_DIR, "game", "dist")

ML_SERVER_URL = "http://127.0.0.1:5001/predict"

create_tables()


# =========================================================
# DISABLE GAME CACHE
# =========================================================

@app.after_request
def disable_game_cache(response):
    if request.path.startswith("/game"):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_value(data, keys, default=0):
    for key in keys:
        value = data.get(key)

        if value is not None and value != "":
            return value

    return default


def safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default

        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def normalize_accuracy(value):
    accuracy = safe_number(value, 0)

    if 0 <= accuracy <= 1:
        accuracy *= 100

    return max(0, min(100, accuracy))


def normalize_difficulty(value):

    allowed_difficulties = {
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "expert": "Expert",
        "extreme": "Extreme"
    }

    selected = str(value or "Medium").strip().lower()

    return allowed_difficulties.get(selected, "Medium")


# =========================================================
# REACTION TIME CALCULATION
# =========================================================

def calculate_reaction_time(data):

    samples = data.get("reaction_times")

    if isinstance(samples, list):

        valid_samples = []

        for sample in samples:
            value = safe_number(sample, None)

            if value is not None and value > 0:
                valid_samples.append(value)

        if valid_samples:
            return round(
                sum(valid_samples) / len(valid_samples),
                3
            )

    reaction_value = get_value(
        data,
        [
            "reaction_time",
            "reactionTime",
            "avg_reaction_time",
            "averageReactionTime"
        ],
        None
    )

    if reaction_value is None:
        return None

    reaction_time = safe_number(reaction_value, None)

    if reaction_time is None or reaction_time <= 0:
        return None

    return round(reaction_time, 3)


# =========================================================
# NORMALIZE GAME DATA
# =========================================================

def normalize_game_data(data):

    normalized = {}

    normalized["player_id"] = data.get("player_id")

    normalized["score"] = safe_number(
        get_value(data, ["score", "final_score", "finalScore"])
    )

    normalized["accuracy"] = normalize_accuracy(
        get_value(
            data,
            ["accuracy", "aim_accuracy", "aimAccuracy"]
        )
    )

    normalized["kills"] = int(safe_number(
        get_value(
            data,
            ["kills", "enemiesDefeated", "enemies_defeated"]
        )
    ))

    normalized["deaths"] = int(safe_number(
        get_value(
            data,
            ["deaths", "playerHits", "player_hits"]
        )
    ))

    normalized["reaction_time"] = calculate_reaction_time(data)

    normalized["average_enemy_speed"] = safe_number(
        get_value(
            data,
            [
                "average_enemy_speed",
                "averageEnemySpeed",
                "enemy_speed",
                "enemySpeed"
            ],
            0
        )
    )

    normalized["survival_time"] = safe_number(
        get_value(
            data,
            [
                "survival_time",
                "survivalTime",
                "time_survived",
                "timeSurvived"
            ]
        )
    )

    normalized["damage_received"] = safe_number(
        get_value(
            data,
            ["damage_received", "damageReceived"]
        )
    )

    normalized["difficulty"] = normalize_difficulty(
        data.get("difficulty", "Medium")
    )

    normalized["skill_level"] = str(
        get_value(
            data,
            ["skill_level", "skillLevel"],
            "Beginner"
        )
    )

    # AI PREDICTION FIELDS

    normalized["ai_recommendation"] = ""
    normalized["recommended_difficulty"] = ""
    normalized["predicted_skill_level"] = ""
    normalized["ml_performance_score"] = 0
    normalized["kd_ratio"] = 0

    return normalized


# =========================================================
# TERMINAL SESSION SUMMARY
# =========================================================

def print_session_summary(normalized, player, session_id, ml_status):

    reaction_time = normalized["reaction_time"]

    if reaction_time is not None:
        reaction_display = f"{reaction_time:.3f} seconds"
    else:
        reaction_display = "Not available"

    print("\n" + "=" * 55)
    print("             GAME SESSION SUMMARY")
    print("=" * 55)

    print("\nPLAYER DETAILS")
    print(f"Player Name          : {player['player_name']}")
    print(f"Player ID            : {normalized['player_id']}")
    print(f"Session ID           : {session_id}")

    print("\nGAME PERFORMANCE")
    print(f"Score                : {normalized['score']}")
    print(f"Kills                : {normalized['kills']}")
    print(f"Deaths               : {normalized['deaths']}")
    print(f"Accuracy             : {normalized['accuracy']:.2f}%")
    print(f"Reaction Time        : {reaction_display}")
    print(f"Survival Time        : {normalized['survival_time']} seconds")
    print(f"Damage Received      : {normalized['damage_received']}")

    print("\nDIFFICULTY")
    print(f"Played Difficulty    : {normalized['difficulty']}")

    print("\nAI / ML ANALYSIS")
    print(f"AI Recommendation    : {normalized['ai_recommendation'] or 'Not available'}")
    print(f"Recommended Level    : {normalized['recommended_difficulty'] or 'Not available'}")
    print(f"Predicted Skill      : {normalized['predicted_skill_level'] or 'Not available'}")
    print(f"Performance Score    : {normalized['ml_performance_score']}")
    print(f"K/D Ratio            : {normalized['kd_ratio']}")

    print("\nML SERVER STATUS")
    print(f"Status               : {ml_status}")

    print("\n" + "=" * 55)
    print("          SESSION SAVED SUCCESSFULLY")
    print("=" * 55 + "\n")


# =========================================================
# PLAYER COOKIE
# =========================================================

def set_player_cookie(response, player_id):

    response.set_cookie(
        "player_id",
        str(player_id),
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/"
    )

    return response


# =========================================================
# FRONTEND ROUTES
# =========================================================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/dashboard.html")
def dashboard():
    return send_from_directory(FRONTEND_FOLDER, "dashboard.html")


@app.route("/frontend/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


# =========================================================
# GAME ROUTES
# =========================================================

@app.route("/game")
@app.route("/game/")
def game():
    return send_from_directory(GAME_BUILD_FOLDER, "index.html")


@app.route("/game/<path:filename>")
def game_assets(filename):
    return send_from_directory(GAME_BUILD_FOLDER, filename)


@app.route("/assets/<path:filename>")
def game_root_assets(filename):
    return send_from_directory(
        os.path.join(GAME_BUILD_FOLDER, "assets"),
        filename
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "AI Gaming Coach backend is running."
    })


# =========================================================
# REGISTER PLAYER
# =========================================================

@app.route("/api/register", methods=["POST"])
def api_register():

    try:
        data = request.get_json(silent=True) or {}

        player_name = (
            data.get("player_name")
            or data.get("name")
            or ""
        ).strip()

        if not player_name:
            return jsonify({
                "success": False,
                "message": "Player name is required."
            }), 400

        player = register_player(player_name)

        if not player:
            return jsonify({
                "success": False,
                "message": "Could not register player."
            }), 500

        response = jsonify({
            "success": True,
            "player": player
        })

        set_player_cookie(response, player["player_id"])

        return response, 201

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# CONNECT EXISTING PLAYER
# =========================================================

@app.route("/api/set-player", methods=["POST"])
def api_set_player():

    try:
        data = request.get_json(silent=True) or {}

        player_id = (
            data.get("player_id")
            or data.get("playerId")
        )

        if not player_id:
            return jsonify({
                "success": False,
                "message": "Player ID is required."
            }), 400

        player = get_player(str(player_id))

        if not player:
            return jsonify({
                "success": False,
                "message": "Player is not registered."
            }), 404

        response = jsonify({
            "success": True,
            "message": "Existing player connected successfully.",
            "player": player
        })

        set_player_cookie(response, player["player_id"])

        return response

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# GET ALL PLAYERS
# =========================================================

@app.route("/api/players", methods=["GET"])
def api_players():

    try:
        players = get_players()

        return jsonify({
            "success": True,
            "count": len(players),
            "players": players
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# GET ONE PLAYER
# =========================================================

@app.route("/api/player/<player_id>", methods=["GET"])
def api_player(player_id):

    try:
        player = get_player(player_id)

        if not player:
            return jsonify({
                "success": False,
                "message": "Player not found."
            }), 404

        return jsonify({
            "success": True,
            "player": player
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# GET PLAYER SESSIONS
# =========================================================

@app.route("/api/player/<player_id>/sessions", methods=["GET"])
def api_player_sessions(player_id):

    try:
        player = get_player(player_id)

        if not player:
            return jsonify({
                "success": False,
                "message": "Player not found."
            }), 404

        sessions = get_player_sessions(player_id)

        return jsonify({
            "success": True,
            "player": player,
            "count": len(sessions),
            "sessions": sessions
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# SAVE COMPLETED GAME SESSION
# =========================================================

@app.route("/api/session", methods=["POST"])
def api_save_session():

    data = request.get_json(silent=True) or {}

    try:

        if not data:
            return jsonify({
                "success": False,
                "message": "No gameplay data received."
            }), 400

        normalized = normalize_game_data(data)

        player_id = (
            normalized.get("player_id")
            or request.cookies.get("player_id")
        )

        if not player_id:
            return jsonify({
                "success": False,
                "message": (
                    "Player ID missing from game data "
                    "and browser cookie."
                )
            }), 400

        player = get_player(str(player_id))

        if not player:
            return jsonify({
                "success": False,
                "message": "Player is not registered."
            }), 404

        normalized["player_id"] = str(player_id)

        # -------------------------------------------------
        # REQUEST ML PREDICTION
        # -------------------------------------------------

        ml_status = "Not available"

        try:

            ml_payload = {
                "score": normalized["score"],
                "accuracy": normalized["accuracy"],
                "kills": normalized["kills"],
                "deaths": normalized["deaths"],
                "reaction_time": normalized["reaction_time"],
                "survival_time": normalized["survival_time"],
                "damage_received": normalized["damage_received"],
                "difficulty": normalized["difficulty"]
            }

            ml_response = requests.post(
                ML_SERVER_URL,
                json=ml_payload,
                timeout=5
            )

            if ml_response.ok:

                prediction_data = ml_response.json()

                result = prediction_data.get(
                    "prediction",
                    prediction_data
                )

                # Save the exact ML recommendation.
                normalized["ai_recommendation"] = str(
                    result.get("recommendation") or ""
                )

                # Save AI recommended difficulty separately.
                normalized["recommended_difficulty"] = str(
                    result.get("recommended_difficulty") or ""
                )

                # Save ML predicted skill level separately.
                normalized["predicted_skill_level"] = str(
                    result.get("skill_level") or ""
                )

                normalized["ml_performance_score"] = safe_number(
                    result.get("performance_score"), 0
                )

                normalized["kd_ratio"] = safe_number(
                    result.get("kd_ratio"), 0
                )

                # Use ML skill level as the session's displayed skill.
                if normalized["predicted_skill_level"]:
                    normalized["skill_level"] = (
                        normalized["predicted_skill_level"]
                    )

                ml_status = "Prediction received successfully"

            else:
                ml_status = (
                    f"Server error ({ml_response.status_code})"
                )

        except requests.RequestException:
            ml_status = "ML server is not available"

        except (ValueError, TypeError):
            ml_status = "Invalid ML response"

        # -------------------------------------------------
        # SAVE SESSION
        # -------------------------------------------------

        session_id = save_session(normalized)

        if not session_id:
            return jsonify({
                "success": False,
                "message": "Database did not return a session ID."
            }), 500

        # Display all session details only once.
        print_session_summary(
            normalized,
            player,
            session_id,
            ml_status
        )

        return jsonify({
            "success": True,
            "message": "Gameplay session saved successfully.",
            "session_id": session_id,
            "player_id": player_id,
            "game_data": normalized,
            "ai_analysis": {
                "recommendation": normalized["ai_recommendation"],
                "recommended_difficulty": normalized["recommended_difficulty"],
                "skill_level": normalized["predicted_skill_level"],
                "performance_score": normalized["ml_performance_score"],
                "kd_ratio": normalized["kd_ratio"]
            }
        }), 201

    except Exception as error:

        print(f"\nSESSION SAVE ERROR: {error}\n")

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# GET ALL GAME SESSIONS
# =========================================================

@app.route("/api/sessions", methods=["GET"])
def api_sessions():

    try:
        sessions = get_sessions()

        return jsonify({
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# =========================================================
# ML SERVER STATUS
# =========================================================

@app.route("/api/ml-status", methods=["GET"])
def ml_status():

    try:
        response = requests.get(
            "http://127.0.0.1:5001/",
            timeout=3
        )

        return jsonify({
            "success": response.ok,
            "message": "ML server is reachable."
        })

    except requests.RequestException:
        return jsonify({
            "success": False,
            "message": "ML server is not running."
        })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
