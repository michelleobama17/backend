import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SPORT = "basketball_nba"
REGION = "us"
MARKETS = "h2h,spreads,totals"
API_KEY = "1d98b10a1e991c76952c896152380fcf"
BASE_URL = "https://api.the-odds-api.com/v4/sports/{sport}/odds"

def fetch_odds(sport=SPORT, region=REGION, markets=MARKETS):
    url = BASE_URL.format(sport=sport)
    params = {
        "regions": region,
        "markets": markets,
        "oddsFormat": "decimal",
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch odds: {response.status_code} - {response.text}")
    return response.json()

def calculate_best_bets(odds_data):
    best_bets = []
    for game in odds_data:
        teams = game["teams"]
        bookmakers = game["bookmakers"]
        for book in bookmakers:
            for market in book["markets"]:
                if market["key"] != "h2h":
                    continue
                outcomes = market["outcomes"]
                if len(outcomes) == 2:
                    team1, team2 = outcomes
                    prob1 = 1 / float(team1["price"])
                    prob2 = 1 / float(team2["price"])
                    total_prob = prob1 + prob2
                    edge1 = (prob2 / total_prob) - 0.5
                    edge2 = (prob1 / total_prob) - 0.5
                    best_bets.append({
                        "game": f"{teams[0]} vs {teams[1]}",
                        "bookmaker": book["title"],
                        "bet": team1["name"] if edge1 > edge2 else team2["name"],
                        "odds": team1["price"] if edge1 > edge2 else team2["price"],
                        "edge": round(max(edge1, edge2), 4)
                    })
    return sorted(best_bets, key=lambda x: -x["edge"])

@app.get("/best-bets")
def get_best_bets():
    try:
        odds_data = fetch_odds()
        best_bets = calculate_best_bets(odds_data)
        return {"timestamp": datetime.utcnow().isoformat(), "bets": best_bets[:10]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
