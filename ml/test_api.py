import requests

url = "http://127.0.0.1:5000/predict"

data = {
    "accuracy": 85,
    "reaction_time": 0.7,
    "score": 850,
    "mistakes": 4,
    "games_played": 19
}

response = requests.post(url, json=data)

print(response.json())