
from flask import Flask, request, jsonify
from predict import predict_player
import math

app = Flask(__name__)


# =========================================================
# VALIDATE NUMERIC INPUT
# =========================================================

def read_number(data, field, integer=False, allow_none=False):

    value = data.get(field)

    if value is None and allow_none:
        return None

    if value is None:
        raise ValueError(f"{field} cannot be empty")

    number = int(value) if integer else float(value)

    if isinstance(number, float) and not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")

    return number


# =========================================================
# TERMINAL DISPLAY HELPERS
# =========================================================

def format_number(value, decimals=2):

    if value is None:
        return "Not available"

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def print_prediction_report(data, result):

    reaction_time = data.get("reaction_time")

    if reaction_time is not None:
        reaction_display = (
            f"{format_number(reaction_time, 3)} seconds"
        )
    else:
        reaction_display = "Not available"

    print("\n" + "=" * 58)
    print("                  AI GAMING COACH")
    print("                 ML PREDICTION REPORT")
    print("=" * 58)

    print("\nGAMEPLAY INPUT")
    print("-" * 58)

    print(f"{'Score':<25}: {format_number(data.get('score'))}")
    print(f"{'Accuracy':<25}: {format_number(data.get('accuracy'))}%")
    print(f"{'Kills':<25}: {data.get('kills')}")
    print(f"{'Deaths':<25}: {data.get('deaths')}")
    print(f"{'Reaction Time':<25}: {reaction_display}")
    print(
        f"{'Survival Time':<25}: "
        f"{format_number(data.get('survival_time'))} seconds"
    )
    print(
        f"{'Damage Received':<25}: "
        f"{data.get('damage_received', 'Not provided')}"
    )
    print(
        f"{'Played Difficulty':<25}: "
        f"{data.get('difficulty', 'Not provided')}"
    )

    print("\nAI / ML PREDICTION")
    print("-" * 58)

    print(
        f"{'K/D Ratio':<25}: "
        f"{format_number(result.get('kd_ratio'))}"
    )
    print(
        f"{'Performance Score':<25}: "
        f"{format_number(result.get('performance_score') )}"
    )
    print(
        f"{'Predicted Skill Level':<25}: "
        f"{result.get('skill_level', 'Not available')}"
    )
    print(
        f"{'Recommended Difficulty':<25}: "
        f"{result.get('recommended_difficulty', 'Not available')}"
    )

    print("\nAI RECOMMENDATION")
    print("-" * 58)

    recommendation = result.get(
        "recommendation",
        "No recommendation available"
    )

    print(recommendation)

    print("\n" + "=" * 58)
    print("             PREDICTION COMPLETED SUCCESSFULLY")
    print("=" * 58 + "\n")


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "server": "AI Gaming Coach ML",
        "status": "Running",
        "message": "ML server is active",
        "health_endpoint": "/health",
        "prediction_endpoint": "/predict"
    }), 200


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "status": "online",
        "message": "ML server is running and ready"
    }), 200


# =========================================================
# PREDICTION ENDPOINT
# =========================================================

@app.route("/predict", methods=["GET", "POST"])
def predict():

    if request.method == "GET":

        return jsonify({
            "success": True,
            "status": "ML prediction endpoint available",
            "message": "Send gameplay data using POST",
            "required_fields": [
                "score",
                "accuracy",
                "kills",
                "deaths",
                "survival_time"
            ],
            "optional_fields": [
                "reaction_time"
            ]
        }), 200

    try:

        data = request.get_json(silent=True)

        if not isinstance(data, dict):

            return jsonify({
                "success": False,
                "error": "Valid JSON gameplay data is required"
            }), 400

        # -------------------------------------------------
        # READ AND VALIDATE GAMEPLAY STATISTICS
        # -------------------------------------------------

        score = read_number(data, "score")
        accuracy = read_number(data, "accuracy")
        kills = read_number(data, "kills", integer=True)
        deaths = read_number(data, "deaths", integer=True)
        survival_time = read_number(data, "survival_time")

        reaction_time = read_number(
            data,
            "reaction_time",
            allow_none=True
        )

        if score < 0 or kills < 0 or deaths < 0:
            raise ValueError(
                "Score, kills and deaths cannot be negative"
            )

        if not 0 <= accuracy <= 100:
            raise ValueError(
                "Accuracy must be between 0 and 100"
            )

        if survival_time < 0:
            raise ValueError(
                "Survival time cannot be negative"
            )

        if reaction_time is not None and reaction_time <= 0:
            reaction_time = None

        # -------------------------------------------------
        # GENERATE ML PREDICTION
        # -------------------------------------------------

        result = predict_player(
            score=score,
            accuracy=accuracy,
            kills=kills,
            deaths=deaths,
            reaction_time=reaction_time,
            survival_time=survival_time
        )

        # -------------------------------------------------
        # DISPLAY FORMATTED TERMINAL REPORT
        # -------------------------------------------------

        print_prediction_report(data, result)

        # -------------------------------------------------
        # SEND PREDICTION RESPONSE
        # -------------------------------------------------

        return jsonify({
            "success": True,
            "message": "Prediction generated successfully",
            "gameplay_data": data,
            "prediction": result
        }), 200

    except (ValueError, TypeError) as error:

        print("\n" + "=" * 58)
        print("             INVALID GAMEPLAY DATA")
        print("-" * 58)
        print(str(error))
        print("=" * 58 + "\n")

        return jsonify({
            "success": False,
            "error": "Invalid gameplay data: " + str(error)
        }), 400

    except Exception as error:

        print("\n" + "=" * 58)
        print("                ML PREDICTION ERROR")
        print("-" * 58)
        print(str(error))
        print("=" * 58 + "\n")

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("\n" + "=" * 58)
    print("                  AI GAMING COACH ML")
    print("=" * 58)
    print("Home       : http://127.0.0.1:5001/")
    print("Health     : http://127.0.0.1:5001/health")
    print("Prediction : http://127.0.0.1:5001/predict")
    print("=" * 58 + "\n")

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True,
        use_reloader=False
    )
