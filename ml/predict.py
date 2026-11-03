def predict_player(score, accuracy, kills, deaths, reaction_time, survival_time):

    score = float(score)
    accuracy = float(accuracy)
    kills = int(kills)
    deaths = int(deaths)
    reaction_time = float(reaction_time)
    survival_time = float(survival_time)

    # Convert fractional accuracy into percentage
    if 0 <= accuracy <= 1:
        accuracy = accuracy * 100

    accuracy = max(0, min(100, accuracy))

    # Calculate K/D ratio
    kd_ratio = kills / deaths if deaths > 0 else kills

    # Calculate performance score
    performance = (
        score * 0.30
        + accuracy * 0.25
        + kills * 4
        - deaths * 3
        + survival_time * 0.10
        - reaction_time * 10
    )

    # Determine player skill and recommendation
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
        "recommendation": recommendation
    }


# Independent testing
if __name__ == "__main__":

    result = predict_player(
        score=500,
        accuracy=80,
        kills=5,
        deaths=2,
        reaction_time=0.4,
        survival_time=60
    )

    print("\nAI GAMING COACH PREDICTION")
    print("--------------------------")

    for key, value in result.items():
        print(f"{key}: {value}")