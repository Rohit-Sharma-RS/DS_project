from fastapi import FastAPI, Request, Form,APIRouter, HTTPException, Response, WebSocket, WebSocketDisconnect, status, Form, Request, Response, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Dict
from .database import User, ChatMessage, create_tables, get_db
from .auth import authenticate_user, create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from PIL import Image
import io
from fastapi.staticfiles import StaticFiles
import json
import pandas as pd
import joblib
from typing import List
import uvicorn
from pathlib import Path
import os

create_tables()

app = FastAPI(title="IPL Match Predictor")

ROOT_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "app", "templates"))
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_info: Dict[int, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: int, username: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_info[user_id] = {"username": username}
        
        # Send currently active users to the new user
        users_list = [{"id": uid, "username": info["username"]} 
                     for uid, info in self.user_info.items()]
        await websocket.send_json({
            "type": "users_list",
            "users": users_list
        })
        
        # Notify everyone about the new user
        await self.broadcast_user_joined(user_id, username)

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_info:
            username = self.user_info[user_id]["username"]
            del self.user_info[user_id]
            return username
        return None

    async def broadcast_user_joined(self, user_id: int, username: str):
        for connection in self.active_connections.values():
            await connection.send_json({
                "type": "user_joined",
                "user": {"id": user_id, "username": username}
            })

    async def broadcast_user_left(self, user_id: int, username: str):
        for connection in self.active_connections.values():
            await connection.send_json({
                "type": "user_left",
                "user": {"id": user_id, "username": username}
            })

    async def broadcast_message(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json({
                "type": "chat_message", 
                "message": message
            })

manager = ConnectionManager()

# Authentication routes
@router.post("/register")
async def register_user(
    request: Request, 
    username: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Username already exists"}
            )
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Email already exists"}
            )
    
        try:
            user = User.create(username=username, email=email, password=password)
        except AttributeError:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash(password)
            user = User(username=username, email=email, hashed_password=hashed_password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response
    
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Registration failed. Please try again."}
        )
    
@router.post("/token")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Incorrect username or password"}
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set HTTP-only cookie with samesite
    response = RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        samesite="strict",  # this is for better security
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60 
    )
    
    return response

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

# Chat room routes
from datetime import datetime, timezone
import pytz

@router.get("/chat")
async def get_chat_page(request: Request, current_user: User = Depends(get_current_active_user)):
    db = next(get_db())
    messages = db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(50).all()
    
    ist_timezone = pytz.timezone('Asia/Kolkata')
    
    messages = reversed([{
        "id": msg.id,
        "content": msg.content,
        "created_at": msg.created_at.astimezone(ist_timezone).strftime("%Y-%m-%d %H:%M:%S IST"),
        "username": db.query(User).filter(User.id == msg.user_id).first().username,
        "user_id": msg.user_id
    } for msg in messages])
    
    return templates.TemplateResponse(
        "chat.html", 
        {
            "request": request, 
            "username": current_user.username,
            "user_id": current_user.id,
            "chat_history": list(messages)
        }
    )
            
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, user_id, user.username)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            content = message_data.get("content", "").strip()
            
            if content:
                # Save message to database
                chat_message = ChatMessage(content=content, user_id=user_id)
                db.add(chat_message)
                db.commit()
                db.refresh(chat_message)
                
                await manager.broadcast_message({
                    "id": chat_message.id,
                    "content": content,
                    "user_id": user_id,
                    "username": user.username,
                    "created_at": chat_message.created_at.astimezone(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S IST")
                })
    except WebSocketDisconnect:
        username = manager.disconnect(user_id)
        if username:
            await manager.broadcast_user_left(user_id, username)
    except Exception as e:
        print(f"WebSocket error: {e}")
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "app", "static")), name="static")

with open(os.path.join(ROOT_DIR, "notebook", "data", "processed_player_final.json"),  "r") as f:
    teams_data = json.load(f)

head_to_head_df = pd.read_csv(os.path.join(ROOT_DIR, "notebook", "data", "head_to_head_dataset.csv"))

model = joblib.load(os.path.join(ROOT_DIR, "app", "model.joblib"))
scaler = joblib.load(os.path.join(ROOT_DIR, "app", "scaler.joblib"))

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
        with open(os.path.join(ROOT_DIR, "notebook","data", "player_analysis.json"), "r") as f:
            player_stats = json.load(f)
        print("Player stats loaded successfully")
    except Exception as e:
        print(f"Error loading player stats: {e}")

def load_team_stats():
    global team_stats
    try:
        with open(os.path.join(ROOT_DIR, "notebook","data", "team_analysis.json"), "r") as f:
            team_stats = json.load(f)
        print("Team stats loaded successfully")
    except Exception as e:
        print(f"Error loading team stats: {e}")

def load_venue_stats():
    global venue_stats
    try:

        with open(os.path.join(ROOT_DIR, "notebook","data", "venue_stats.json"), "r") as f:
            venue_stats = json.load(f)
        print("Venue stats loaded successfully")
    except Exception as e:
        print(f"Error loading venue stats: {e}")

load_venue_stats()

def align_feature_names(df_encoded):
    """Ensure feature names match exactly what the model was trained on"""
    
    team_name_mapping = {
        "Punjab Kings": "Kings XI Punjab",
        "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
    }
    
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
    return templates.TemplateResponse(request, "landing.html")

@app.get("/home", response_class=HTMLResponse)
async def index(request: Request):
    # grab all the teams for the dropdown
    team_names = list(teams_data["teams"].keys())
    
    # check if user is logged in from cookie
    current_user = None
    try:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            db = next(get_db())
            current_user = get_current_active_user(token=token, db=db)
    except Exception:
        pass
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "team_names": team_names, 
            "venues": venues, 
            "user": current_user
        }
        
    )

@app.get("/playeranalyzer/", response_class=HTMLResponse)
async def playeranalyzer(request: Request):
    # need to load this every time cuz it might change
    load_player_stats()
    
    return templates.TemplateResponse(
        request,
        "playeranalyzer.html",
        {"players": list(player_stats.keys())}
    )

@app.get("/api/placeholder/{width}/{height}")
async def placeholder_image(width: int, height: int):
    # just a gray box for when images aren't ready yet
    img = Image.new('RGB', (width, height), color=(200, 200, 200))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")

@app.get("/teamanalyzer/", response_class=HTMLResponse)
async def teamanalyzer(request: Request):
    # gotta refresh this each time
    load_team_stats()
    
    return templates.TemplateResponse(
        request,
        "teamanalyzer.html",
        {"teams": list(team_stats.keys())}
    )

@app.get("/venueanalyzer/", response_class=HTMLResponse)
async def venueanalyzer(request: Request):
    # all the stadiums and stuff
    venues = list(venue_stats.keys())   
    
    return templates.TemplateResponse(
        request,
        "venueanalyzer.html",
        {"venues": venues}
    )


@app.get("/get_players/{team_name}")
async def get_players(team_name: str):
    if team_name in teams_data["teams"]:
        # only want active players not benched ones
        players = [player for player in teams_data["teams"][team_name] if player["present"]]
        players_info = [{"name": player["name"], "role": player["Role"]} for player in players]
        return {"players": players_info}
    return {"players": []}

@app.get("/api/venue-stats/{venue_name}")
async def get_venue_stats(venue_name: str):
    if venue_name in venue_stats:
        return venue_stats[venue_name]
    else:
        raise HTTPException(status_code=404, detail="Venue not found")
    
@app.get("/api/venues")
async def get_venues():
    return {"venues": list(venue_stats.keys())}

@app.get("/api/player-stats/{player_name}")
async def get_player_stats(player_name: str):
    if player_name in player_stats:
        return player_stats[player_name]
    else:
        raise HTTPException(status_code=404, detail="Player not found")

@app.get("/api/teams-stats/{team_name}")
async def get_team_stats(team_name: str):
    if team_name in team_stats:
        return team_stats[team_name]
    else:
        raise HTTPException(status_code=404, detail="Team not found")
    
@app.get("/get_head_to_head/{team1}/{team2}")
async def get_head_to_head(team1: str, team2: str):
    # look for matches where team1 played against team2
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
        # flip it around cuz teams are backwards in the data
        return {
            "team_a": team1,
            "team_b": team2,
            "team_a_wins": int(match2['Team_B_Wins'].values[0]),
            "team_b_wins": int(match2['Team_A_Wins'].values[0]),
            "total_matches": int(match2['Total_Matches'].values[0])
        }
    else:
        # never played each other before
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
    # find the right players from our data
    team1_players_data = [player for player in teams_data["teams"][team1] 
                            if player["name"] in team1_players and player["present"]]
    
    team2_players_data = [player for player in teams_data["teams"][team2] 
                            if player["name"] in team2_players and player["present"]]
    
    # avg team stats based on players
    team1_avg_elo = sum(player["ELO"] for player in team1_players_data) / len(team1_players_data)
    team2_avg_elo = sum(player["ELO"] for player in team2_players_data) / len(team2_players_data)
    
    team1_avg_form = sum(player["Form"] for player in team1_players_data) / len(team1_players_data)
    team2_avg_form = sum(player["Form"] for player in team2_players_data) / len(team2_players_data)
    
    # who's beaten who before
    h2h_stats = await get_head_to_head(team1, team2)
    team1_wins = h2h_stats["team_a_wins"]
    team2_wins = h2h_stats["team_b_wins"]
    total_matches = h2h_stats["total_matches"]
    
    # not using these but model needs them
    team1_last_5_wins = 0
    team2_last_5_wins = 0
    
    # more stats for the model
    team1_vs_team2_matches = total_matches
    head_to_head_win_rate = team1_wins / total_matches if total_matches > 0 else 0.5
    team1_win_rate = team1_wins / total_matches if total_matches > 0 else 0.5
    
    # put everything in a dataframe for the model
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
        X_scaled = scaler.transform(df_new)
        
        # who's gonna win
        prediction = model.predict(X_scaled)[0]
        win_probability = model.predict_proba(X_scaled)[0]
        
        # figure out who won and chances
        winner = team1 if prediction == 1 else team2
        prob_team1 = round(win_probability[1] * 100, 2) if len(win_probability) > 1 else 50
        prob_team2 = round(win_probability[0] * 100, 2) if len(win_probability) > 1 else 50
        
        # package it all up nicely
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
        # something went wrong better tell what happened
        error_details = {
            "error": str(e),
            "details": {
                "features_used": list(df_new.columns),
                "data_shape": df_new.shape
            }
        }
        print(f"Error in predict: {error_details}")
        return JSONResponse(status_code=500, content=error_details)

app.include_router(router, prefix="")

if __name__ == "__main__":
    if hasattr(model, 'feature_names_in_'):
        print("Model expects these features:")
        print(sorted(model.feature_names_in_))
        
        # keep track of what the model needs
        expected_features = set(model.feature_names_in_)
    else:
        print("Model doesn't have feature_names_in_ attribute")
        expected_features = set()
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
