from flask import Flask, request, jsonify
from predict import predict_player

app = Flask(__name__)


# ---------------------------------------
# HOME PAGE
# ---------------------------------------
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


# ---------------------------------------
# HEALTH CHECK
# ---------------------------------------
@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "status": "online",
        "message": "ML server is running and ready"
    }), 200


# ---------------------------------------
# PREDICTION ENDPOINT
# ---------------------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():

    # GET request: endpoint status information
    if request.method == "GET":

        return jsonify({
            "success": True,
            "status": "ML prediction endpoint available",
            "message": "Send gameplay data using POST to generate predictions",
            "required_fields": [
                "score",
                "accuracy",
                "kills",
                "deaths",
                "reaction_time",
                "survival_time"
            ]
        }), 200

    # POST request: actual prediction
    try:

        data = request.get_json(silent=True)

        if not isinstance(data, dict):

            return jsonify({
                "success": False,
                "error": "Valid JSON gameplay data is required"
            }), 400

        required_fields = [
            "score",
            "accuracy",
            "kills",
            "deaths",
            "reaction_time",
            "survival_time"
        ]

        missing_fields = [
            field for field in required_fields
            if field not in data
        ]

        if missing_fields:

            return jsonify({
                "success": False,
                "error": "Missing gameplay fields",
                "missing_fields": missing_fields
            }), 400

        # Read gameplay statistics
        score = float(data["score"])
        accuracy = float(data["accuracy"])
        kills = int(data["kills"])
        deaths = int(data["deaths"])
        reaction_time = float(data["reaction_time"])
        survival_time = float(data["survival_time"])

        # Validate gameplay statistics
        if score < 0 or kills < 0 or deaths < 0:
            return jsonify({
                "success": False,
                "error": "Score, kills and deaths cannot be negative"
            }), 400

        if not 0 <= accuracy <= 100:
            return jsonify({
                "success": False,
                "error": "Accuracy must be between 0 and 100"
            }), 400

        if reaction_time < 0 or survival_time < 0:
            return jsonify({
                "success": False,
                "error": "Time values cannot be negative"
            }), 400

        # Generate ML prediction
        result = predict_player(
            score=score,
            accuracy=accuracy,
            kills=kills,
            deaths=deaths,
            reaction_time=reaction_time,
            survival_time=survival_time
        )

        # Print results in terminal
        print("\n========== GAMEPLAY DATA ==========")
        print(data)

        print("\n========== ML PREDICTION ==========")
        print(result)

        print("===================================\n")

        # Return prediction to backend
        return jsonify({
            "success": True,
            "message": "Prediction generated successfully",
            "gameplay_data": data,
            "prediction": result
        }), 200

    except (ValueError, TypeError) as error:

        return jsonify({
            "success": False,
            "error": "Invalid gameplay data: " + str(error)
        }), 400

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ---------------------------------------
# START SERVER
# ---------------------------------------
if __name__ == "__main__":

    print("\n===================================")
    print("       AI GAMING COACH ML")
    print("===================================")
    print("Home       : http://127.0.0.1:5001/")
    print("Health     : http://127.0.0.1:5001/health")
    print("Prediction : http://127.0.0.1:5001/predict")
    print("===================================\n")

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )