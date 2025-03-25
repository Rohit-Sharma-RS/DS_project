import os
import sys
import json
import pandas as pd
import joblib
import pytest
from pathlib import Path
import warnings

# Add the project root directory to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, project_root)

from app.app import app  # Import your FastAPI app

def test_data_loading():
    """Test if essential data files are loaded correctly"""
    
    # Check team data
    team_data_path = os.path.join(project_root, 'notebook', 'data', 'processed_player_final.json')
    assert os.path.exists(team_data_path), "Team data file not found"
    
    with open(team_data_path, 'r') as f:
        teams_data = json.load(f)
    
    assert 'teams' in teams_data, "Teams key missing in team data"
    assert len(teams_data['teams']) > 0, "No teams found in data"

def test_model_loading():
    """Test ML model loading and basic predictions"""
    
    # Check model file existence
    model_path = os.path.join(project_root, 'app', 'model.joblib')
    assert os.path.exists(model_path), "Model file not found"
    
    # Load model and scaler
    model = joblib.load(model_path)
    scaler_path = os.path.join(project_root, 'app', 'scaler.joblib')
    scaler = joblib.load(scaler_path)
    
    # Create sample prediction data
    sample_data = {
        'team1_avg_elo': 1500,
        'team2_avg_elo': 1450,
        'team1_avg_form': 0.7,
        'team2_avg_form': 0.6,
        'team1_last_5_wins': 3,
        'team2_last_5_wins': 2,
        'team1_vs_team2_matches': 10,
        'head_to_head_win_rate': 0.6,
        'team1_win_rate': 0.55
    }
    
    df_sample = pd.DataFrame([sample_data])
    
    # Scale and predict
    X_scaled = scaler.transform(df_sample)
    prediction = model.predict(X_scaled)
    
    # Ensure prediction is either 0 or 1
    assert prediction[0] in [0, 1], "Invalid prediction output"

def test_data_dependencies():
    """Check if dependent data files exist"""
    data_files = [
        'head_to_head_dataset.csv',
        'player_analysis.json',
        'team_analysis.json',
        'venue_stats.json'
    ]
    
    for file in data_files:
        file_path = os.path.join(project_root, 'notebook', 'data', file)
        assert os.path.exists(file_path), f"{file} not found"

def test_api_routes():
    """Test basic API routes functionality"""
    
    # This requires the FastAPI TestClient
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test landing page
    response = client.get("/")
    assert response.status_code == 200, "Landing page not accessible"
    
    # Test home page
    response = client.get("/home")
    assert response.status_code == 200, "Home page not accessible"
    
    # Test player analyzer
    response = client.get("/playeranalyzer/")
    assert response.status_code == 200, "Player analyzer page not accessible"
    
    # Test team analyzer
    response = client.get("/teamanalyzer/")
    assert response.status_code == 200, "Team analyzer page not accessible"
    
    # Test venue analyzer
    response = client.get("/venueanalyzer/")
    assert response.status_code == 200, "Venue analyzer page not accessible"

def test_data_analyzers():
    """Test data analyzer functionality"""
    
    # Load player stats
    player_stats_path = os.path.join(project_root, 'notebook', 'data', 'player_analysis.json')
    with open(player_stats_path, 'r') as f:
        player_stats = json.load(f)
    
    # Test player stats
    assert len(player_stats) > 0, "No player stats loaded"
    sample_player = list(player_stats.keys())[0]
    assert 'role' in player_stats[sample_player], "Player role missing"
    
    # Load team stats
    team_stats_path = os.path.join(project_root, 'notebook', 'data', 'team_analysis.json')
    with open(team_stats_path, 'r') as f:
        team_stats = json.load(f)
    
    # Test team stats
    assert len(team_stats) > 0, "No team stats loaded"
    sample_team = list(team_stats.keys())[0]
    assert 'matches_played' in team_stats[sample_team], "Team match stats missing"

def test_predict_failure():
    """Test the /predict endpoint with missing required fields"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Missing 'team1_players'
    payload = {
        "team1": "Mumbai Indians",
        "team2": "Chennai Super Kings",
        "team2_players": ["MS Dhoni", "Ravindra Jadeja"],
        "venue": "M Chinnaswamy Stadium"
    }
    
    response = client.post("/predict", json=payload)
    # Expect a validation error (422 Unprocessable Entity)
    assert response.status_code == 422, "Predict endpoint should return 422 for incomplete data"

def test_nonexistent_endpoint():
    """Test that an unknown endpoint returns 404"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.get("/nonexistent")
    assert response.status_code == 404, "Non-existent endpoint did not return 404"

def test_api_venues():
    """Test that the /api/venues endpoint returns expected JSON data"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.get("/api/venues")
    assert response.status_code == 200, "API venues endpoint not accessible"
    data = response.json()
    assert "venues" in data, "Venues key missing in API response"

def test_get_players():
    """Test the /get_players endpoint for a valid team and non-existent team"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    team_name = "Mumbai Indians"
    response = client.get(f"/get_players/{team_name}")
    assert response.status_code == 200, "Get players endpoint not accessible for existing team"
    data = response.json()
    assert "players" in data, "Players key missing in response"
    
    # For a non-existent team, expecting an empty list or appropriate response
    response = client.get("/get_players/NonExistentTeam")
    assert response.status_code == 200, "Get players endpoint did not handle non-existent team correctly"
    data = response.json()
    assert "players" in data, "Players key missing in response for non-existent team"
    # You can also assert that the list is empty if that’s the expected behavior
    # assert data["players"] == [], "Expected empty players list for non-existent team"

if __name__ == "__main__":
    pytest.main([__file__])
