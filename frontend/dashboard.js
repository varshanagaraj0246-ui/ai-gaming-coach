// =========================================================
// AI GAMING COACH - DASHBOARD
// Connects Dashboard -> Backend -> Database -> AI Prediction
// =========================================================

const API_URL = "http://127.0.0.1:5000/api/sessions";


// =========================================================
// LOAD DASHBOARD
// =========================================================

document.addEventListener("DOMContentLoaded", () => {

    loadDashboardData();

});


// =========================================================
// GET GAME DATA FROM BACKEND
// =========================================================

async function loadDashboardData() {

    try {

        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Backend connection failed");
        }

        const result = await response.json();

        console.log("Dashboard data received:", result);

        if (!result.success || !result.sessions) {

            console.error("No session data received");

            return;
        }


        const sessions = result.sessions;


        if (sessions.length === 0) {

            console.log("No game sessions available yet");

            return;
        }


        // Update all dashboard sections
        updateStatistics(sessions);
        updateGameplayGraph(sessions);
        updatePerformanceDetection(sessions);
        updateAICoach(sessions);


    } catch (error) {

        console.error("Dashboard error:", error);

        showConnectionError();

    }

}


// =========================================================
// GET LATEST SESSION
// =========================================================

function getLatestSession(sessions) {

    return sessions[sessions.length - 1];

}


// =========================================================
// STATISTICS
// =========================================================

function updateStatistics(sessions) {

    const latest = getLatestSession(sessions);

    if (!latest) return;


    // Find statistic values already present in your HTML
    const values = document.querySelectorAll(".stat-value");


    if (values.length >= 1) {

        values[0].textContent =
            formatNumber(latest.score);

    }


    if (values.length >= 2) {

        values[1].textContent =
            formatNumber(latest.accuracy);

    }


    if (values.length >= 3) {

        values[2].textContent =
            formatNumber(latest.kills);

    }


    if (values.length >= 4) {

        values[3].textContent =
            formatNumber(latest.deaths);

    }


    if (values.length >= 5) {

        const kd =
            latest.deaths > 0
                ? latest.kills / latest.deaths
                : latest.kills;

        values[4].textContent =
            kd.toFixed(2);

    }

}


// =========================================================
// GAMEPLAY GRAPH
// =========================================================

function updateGameplayGraph(sessions) {

    /*
       Your dashboard already contains a custom animated
       gameplay graph.

       We use the actual game scores instead of hardcoded
       values.
    */

    const games =
        document.querySelectorAll(".game");


    if (games.length === 0) {

        console.log("Gameplay graph containers not found");

        return;

    }


    // Show the most recent games
    const recentSessions =
        sessions.slice(-games.length);


    if (recentSessions.length === 0) return;


    // Find maximum score for proper graph scaling
    const maxScore =
        Math.max(
            ...recentSessions.map(
                session => Number(session.score) || 0
            ),
            1
        );


    games.forEach((gameElement, index) => {

        const session =
            recentSessions[index];


        if (!session) {

            gameElement.style.display = "none";

            return;

        }


        gameElement.style.display = "";


        const score =
            Number(session.score) || 0;


        // Find bar
        const bar =
            gameElement.querySelector(".bar");


        if (bar) {

            // Keep bar inside a useful visual range
            const percentage =
                Math.max(
                    8,
                    Math.min(
                        100,
                        (score / maxScore) * 100
                    )
                );


            bar.style.height =
                percentage + "%";

        }


        // Score displayed above bar
        const value =
            gameElement.querySelector(".bar-value");


        if (value) {

            value.textContent =
                formatNumber(score);

        }


        // Game name
        const name =
            gameElement.querySelector(".game-name");


        if (name) {

            name.textContent =
                "Game " +
                (sessions.length -
                recentSessions.length +
                index + 1);

        }


        // Additional information
        const info =
            gameElement.querySelector(".game-info");


        if (info) {

            const kills =
                Number(session.kills) || 0;

            const deaths =
                Number(session.deaths) || 0;

            const accuracy =
                Number(session.accuracy) || 0;


            /*
               Keep the existing HTML structure and only
               update its useful gameplay information.
            */

            const difficulty =
                session.difficulty ||
                "Not detected";


            info.innerHTML =

                "Kills: " +
                kills +

                "<br>" +

                "Accuracy: " +
                accuracy +
                "%";


            const tag =
                gameElement.querySelector(
                    ".difficulty-tag"
                );


            if (tag) {

                tag.textContent =
                    difficulty;

            }

        }

    });

}


// =========================================================
// PERFORMANCE DETECTION
// =========================================================

function updatePerformanceDetection(sessions) {

    const latest =
        getLatestSession(sessions);


    if (!latest) return;


    const score =
        Number(latest.score) || 0;

    const accuracy =
        Number(latest.accuracy) || 0;

    const kills =
        Number(latest.kills) || 0;

    const deaths =
        Number(latest.deaths) || 0;

    const reactionTime =
        Number(latest.reaction_time) || 0;

    const survivalTime =
        Number(latest.survival_time) || 0;


    // Calculate K/D
    const kd =
        deaths > 0
            ? kills / deaths
            : kills;


    /*
       This calculation is only used as a fallback.

       If the backend/ML system already supplied
       skill_level, we use that result.
    */

    let skill =
        latest.skill_level;


    if (!skill) {

        const performanceScore =

            score * 0.30 +

            accuracy * 0.25 +

            kills * 4 -

            deaths * 3 +

            survivalTime * 0.10 -

            reactionTime * 10;


        if (performanceScore >= 250) {

            skill = "Advanced";

        } else if (performanceScore >= 120) {

            skill = "Intermediate";

        } else {

            skill = "Beginner";

        }

    }


    // Score number
    const scoreNumber =
        document.querySelector(
            ".score-number"
        );


    if (scoreNumber) {

        /*
           Display a meaningful performance
           percentage instead of an arbitrary number.
        */

        let performancePercent;


        if (skill === "Advanced") {

            performancePercent = 90;

        } else if (skill === "Intermediate") {

            performancePercent = 70;

        } else {

            performancePercent = 45;

        }


        // Fine-tune percentage using accuracy
        performancePercent =
            Math.round(
                performancePercent * 0.7 +
                Math.min(100, accuracy) * 0.3
            );


        scoreNumber.textContent =
            performancePercent;

    }


    // Skill level
    const skillElement =
        document.querySelector(".skill");


    if (skillElement) {

        skillElement.textContent =
            skill;

    }


    // Skill description
    const description =
        document.querySelector(".skill-desc");


    if (description) {

        let message;


        if (skill === "Advanced") {

            message =
                "Excellent gameplay. Your score, accuracy and combat performance are strong. Try a harder challenge.";

        } else if (skill === "Intermediate") {

            message =
                "Good gameplay. Your fundamentals are developing well. Focus on accuracy, survival and consistent scoring.";

        } else {

            message =
                "Keep practicing. Focus on accuracy, reaction time and surviving longer during gameplay.";

        }


        description.textContent =
            message;

    }


    console.log(
        "Performance detected:",
        skill,
        "K/D:",
        kd.toFixed(2)
    );

}


// =========================================================
// AI COACH
// =========================================================

function updateAICoach(sessions) {

    const latest =
        getLatestSession(sessions);


    if (!latest) return;


    const skill =
        latest.skill_level ||
        "Beginner";


    const difficulty =
        latest.difficulty ||
        "Easy";


    const score =
        Number(latest.score) || 0;

    const accuracy =
        Number(latest.accuracy) || 0;

    const kills =
        Number(latest.kills) || 0;

    const deaths =
        Number(latest.deaths) || 0;

    const reactionTime =
        Number(latest.reaction_time) || 0;

    const survivalTime =
        Number(latest.survival_time) || 0;


    const kd =
        deaths > 0
            ? kills / deaths
            : kills;


    /*
       Try to find existing coach text elements.

       We don't create a new visual design here.
       We update the existing dashboard.
    */

    const coach =
        document.querySelector(".coach");


    if (!coach) {

        console.log("AI Coach section not found");

        return;

    }


    // Look for common text elements
    const coachText =
        coach.querySelector(
            ".coach-text, .coach-message, p"
        );


    let recommendation;


    // Use ML recommendation if available
    if (latest.recommendation) {

        recommendation =
            latest.recommendation;

    } else if (skill === "Advanced") {

        recommendation =
            "Excellent performance! Try a harder challenge.";

    } else if (skill === "Intermediate") {

        recommendation =
            "Good performance! Keep improving your accuracy and survival time.";

    } else {

        recommendation =
            "Keep practicing your accuracy, reaction time and survival skills.";

    }


    if (coachText) {

        coachText.textContent =
            recommendation;

    }


    /*
       Find text inside the coach section that can
       display useful AI insights.
    */

    const coachParagraphs =
        coach.querySelectorAll("p");


    if (coachParagraphs.length > 1) {

        coachParagraphs[1].textContent =

            "Skill: " +
            skill +

            " • Difficulty: " +
            difficulty +

            " • K/D: " +
            kd.toFixed(2);

    }


    /*
       If the existing coach section contains list items,
       turn them into useful ranked coaching points.
    */

    const listItems =
        coach.querySelectorAll("li");


    if (listItems.length > 0) {

        const advice = [];


        if (accuracy < 60) {

            advice.push(
                "Improve accuracy"
            );

        } else {

            advice.push(
                "Strong accuracy"
            );

        }


        if (kd < 1) {

            advice.push(
                "Reduce deaths"
            );

        } else {

            advice.push(
                "Good combat efficiency"
            );

        }


        if (reactionTime > 0.8) {

            advice.push(
                "Improve reaction speed"
            );

        } else {

            advice.push(
                "Fast reactions"
            );

        }


        if (survivalTime < 30) {

            advice.push(
                "Survive longer"
            );

        } else {

            advice.push(
                "Good survival"
            );

        }


        listItems.forEach(
            (item, index) => {

                if (advice[index]) {

                    item.textContent =
                        advice[index];

                }

            }
        );

    }


    console.log(
        "AI Coach:",
        recommendation
    );

}


// =========================================================
// CONNECTION ERROR
// =========================================================

function showConnectionError() {

    console.error(
        "Could not connect to backend."
    );


    /*
       Do not destroy the dashboard.

       If the backend is temporarily unavailable,
       simply log the problem.
    */

}


// =========================================================
// NUMBER FORMATTER
// =========================================================

function formatNumber(value) {

    const number =
        Number(value);


    if (Number.isNaN(number)) {

        return "0";

    }


    return number.toLocaleString(
        undefined,
        {
            maximumFractionDigits: 2
        }
    );

}


// =========================================================
// AUTO REFRESH
// =========================================================

/*
   Refresh dashboard every 5 seconds.

   This means that when another player finishes a game
   and the backend saves it, the dashboard can receive
   the new information automatically.
*/

setInterval(
    loadDashboardData,
    5000
);