from fastapi import FastAPI, Request, Form,APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
import io
from fastapi.staticfiles import StaticFiles
import json
import pandas as pd
import numpy as np
import joblib
from typing import List
import uvicorn

app = FastAPI(title="IPL Match Predictor")

templates = Jinja2Templates(directory=r".\app\templates")

app.mount("/static", StaticFiles(directory=r".\app\static"), name="static")

with open(r"notebook\data\processed_player_final.json", "r") as f:
    teams_data = json.load(f)

head_to_head_df = pd.read_csv(r"notebook\data\head_to_head_dataset.csv")

# Load ML models and scaler
model = joblib.load(r".\app\model.joblib")
scaler = joblib.load(r".\app\scaler.joblib")

# Get all team names for one-hot encoding
all_teams = list(teams_data["teams"].keys())
# Get all venue names for one-hot encoding
venues = [
    "M Chinnaswamy Stadium",
    "Punjab Cricket Association Stadium",
    "Arun Jaitley Stadium",
    "Wankhede Stadium",
    "Saurashtra Cricket Association Stadium",
    "Eden Gardens",
    "Sawai Mansingh Stadium",
    "Rajiv Gandhi International Stadium",
    "MA Chidambaram Stadium",
    "Dr DY Patil Sports Academy",
    "Brabourne Stadium",
    "Narendra Modi Stadium",
    "Barabati Stadium",
    "Vidarbha Cricket Association Stadium",
    "Himachal Pradesh Cricket Association Stadium",
    "Nehru Stadium",
    "Holkar Cricket Stadium",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "Maharashtra Cricket Association Stadium",
    "Shaheed Veer Narayan Singh International Stadium",
    "JSCA International Stadium Complex",
    "Green Park",
    "Ekana Cricket Stadium",
    "Barsapara Cricket Stadium"
]

venue_stats = {}

player_stats = {}
team_stats = {}

def load_player_stats():
    global player_stats
    try:
        with open(r".\notebook\data\player_analysis.json", "r") as f:
            player_stats = json.load(f)
        print("Player stats loaded successfully")
    except Exception as e:
        print(f"Error loading player stats: {e}")

def load_team_stats():
    global team_stats
    try:
        with open(r".\notebook\data\team_analysis.json", "r") as f:
            team_stats = json.load(f)
        print("Team stats loaded successfully")
    except Exception as e:
        print(f"Error loading team stats: {e}")

def load_venue_stats():
    global venue_stats
    try:
        # Load from wherever you have your venue data stored
        # For example, from a JSON file:
        with open(r".\notebook\data\venue_stats.json", "r") as f:
            venue_stats = json.load(f)
        print("Venue stats loaded successfully")
    except Exception as e:
        print(f"Error loading venue stats: {e}")

load_venue_stats()

def align_feature_names(df_encoded):
    """Ensure feature names match exactly what the model was trained on"""
    
    # Map new team names to their older versions if needed
    team_name_mapping = {
        "Punjab Kings": "Kings XI Punjab",
        "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
        # Add any other mappings here
    }
    
    # Replace team names in the dataframe columns
    renamed_columns = {}
    for col in df_encoded.columns:
        new_col = col
        for new_name, old_name in team_name_mapping.items():
            if f"team1_{new_name}" in col:
                new_col = col.replace(f"team1_{new_name}", f"team1_{old_name}")
            elif f"team2_{new_name}" in col:
                new_col = col.replace(f"team2_{new_name}", f"team2_{old_name}")
        
        if col != new_col:
            renamed_columns[col] = new_col
    
    # Rename columns if needed
    if renamed_columns:
        df_encoded = df_encoded.rename(columns=renamed_columns)
    
    # Add missing columns that model expects (with zeros)
    expected_features = model.feature_names_in_ if hasattr(model, 'feature_names_in_') else []
    
    for feature in expected_features:
        if feature not in df_encoded.columns:
            df_encoded[feature] = 0
    
    # Add head_to_head columns if they're missing but expected
    if "head_to_head_wins" in expected_features and "head_to_head_wins" not in df_encoded.columns:
        df_encoded["head_to_head_wins"] = df_encoded["team1_wins"]
    
    if "head_to_head_losses" in expected_features and "head_to_head_losses" not in df_encoded.columns:
        df_encoded["head_to_head_losses"] = df_encoded["team2_wins"]
    
    # Keep only columns that the model expects
    if expected_features:
        df_encoded = df_encoded[expected_features]
    
    return df_encoded

@app.get("/")
async def get_landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def index(request: Request):
    # Get list of team names
    team_names = list(teams_data["teams"].keys())
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "team_names": team_names, "venues": venues}
    )
@app.get("/playeranalyzer/", response_class=HTMLResponse)
async def playeranalyzer(request: Request):
    """
    Render the player analyzer page
    """
    # Load player stats
    load_player_stats()
    
    return templates.TemplateResponse(
        "playeranalyzer.html",
        {"request": request, "players": list(player_stats.keys())}
    )

@app.get("/api/placeholder/{width}/{height}")
async def placeholder_image(width: int, height: int):
    # Create a simple placeholder image with the specified dimensions
    img = Image.new('RGB', (width, height), color=(200, 200, 200))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")

@app.get("/teamanalyzer/", response_class=HTMLResponse)
async def teamanalyzer(request: Request):
    """
    Render the team analyzer page
    """
    # Load team stats
    load_team_stats()
    
    return templates.TemplateResponse(
        "teamanalyzer.html",
        {"request": request, "teams": list(team_stats.keys())}
    )


@app.get("/venueanalyzer/", response_class=HTMLResponse)
async def venueanalyzer(request: Request):
    """
    Render the venue analyzer page
    """
    venues = list(venue_stats.keys())   
    
    return templates.TemplateResponse(
        "venueanalyzer.html",
        {"request": request, "venues": venues}
    )


@app.get("/get_players/{team_name}")
async def get_players(team_name: str):
    """Get players for a specific team"""
    if team_name in teams_data["teams"]:
        # Return only the players that are present
        players = [player for player in teams_data["teams"][team_name] if player["present"]]
        # Extract just the name and role for the response
        players_info = [{"name": player["name"], "role": player["Role"]} for player in players]
        return {"players": players_info}
    return {"players": []}

@app.get("/api/venue-stats/{venue_name}")
async def get_venue_stats(venue_name: str):
    """Get statistics for a specific venue"""
    if venue_name in venue_stats:
        return venue_stats[venue_name]
    else:
        raise HTTPException(status_code=404, detail="Venue not found")
    
@app.get("/api/venues")
async def get_venues():
    """Get list of available venues"""
    return {"venues": list(venue_stats.keys())}

@app.get("/api/player-stats/{player_name}")
async def get_player_stats(player_name: str):
    """Get statistics for a specific player"""
    if player_name in player_stats:
        return player_stats[player_name]
    else:
        raise HTTPException(status_code=404, detail="Player not found")

@app.get("/api/teams-stats/{team_name}")
async def get_team_stats(team_name: str):
    """Get statistics for a specific team"""
    if team_name in team_stats:
        return team_stats[team_name]
    else:
        raise HTTPException(status_code=404, detail="Team not found")
    
@app.get("/get_head_to_head/{team1}/{team2}")
async def get_head_to_head(team1: str, team2: str):
    """Get head-to-head statistics for two teams"""
    # Check for direct match in head_to_head_df
    match1 = head_to_head_df[(head_to_head_df['Team_A'] == team1) & (head_to_head_df['Team_B'] == team2)]
    match2 = head_to_head_df[(head_to_head_df['Team_A'] == team2) & (head_to_head_df['Team_B'] == team1)]
    
    if not match1.empty:
        return {
            "team_a": team1,
            "team_b": team2,
            "team_a_wins": int(match1['Team_A_Wins'].values[0]),
            "team_b_wins": int(match1['Team_B_Wins'].values[0]),
            "total_matches": int(match1['Total_Matches'].values[0])
        }
    elif not match2.empty:
        # Swap the results since teams are in reverse order
        return {
            "team_a": team1,
            "team_b": team2,
            "team_a_wins": int(match2['Team_B_Wins'].values[0]),
            "team_b_wins": int(match2['Team_A_Wins'].values[0]),
            "total_matches": int(match2['Total_Matches'].values[0])
        }
    else:
        # No head-to-head data found
        return {
            "team_a": team1,
            "team_b": team2,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "total_matches": 0
        }

@app.post("/predict")
async def predict_match(
    team1: str = Form(...),
    team2: str = Form(...),
    team1_players: List[str] = Form(...),
    team2_players: List[str] = Form(...),
    venue: str = Form(...)
):
    """Predict match result based on selected teams and players"""
    
    # Calculate team strengths based on player ELOs
    team1_players_data = [player for player in teams_data["teams"][team1] 
                          if player["name"] in team1_players and player["present"]]
    
    team2_players_data = [player for player in teams_data["teams"][team2] 
                          if player["name"] in team2_players and player["present"]]
    
    # Calculate average ELO and form for each team
    team1_avg_elo = sum(player["ELO"] for player in team1_players_data) / len(team1_players_data)
    team2_avg_elo = sum(player["ELO"] for player in team2_players_data) / len(team2_players_data)
    
    team1_avg_form = sum(player["Form"] for player in team1_players_data) / len(team1_players_data)
    team2_avg_form = sum(player["Form"] for player in team2_players_data) / len(team2_players_data)
    
    # Get head-to-head stats
    h2h_stats = await get_head_to_head(team1, team2)
    team1_wins = h2h_stats["team_a_wins"]
    team2_wins = h2h_stats["team_b_wins"]
    total_matches = h2h_stats["total_matches"]
    
    # Set default values for last 5 wins
    team1_last_5_wins = 0
    team2_last_5_wins = 0
    
    # Calculate head-to-head metrics
    team1_vs_team2_matches = total_matches
    head_to_head_win_rate = team1_wins / total_matches if total_matches > 0 else 0.5
    
    # Calculate team1 win rate
    team1_win_rate = team1_wins / total_matches if total_matches > 0 else 0.5
    
    # Create dataframe with ONLY the required features
    data = {
        'team1_avg_elo': team1_avg_elo,
        'team2_avg_elo': team2_avg_elo,
        'team1_avg_form': team1_avg_form,
        'team2_avg_form': team2_avg_form,
        'team1_last_5_wins': team1_last_5_wins,
        'team2_last_5_wins': team2_last_5_wins,
        'team1_vs_team2_matches': team1_vs_team2_matches,
        'head_to_head_win_rate': head_to_head_win_rate,
        'team1_win_rate': team1_win_rate
    }
    
    df_new = pd.DataFrame([data])
    
    try:
        # Scale the features
        X_scaled = scaler.transform(df_new)
        
        # Make prediction
        prediction = model.predict(X_scaled)[0]
        win_probability = model.predict_proba(X_scaled)[0]
        
        # Determine winner
        winner = team1 if prediction == 1 else team2
        prob_team1 = round(win_probability[1] * 100, 2) if len(win_probability) > 1 else 50
        prob_team2 = round(win_probability[0] * 100, 2) if len(win_probability) > 1 else 50
        
        # Create comprehensive result
        result = {
            "team1": team1,
            "team2": team2,
            "team1_players": team1_players,
            "team2_players": team2_players,
            "venue": venue,
            "stats": {
                "team1_avg_elo": round(team1_avg_elo, 2),
                "team2_avg_elo": round(team2_avg_elo, 2),
                "team1_avg_form": round(team1_avg_form, 2),
                "team2_avg_form": round(team2_avg_form, 2),
                "head_to_head": f"{team1_wins}-{team2_wins}",
                "total_matches": total_matches
            },
            "prediction": {
                "winner": winner,
                "team1_probability": prob_team1,
                "team2_probability": prob_team2
            }
        }
        
        return JSONResponse(content=result)
    
    except Exception as e:
        # Return error details for debugging
        error_details = {
            "error": str(e),
            "details": {
                "features_used": list(df_new.columns),
                "data_shape": df_new.shape
            }
        }
        print(f"Error in predict: {error_details}")
        return JSONResponse(status_code=500, content=error_details)
        
if __name__ == "__main__":
    if hasattr(model, 'feature_names_in_'):
        print("Model expects these features:")
        print(sorted(model.feature_names_in_))
        
        # Store expected features for later use
        expected_features = set(model.feature_names_in_)
    else:
        print("Model doesn't have feature_names_in_ attribute")
        expected_features = set()
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)