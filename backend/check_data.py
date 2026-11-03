import sqlite3
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "game.db"
)


print("\n====================================")
print("       AI GAMING COACH DATA")
print("====================================")

print("\nDatabase:")
print(DATABASE)


if not os.path.exists(DATABASE):

    print("\nDatabase does not exist yet.")

    print("Start app.py first.")

    exit()


connection = sqlite3.connect(DATABASE)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()


try:

    cursor.execute(
        "SELECT COUNT(*) AS count FROM sessions"
    )

    count = cursor.fetchone()["count"]


    print("\nTotal games:", count)


    cursor.execute("""
        SELECT *
        FROM sessions
        ORDER BY id DESC
    """)


    rows = cursor.fetchall()


    if len(rows) == 0:

        print("\nNo game data found.")


    else:

        print("\nGame data:")
        print("------------------------------------")


        for row in rows:

            print(
                f"ID: {row['id']} | "
                f"Score: {row['score']} | "
                f"Kills: {row['kills']} | "
                f"Deaths: {row['deaths']} | "
                f"Accuracy: {row['accuracy']} | "
                f"Difficulty: {row['difficulty']} | "
                f"Skill: {row['skill_level']} | "
                f"Time: {row['created_at']}"
            )


except Exception as error:

    print("\nERROR:")
    print(error)


finally:

    connection.close()


print("\n====================================")