from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json
from pathlib import Path

# Create a router
router = APIRouter()

# Load venue stats from a JSON file or database
# For this example, let's assume you've preprocessed the data and stored it in a JSON file
venue_stats = {}

# Path to your venue stats data
VENUE_STATS_PATH = Path("data/venue_stats.json")

def load_venue_stats():
    """Load venue statistics from JSON file"""
    global venue_stats
    try:
        if VENUE_STATS_PATH.exists():
            with open(VENUE_STATS_PATH, "r") as  f:
                venue_stats = json.load(f)
        else:
            # If file doesn't exist, create a sample structure
            venue_stats = {}
    except Exception as e:
        print(f"Error loading venue stats: {e}")
        venue_stats = {}

# Load the stats on startup
load_venue_stats()

@router.get("/api/venue-stats/{venue_name}")
async def get_venue_stats(venue_name: str) -> Dict[str, Any]:
    """
    Get statistics for a specific venue
    """
    if venue_name not in venue_stats:
        raise HTTPException(status_code=404, detail=f"Stats for venue '{venue_name}' not found")
    
    return venue_stats[venue_name]

@router.get("/api/venues")
async def get_venues():
    """
    Get list of all venues
    """
    return list(venue_stats.keys())

# You can add this router to your main FastAPI app
# Example in your main.py:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router)