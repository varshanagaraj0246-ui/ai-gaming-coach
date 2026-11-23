
from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
    session
)
from flask_cors import CORS
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
import os
import requests
import math
import re

from database import (
    create_tables,
    register_player,
    get_player_by_email,
    get_players,
    get_player,
    save_session as save_game_session,
    get_player_sessions
)

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "ai-gaming-coach-change-this-secret-key"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30
)

CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTEND_FOLDER = os.path.join(BASE_DIR, "frontend")
GAME_BUILD_FOLDER = os.path.join(BASE_DIR, "game", "dist")

ML_SERVER_URL = "http://127.0.0.1:5001/predict"

create_tables()


# =========================================================
# REQUEST TERMINAL LOGGING
# =========================================================

@app.before_request
def log_api_request():

    if request.path.startswith("/api/"):

        print("\n" + "-" * 55)
        print("API REQUEST")
        print(f"Method : {request.method}")
        print(f"Endpoint : {request.path}")

        if session.get("player_id"):
            print(f"Logged-in player : {session.get('player_id')}")
        else:
            print("Logged-in player : None")


@app.after_request
def log_api_response(response):

    if request.path.startswith("/api/"):

        print(f"Response status : {response.status_code}")
        print("-" * 55 + "\n")

    return response


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


def get_logged_in_player():

    player_id = session.get("player_id")

    if not player_id:
        return None

    return get_player(player_id)


def player_response_data(player):

    if not player:
        return None

    return {
        "player_id": player.get("player_id"),
        "player_name": player.get("player_name"),
        "email": player.get("email")
    }


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

    print("\n" + "=" * 60)
    print("                 GAME SESSION SUMMARY")
    print("=" * 60)

    print("\nPLAYER DETAILS")

    print(f"Player Name          : {player['player_name']}")
    print(f"Email                : {player['email']}")
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

    print(
        f"AI Recommendation    : "
        f"{normalized['ai_recommendation'] or 'Not available'}"
    )

    print(
        f"Recommended Level    : "
        f"{normalized['recommended_difficulty'] or 'Not available'}"
    )

    print(
        f"Predicted Skill      : "
        f"{normalized['predicted_skill_level'] or 'Not available'}"
    )

    print(f"Performance Score    : {normalized['ml_performance_score']}")
    print(f"K/D Ratio            : {normalized['kd_ratio']}")

    print("\nML SERVER STATUS")
    print(f"Status               : {ml_status}")

    print("\n" + "=" * 60)
    print("-" * 60)
    print("API SESSIONS")
    print("URL : http://127.0.0.1:5000/api/sessions")
    print("Open this URL in the browser while logged in to view saved sessions.")
    print("-" * 60)
    print("             SESSION SAVED SUCCESSFULLY")
    print("=" * 60 + "\n")


# =========================================================
# FRONTEND ROUTES
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_FOLDER,
        "index.html"
    )


@app.route("/dashboard.html")
def dashboard():

    return send_from_directory(
        FRONTEND_FOLDER,
        "dashboard.html"
    )


@app.route("/frontend/<path:filename>")
def frontend_files(filename):

    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


# =========================================================
# GAME ROUTES
# =========================================================

@app.route("/game")
@app.route("/game/")
def game():

    return send_from_directory(
        GAME_BUILD_FOLDER,
        "index.html"
    )


@app.route("/game/<path:filename>")
def game_assets(filename):

    return send_from_directory(
        GAME_BUILD_FOLDER,
        filename
    )


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

        player_name = str(
            data.get("player_name")
            or data.get("name")
            or ""
        ).strip()

        email = str(data.get("email") or "").strip().lower()
        password = str(data.get("password") or "")

        if not player_name:

            return jsonify({
                "success": False,
                "message": "Player name is required."
            }), 400

        if not email:

            return jsonify({
                "success": False,
                "message": "Email address is required."
            }), 400

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):

            return jsonify({
                "success": False,
                "message": "Enter a valid email address."
            }), 400

        if len(password) < 8:

            return jsonify({
                "success": False,
                "message": "Password must contain at least 8 characters."
            }), 400

        password_hash = generate_password_hash(password)

        player = register_player(
            player_name,
            email,
            password_hash
        )

        if not player:

            return jsonify({
                "success": False,
                "message": (
                    "This email is already registered. "
                    "Please log in instead."
                )
            }), 409

        session.clear()
        session.permanent = True
        session["player_id"] = player["player_id"]

        print("\nREGISTRATION SUCCESSFUL")
        print(f"Player ID : {player['player_id']}")
        print(f"Name      : {player['player_name']}")
        print(f"Email     : {player['email']}")

        return jsonify({
            "success": True,
            "message": "Registration successful.",
            "player": player
        }), 201

    except Exception as error:

        print(f"REGISTRATION ERROR: {error}")

        return jsonify({
            "success": False,
            "message": "Registration failed. Please try again."
        }), 500


# =========================================================
# LOGIN PLAYER - EMAIL AND PASSWORD VERIFICATION
# =========================================================

@app.route("/api/login", methods=["POST"])
def api_login():

    try:

        data = request.get_json(silent=True) or {}

        email = str(data.get("email") or "").strip().lower()
        password = str(data.get("password") or "")

        if not email or not password:

            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        player = get_player_by_email(email)

        if not player:

            print(f"LOGIN FAILED | Unknown email: {email}")

            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        password_hash = player.get("password_hash")

        if not password_hash or not check_password_hash(
            password_hash,
            password
        ):

            print(f"LOGIN FAILED | Incorrect password: {email}")

            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        session.clear()
        session.permanent = True
        session["player_id"] = player["player_id"]

        safe_player = player_response_data(player)

        print("\nLOGIN SUCCESSFUL")
        print(f"Player ID : {player['player_id']}")
        print(f"Name      : {player['player_name']}")
        print(f"Email     : {player['email']}")

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "player": safe_player
        })

    except Exception as error:

        print(f"LOGIN ERROR: {error}")

        return jsonify({
            "success": False,
            "message": "Login failed. Please try again."
        }), 500


# =========================================================
# LOGOUT PLAYER
# =========================================================

@app.route("/api/logout", methods=["POST"])
def api_logout():

    player_id = session.get("player_id")

    session.clear()

    print(f"\nLOGOUT SUCCESSFUL | Player: {player_id or 'Unknown'}")

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# =========================================================
# GET CURRENTLY LOGGED-IN PLAYER
# =========================================================

@app.route("/api/me", methods=["GET"])
def api_me():

    player = get_logged_in_player()

    if not player:

        return jsonify({
            "success": False,
            "authenticated": False,
            "message": "Please log in."
        }), 401

    return jsonify({
        "success": True,
        "authenticated": True,
        "player": player
    })


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

        print(f"GET PLAYERS ERROR: {error}")

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

        logged_in_player = get_logged_in_player()

        if not logged_in_player:

            return jsonify({
                "success": False,
                "message": "Please log in."
            }), 401

        if logged_in_player["player_id"] != player_id:

            return jsonify({
                "success": False,
                "message": "You cannot access another player's account."
            }), 403

        return jsonify({
            "success": True,
            "player": logged_in_player
        })

    except Exception as error:

        print(f"GET PLAYER ERROR: {error}")

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

        player = get_logged_in_player()

        if not player:

            return jsonify({
                "success": False,
                "message": "Please log in."
            }), 401

        if player["player_id"] != player_id:

            return jsonify({
                "success": False,
                "message": "You cannot access another player's sessions."
            }), 403

        sessions = get_player_sessions(player_id)

        print(
            f"\nAPI SESSIONS FETCHED | "
            f"Player: {player_id} | "
            f"Total sessions: {len(sessions)}"
        )

        return jsonify({
            "success": True,
            "player": player,
            "count": len(sessions),
            "sessions": sessions
        })

    except Exception as error:

        print(f"GET PLAYER SESSIONS ERROR: {error}")

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

        # Do not trust player_id sent by the browser.
        # Always use the authenticated Flask session.

        player = get_logged_in_player()

        if not player:

            return jsonify({
                "success": False,
                "message": "Please log in before playing the game."
            }), 401

        normalized = normalize_game_data(data)

        normalized["player_id"] = player["player_id"]

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

                normalized["ai_recommendation"] = str(
                    result.get("recommendation") or ""
                )

                normalized["recommended_difficulty"] = str(
                    result.get("recommended_difficulty") or ""
                )

                normalized["predicted_skill_level"] = str(
                    result.get("skill_level") or ""
                )

                normalized["ml_performance_score"] = safe_number(
                    result.get("performance_score"),
                    0
                )

                normalized["kd_ratio"] = safe_number(
                    result.get("kd_ratio"),
                    0
                )

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
        # SAVE SESSION TO DATABASE
        # -------------------------------------------------

        session_id = save_game_session(normalized)

        if not session_id:

            return jsonify({
                "success": False,
                "message": "Database did not return a session ID."
            }), 500

        # -------------------------------------------------
        # PRINT SESSION DETAILS IN TERMINAL
        # -------------------------------------------------

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
            "player_id": player["player_id"],
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
# GET GAME SESSIONS FOR LOGGED-IN PLAYER
# =========================================================

@app.route("/api/sessions", methods=["GET"])
def api_sessions():

    try:

        player = get_logged_in_player()

        if not player:

            return jsonify({
                "success": False,
                "message": "Please log in to view gameplay sessions."
            }), 401

        sessions = get_player_sessions(player["player_id"])

        # -------------------------------------------------
        # FORMATTED TERMINAL OUTPUT
        # -------------------------------------------------

        print("\n")
        print("=" * 75)
        print("                 AI GAMING COACH")
        print("                 PLAYER SESSION REPORT")
        print("=" * 75)

        print("\nPLAYER INFORMATION")
        print("-" * 75)

        print(f"{'Player Name':<25}: {player['player_name']}")
        print(f"{'Player ID':<25}: {player['player_id']}")
        print(f"{'Email':<25}: {player['email']}")
        print(f"{'Total Game Sessions':<25}: {len(sessions)}")

        print("\nGAMEPLAY SESSION DETAILS")
        print("-" * 75)

        if sessions:

            headers = (
                f"{'ID':<8}"
                f"{'SCORE':<12}"
                f"{'KILLS':<10}"
                f"{'DEATHS':<10}"
                f"{'ACCURACY':<13}"
                f"{'DATE':<22}"
            )

            print(headers)
            print("-" * 75)

            for game_session in sessions:

                print(
                    f"{str(game_session.get('id', 'N/A')):<8}"
                    f"{str(game_session.get('score', 'N/A')):<12}"
                    f"{str(game_session.get('kills', 'N/A')):<10}"
                    f"{str(game_session.get('deaths', 'N/A')):<10}"
                    f"{str(game_session.get('accuracy', 'N/A')) + '%':<13}"
                    f"{str(game_session.get('created_at', 'N/A')):<22}"
                )

        else:

            print("No gameplay sessions found.")

        print("-" * 75)

        print("\nAPI ENDPOINT")
        print("-" * 75)

        print("API Sessions : http://127.0.0.1:5000/api/sessions")
        print("Status       : Successfully retrieved")

        print("=" * 75 + "\n")

        # -------------------------------------------------
        # JSON RESPONSE - UNCHANGED
        # -------------------------------------------------

        return jsonify({
            "success": True,
            "player": player,
            "count": len(sessions),
            "sessions": sessions
        })

    except Exception as error:

        print(f"GET SESSIONS ERROR: {error}")

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

    print("\n" + "=" * 55)
    print("             AI GAMING COACH BACKEND")
    print("=" * 55)

    print("Website     : http://127.0.0.1:5000")
    print("Dashboard   : http://127.0.0.1:5000/dashboard.html")
    print("Game        : http://127.0.0.1:5000/game/")
    print("API Health  : http://127.0.0.1:5000/api/health")
    print("API Sessions: http://127.0.0.1:5000/api/sessions")

    print("=" * 55 + "\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
