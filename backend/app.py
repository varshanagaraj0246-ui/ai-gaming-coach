from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import requests

from database import create_tables, save_session, get_sessions


# =========================================================
# 1. FLASK APPLICATION
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# 2. PROJECT FOLDER PATHS
# =========================================================

# Project structure:
#
# AI-Gaming-Coach/
# ├── backend/
# │   ├── app.py
# │   └── database.py
# ├── frontend/
# │   ├── index.html
# │   └── dashboard.html
# ├── game/
# │   ├── src/
# │   └── dist/
# │       ├── index.html
# │       └── assets/
# ├── ml/
# └── database/

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FRONTEND_FOLDER = os.path.join(
    BASE_DIR,
    "frontend"
)

GAME_BUILD_FOLDER = os.path.join(
    BASE_DIR,
    "game",
    "dist"
)


# =========================================================
# 3. ML SERVER CONFIGURATION
# =========================================================

ML_SERVER_URL = "http://127.0.0.1:5001/predict"


# =========================================================
# 4. STARTUP INFORMATION
# =========================================================

print("\n==============================================")
print("             AI GAMING COACH")
print("==============================================")

print("Project folder:", BASE_DIR)

print("Frontend folder:", FRONTEND_FOLDER)

print("React build folder:", GAME_BUILD_FOLDER)

print(
    "Home page exists:",
    os.path.isfile(
        os.path.join(FRONTEND_FOLDER, "index.html")
    )
)

print(
    "Dashboard exists:",
    os.path.isfile(
        os.path.join(FRONTEND_FOLDER, "dashboard.html")
    )
)

print(
    "React build exists:",
    os.path.isfile(
        os.path.join(GAME_BUILD_FOLDER, "index.html")
    )
)

print("==============================================\n")


# =========================================================
# 5. MAIN WEBSITE
# =========================================================

@app.route("/")
def home():

    index_file = os.path.join(
        FRONTEND_FOLDER,
        "index.html"
    )

    if not os.path.isfile(index_file):

        return (
            "Home page not found. "
            "Check frontend/index.html.",
            404
        )

    return send_from_directory(
        FRONTEND_FOLDER,
        "index.html"
    )


# =========================================================
# 6. REACT GAME PAGE
# =========================================================

# The actual game is built from:
#
# game/src/app.jsx
# game/src/app.css
#
# Its generated website is:
#
# game/dist/index.html
#
# Open:
# http://127.0.0.1:5000/game/
#
# =========================================================

@app.route("/game")
@app.route("/game/")
def serve_game():

    game_index = os.path.join(
        GAME_BUILD_FOLDER,
        "index.html"
    )

    if not os.path.isfile(game_index):

        return (
            "React game build not found. "
            "Open the game folder in a terminal "
            "and run: npm run build",
            404
        )

    return send_from_directory(
        GAME_BUILD_FOLDER,
        "index.html"
    )


# =========================================================
# 7. REACT GAME ASSETS
# =========================================================

# Serves the built JavaScript, CSS, images and other
# assets required by the React game.
#
# Example:
# /game/assets/index-xxxx.js
# /game/assets/index-xxxx.css
#
# =========================================================

@app.route("/game/<path:filename>")
def serve_game_assets(filename):

    return send_from_directory(
        GAME_BUILD_FOLDER,
        filename
    )


# =========================================================
# 8. DASHBOARD
# =========================================================

@app.route("/dashboard.html")
def dashboard():

    dashboard_file = os.path.join(
        FRONTEND_FOLDER,
        "dashboard.html"
    )

    if not os.path.isfile(dashboard_file):

        return (
            "Dashboard not found. "
            "Check frontend/dashboard.html.",
            404
        )

    return send_from_directory(
        FRONTEND_FOLDER,
        "dashboard.html"
    )


# =========================================================
# 9. FRONTEND STATIC FILES
# =========================================================

# Serves files stored inside frontend/.
#
# Example:
# /frontend/style.css
# /frontend/dashboard.js
#
# =========================================================

@app.route("/frontend/<path:filename>")
def serve_frontend_assets(filename):

    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


# =========================================================
# 10. DATABASE INITIALIZATION
# =========================================================

try:

    create_tables()

    print("Database tables initialized successfully.")

except Exception as error:

    print("Database initialization failed:")
    print(error)

    raise


# =========================================================
# 11. BACKEND HEALTH CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "message": "AI Gaming Coach backend is running"
    })


# =========================================================
# 12. CHECK ML SERVER STATUS
# =========================================================

@app.route("/api/ml-status", methods=["GET"])
def ml_status():

    try:

        # The ML server may not define a root page.
        # Check the prediction endpoint with GET.
        # A 405 response still indicates that a server
        # is responding, but does not prove prediction works.

        response = requests.get(
            ML_SERVER_URL,
            timeout=3
        )

        return jsonify({
            "success": True,
            "ml_server": "reachable",
            "http_status": response.status_code
        })

    except requests.exceptions.RequestException as error:

        return jsonify({
            "success": False,
            "ml_server": "unavailable",
            "message": str(error)
        }), 503


# =========================================================
# 13. RECEIVE GAME SESSION
# =========================================================

@app.route("/api/session", methods=["POST"])
def receive_session():

    try:

        # -----------------------------------------------
        # RECEIVE GAME DATA
        # -----------------------------------------------

        data = request.get_json(silent=True)

        if not isinstance(data, dict) or not data:

            return jsonify({
                "success": False,
                "message": "Valid game-session JSON is required"
            }), 400


        # -----------------------------------------------
        # PLAYER IDENTIFIER
        # -----------------------------------------------

        if not data.get("player_id"):

            data["player_id"] = "Player1"


        # -----------------------------------------------
        # PREPARE FEATURES FOR ML
        # -----------------------------------------------

        ml_data = {
            "score": data.get("score", 0),
            "accuracy": data.get("accuracy", 0),
            "kills": data.get("kills", 0),
            "deaths": data.get("deaths", 0),
            "reaction_time": data.get("reaction_time", 0),
            "survival_time": data.get("survival_time", 0)
        }


        print("\n==============================================")
        print("NEW GAME SESSION RECEIVED")
        print("==============================================")
        print("Game data:", data)
        print("ML input:", ml_data)


        # -----------------------------------------------
        # CALL ML PREDICTION API
        # -----------------------------------------------

        prediction = None
        ml_error = None

        try:

            ml_response = requests.post(
                ML_SERVER_URL,
                json=ml_data,
                timeout=10
            )

            ml_response.raise_for_status()

            prediction = ml_response.json()

            if not isinstance(prediction, dict):

                raise ValueError(
                    "ML API must return a JSON object"
                )

            print("ML prediction:", prediction)


            # -------------------------------------------
            # ATTACH AVAILABLE PREDICTION FIELDS
            # -------------------------------------------

            if prediction.get("difficulty") is not None:

                data["difficulty"] = prediction["difficulty"]

            if prediction.get("skill_level") is not None:

                data["skill_level"] = prediction["skill_level"]


        except (
            requests.exceptions.RequestException,
            ValueError
        ) as error:

            ml_error = str(error)

            print("ML prediction failed:", ml_error)


        # -----------------------------------------------
        # SAVE GAME SESSION
        # -----------------------------------------------
        #
        # The game session is saved even if the ML API
        # is unavailable. This prevents a prediction
        # service failure from automatically discarding
        # the gameplay results.
        #
        # -----------------------------------------------

        session_id = save_session(data)


        # -----------------------------------------------
        # RETURN RESULTS TO FRONTEND
        # -----------------------------------------------

        response_data = {
            "success": True,
            "message": "Game session saved successfully",
            "session_id": session_id,
            "game_data": data,
            "ai_prediction": prediction
        }

        if ml_error:

            response_data["ml_status"] = "unavailable"
            response_data["ml_error"] = ml_error

        else:

            response_data["ml_status"] = "success"


        print("Session saved:", session_id)
        print("==============================================\n")

        return jsonify(response_data), 201


    except Exception as error:

        print("\nERROR PROCESSING GAME SESSION:")
        print(error)

        return jsonify({
            "success": False,
            "message": "Unable to process game session",
            "error": str(error)
        }), 500


# =========================================================
# 14. GET ALL GAME SESSIONS
# =========================================================

@app.route("/api/sessions", methods=["GET"])
def get_all_sessions():

    try:

        sessions = get_sessions()

        return jsonify({
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        })

    except Exception as error:

        print("Unable to retrieve sessions:", error)

        return jsonify({
            "success": False,
            "message": "Unable to retrieve game sessions",
            "error": str(error)
        }), 500


# =========================================================
# 15. MAIN SERVER
# =========================================================

if __name__ == "__main__":

    print("\n==============================================")
    print("          AI GAMING COACH SERVER")
    print("==============================================")

    print("Main website:")
    print("http://127.0.0.1:5000/")

    print("\nReact game:")
    print("http://127.0.0.1:5000/game/")

    print("\nDashboard:")
    print("http://127.0.0.1:5000/dashboard.html")

    print("\nBackend health:")
    print("http://127.0.0.1:5000/api/health")

    print("\nML status:")
    print("http://127.0.0.1:5000/api/ml-status")

    print("\nSaved game sessions:")
    print("http://127.0.0.1:5000/api/sessions")

    print("==============================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )