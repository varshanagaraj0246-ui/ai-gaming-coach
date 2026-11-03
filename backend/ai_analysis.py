def analyze_player(session):

    # Get player data
    score = session["score"]
    accuracy = session["accuracy"]
    kills = session["kills"]
    deaths = session["deaths"]
    reaction_time = session["reaction_time"]
    survival_time = session["survival_time"]

    # Calculate K/D ratio
    if deaths == 0:
        kd_ratio = kills
    else:
        kd_ratio = kills / deaths

    # Calculate performance score
    performance_score = (
        accuracy * 0.30
        + kd_ratio * 10 * 0.25
        + score / 100 * 0.25
        + survival_time / 10 * 0.20
    )

    # Limit score to 100
    if performance_score > 100:
        performance_score = 100

    # Determine skill level
    if performance_score >= 70:
        skill_level = "Advanced"

    elif performance_score >= 45:
        skill_level = "Intermediate"

    else:
        skill_level = "Beginner"

    # -----------------------------------------
    # PERSONALIZED COACHING
    # -----------------------------------------

    recommendations = []

    if accuracy < 60:

        recommendations.append(
            "Improve aiming accuracy by practicing target shooting."
        )

    elif accuracy >= 80:

        recommendations.append(
            "Excellent accuracy. Continue practicing precision aiming."
        )

    if kd_ratio < 1:

        recommendations.append(
            "Improve positioning and avoid unnecessary fights."
        )

    elif kd_ratio >= 2:

        recommendations.append(
            "Strong K/D ratio. Try taking more challenging engagements."
        )

    if reaction_time > 0.5:

        recommendations.append(
            "Practice reaction-time exercises to respond faster."
        )

    elif reaction_time <= 0.3:

        recommendations.append(
            "Excellent reaction speed. Maintain your current reflex training."
        )

    if survival_time < 180:

        recommendations.append(
            "Focus on defensive gameplay and surviving longer."
        )

    elif survival_time >= 300:

        recommendations.append(
            "Good survival ability. Try increasing your combat intensity."
        )

    # If there are no specific weaknesses
    if len(recommendations) == 0:

        recommendations.append(
            "Excellent overall performance. Continue improving your skills."
        )

    # -----------------------------------------
    # DIFFICULTY RECOMMENDATION
    # -----------------------------------------

    if performance_score >= 75:

        recommended_difficulty = "Hard"

    elif performance_score >= 50:

        recommended_difficulty = "Medium"

    else:

        recommended_difficulty = "Easy"

    # -----------------------------------------
    # RETURN AI ANALYSIS
    # -----------------------------------------

    return {

        "kd_ratio": round(kd_ratio, 2),

        "performance_score": round(
            performance_score, 2
        ),

        "skill_level": skill_level,

        "recommended_difficulty":
            recommended_difficulty,

        "recommendations":
            recommendations
    }