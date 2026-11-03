import sqlite3
import os
from datetime import datetime

# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_DIR = os.path.join(BASE_DIR, "database")

DATABASE = os.path.join(
    DATABASE_DIR,
    "game.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    os.makedirs(DATABASE_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE TABLES
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
            survival_time REAL DEFAULT 0,
            damage_received REAL DEFAULT 0,

            difficulty TEXT DEFAULT 'Medium',
            skill_level TEXT DEFAULT 'Beginner',

            created_at TEXT NOT NULL
        )
    """)

    connection.commit()

    connection.close()


# =========================================================
# SAVE GAME SESSION
# =========================================================

def save_session(data):

    connection = get_connection()

    cursor = connection.cursor()

    player_id = data.get("player_id", "Player1")

    score = data.get("score", 0)
    accuracy = data.get("accuracy", 0)
    kills = data.get("kills", 0)
    deaths = data.get("deaths", 0)

    reaction_time = data.get("reaction_time", 0)
    survival_time = data.get("survival_time", 0)
    damage_received = data.get("damage_received", 0)

    difficulty = data.get("difficulty", "Medium")
    skill_level = data.get("skill_level", "Beginner")

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Create player if it doesn't already exist
    cursor.execute("""
        INSERT OR IGNORE INTO players
        (player_id, player_name)
        VALUES (?, ?)
    """, (
        player_id,
        player_id
    ))

    # Save game session
    cursor.execute("""
        INSERT INTO sessions
        (
            player_id,
            score,
            accuracy,
            kills,
            deaths,
            reaction_time,
            survival_time,
            damage_received,
            difficulty,
            skill_level,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        player_id,
        score,
        accuracy,
        kills,
        deaths,
        reaction_time,
        survival_time,
        damage_received,
        difficulty,
        skill_level,
        created_at
    ))

    connection.commit()

    session_id = cursor.lastrowid

    connection.close()

    print(
        f"GAME DATA SAVED | "
        f"Player: {player_id} | "
        f"Score: {score} | "
        f"Kills: {kills} | "
        f"Deaths: {deaths}"
    )

    return session_id


# =========================================================
# GET ALL SESSIONS
# =========================================================

def get_sessions():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM sessions
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    sessions = [dict(row) for row in rows]

    connection.close()

    return sessions