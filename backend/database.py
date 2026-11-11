
import sqlite3
import os
from datetime import datetime

# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE = os.path.join(DATABASE_DIR, "game.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    os.makedirs(DATABASE_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE TABLES AND MIGRATE EXISTING DATABASE
# =========================================================

def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT UNIQUE NOT NULL,
            player_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            score REAL DEFAULT 0,
            accuracy REAL DEFAULT 0,
            kills INTEGER DEFAULT 0,
            deaths INTEGER DEFAULT 0,
            reaction_time REAL DEFAULT 0,
            average_enemy_speed REAL DEFAULT 0,
            survival_time REAL DEFAULT 0,
            damage_received REAL DEFAULT 0,
            difficulty TEXT DEFAULT 'Medium',
            skill_level TEXT DEFAULT 'Beginner',
            created_at TEXT NOT NULL,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    """)

    # Add missing columns to existing databases.
    # Existing records are preserved.

    cursor.execute("PRAGMA table_info(sessions)")

    existing_columns = {
        row["name"] for row in cursor.fetchall()
    }

    new_columns = {
        "average_enemy_speed": "REAL DEFAULT 0",
        "ai_recommendation": "TEXT DEFAULT ''",
        "recommended_difficulty": "TEXT DEFAULT ''",
        "predicted_skill_level": "TEXT DEFAULT ''",
        "ml_performance_score": "REAL DEFAULT 0",
        "kd_ratio": "REAL DEFAULT 0"
    }

    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:

            cursor.execute(
                f"ALTER TABLE sessions ADD COLUMN "
                f"{column_name} {column_type}"
            )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_player
        ON sessions(player_id)
    """)

    connection.commit()
    connection.close()


# =========================================================
# REGISTER PLAYER
# =========================================================

def register_player(player_name):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT player_id
            FROM players
            ORDER BY id DESC
            LIMIT 1
        """)

        last_player = cursor.fetchone()

        if last_player:

            last_id = last_player["player_id"]

            try:
                number = int(last_id.replace("P", "")) + 1
            except (ValueError, AttributeError):
                number = 1

        else:
            number = 1

        player_id = f"P{number:03d}"

        while True:

            cursor.execute("""
                SELECT player_id
                FROM players
                WHERE player_id = ?
            """, (player_id,))

            if cursor.fetchone() is None:
                break

            number += 1
            player_id = f"P{number:03d}"

        cursor.execute("""
            INSERT INTO players (player_id, player_name)
            VALUES (?, ?)
        """, (player_id, player_name))

        connection.commit()

        return {
            "player_id": player_id,
            "player_name": player_name
        }

    except sqlite3.IntegrityError:

        connection.rollback()
        return None

    finally:
        connection.close()


# =========================================================
# GET ALL PLAYERS
# =========================================================

def get_players():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            p.player_id,
            p.player_name,
            COUNT(s.id) AS total_games,
            COALESCE(MAX(s.score), 0) AS highest_score
        FROM players p
        LEFT JOIN sessions s
            ON p.player_id = s.player_id
        GROUP BY p.player_id, p.player_name
        ORDER BY p.id ASC
    """)

    players = [
        dict(row) for row in cursor.fetchall()
    ]

    connection.close()

    return players


# =========================================================
# GET ONE PLAYER
# =========================================================

def get_player(player_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM players
        WHERE player_id = ?
    """, (player_id,))

    row = cursor.fetchone()

    connection.close()

    return dict(row) if row else None


# =========================================================
# SAVE GAME SESSION
# =========================================================

def save_session(data):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        player_id = data.get("player_id")

        if not player_id:
            raise ValueError("Player ID is missing.")

        cursor.execute("""
            SELECT player_id
            FROM players
            WHERE player_id = ?
        """, (player_id,))

        if cursor.fetchone() is None:

            raise ValueError(
                f"Player {player_id} is not registered."
            )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO sessions (
                player_id,
                score,
                accuracy,
                kills,
                deaths,
                reaction_time,
                average_enemy_speed,
                survival_time,
                damage_received,
                difficulty,
                skill_level,
                created_at,
                ai_recommendation,
                recommended_difficulty,
                predicted_skill_level,
                ml_performance_score,
                kd_ratio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            data.get("score", 0),
            data.get("accuracy", 0),
            data.get("kills", 0),
            data.get("deaths", 0),
            data.get("reaction_time"),
            data.get("average_enemy_speed", 0),
            data.get("survival_time", 0),
            data.get("damage_received", 0),
            data.get("difficulty", "Medium"),
            data.get("skill_level", "Beginner"),
            created_at,
            data.get("ai_recommendation", ""),
            data.get("recommended_difficulty", ""),
            data.get("predicted_skill_level", ""),
            data.get("ml_performance_score", 0),
            data.get("kd_ratio", 0)
        ))

        session_id = cursor.lastrowid

        connection.commit()

        print(
            f"GAME DATA SAVED | Player: {player_id} | "
            f"Session: {session_id} | "
            f"Score: {data.get('score', 0)}"
        )

        return session_id

    except Exception:

        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# GET ALL GAME SESSIONS
# =========================================================

def get_sessions():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM sessions
        ORDER BY id DESC
    """)

    sessions = [
        dict(row) for row in cursor.fetchall()
    ]

    connection.close()

    return sessions


# =========================================================
# GET SESSIONS FOR ONE PLAYER
# =========================================================

def get_player_sessions(player_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM sessions
        WHERE player_id = ?
        ORDER BY id DESC
    """, (player_id,))

    sessions = [
        dict(row) for row in cursor.fetchall()
    ]

    connection.close()

    return sessions
