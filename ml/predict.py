
def predict_player(
    score,
    accuracy,
    kills,
    deaths,
    reaction_time,
    survival_time
):

    score = float(score or 0)
    accuracy = float(accuracy or 0)
    kills = int(kills or 0)
    deaths = int(deaths or 0)
    survival_time = float(survival_time or 0)

    # Reaction time is measured in seconds.
    # None means that no valid measurement was recorded.
    if reaction_time is not None:
        reaction_time = float(reaction_time)

        if reaction_time <= 0:
            reaction_time = None

    # Convert fractional accuracy into percentage.
    if 0 <= accuracy <= 1:
        accuracy *= 100

    accuracy = max(0, min(100, accuracy))

    # Calculate K/D ratio.
    kd_ratio = kills / deaths if deaths > 0 else kills

    # Calculate performance score.
    performance = (
        score * 0.30
        + accuracy * 0.25
        + kills * 4
        - deaths * 3
        + survival_time * 0.10
    )

    # Apply reaction-time penalty only when a real
    # reaction-time measurement is available.
    if reaction_time is not None:
        performance -= reaction_time * 10

    # Determine player skill and recommendation.
    if performance >= 250:

        skill_level = "Advanced"
        recommended_difficulty = "Hard"

        recommendation = (
            "Excellent performance! You have strong combat skills. "
            "Continue challenging yourself at Hard difficulty."
        )

    elif performance >= 120:

        skill_level = "Intermediate"
        recommended_difficulty = "Medium"

        recommendation = (
            "Good performance! Improve your accuracy and survival "
            "time to reach the Advanced level."
        )

    else:

        skill_level = "Beginner"
        recommended_difficulty = "Easy"

        recommendation = (
            "Keep practicing! Focus on accuracy, reaction time "
            "and survival skills."
        )

    return {
        "kd_ratio": round(kd_ratio, 2),
        "performance_score": round(performance, 2),
        "skill_level": skill_level,
        "recommended_difficulty": recommended_difficulty,
        "reaction_time": (
            round(reaction_time, 3)
            if reaction_time is not None
            else None
        ),
        "recommendation": recommendation
    }


# =========================================================
# INDEPENDENT TESTING
# =========================================================

if __name__ == "__main__":

    print("\nTEST 1: VALID REACTION TIME")

    result = predict_player(
        score=500,
        accuracy=80,
        kills=5,
        deaths=2,
        reaction_time=0.483,
        survival_time=60
    )

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\nTEST 2: REACTION TIME UNAVAILABLE")

    result = predict_player(
        score=500,
        accuracy=80,
        kills=5,
        deaths=2,
        reaction_time=None,
        survival_time=60
    )

    for key, value in result.items():
        print(f"{key}: {value}")
