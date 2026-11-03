import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier


# Load training data
data = pd.read_csv("gameplay_data.csv")

# Input features
X = data[
    [
        "accuracy",
        "reaction_time",
        "score",
        "mistakes",
        "games_played"
    ]
]

# Target
y = data["skill_level"]


# Create Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

# Train model
model.fit(X, y)


# Save trained model
joblib.dump(model, "random_forest_model.pkl")


print("===================================")
print("Random Forest Model Trained")
print("===================================")
print("Training records:", len(data))
print("Features:", X.columns.tolist())
print("Classes:", model.classes_)
print("Model saved as: random_forest_model.pkl")
print("===================================")