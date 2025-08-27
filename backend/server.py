from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, timezone
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Mood constants
MOODS = {
    1: {"emoji": "😢", "label": "Very Sad"},
    2: {"emoji": "😕", "label": "Sad"},
    3: {"emoji": "😐", "label": "Neutral"},
    4: {"emoji": "🙂", "label": "Happy"},
    5: {"emoji": "😄", "label": "Very Happy"}
}

# Helper functions for MongoDB date handling
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data.get('entry_date'), date):
        data['entry_date'] = data['entry_date'].isoformat()
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    return data

def parse_from_mongo(item):
    """Parse MongoDB data back to Python objects"""
    if isinstance(item.get('entry_date'), str):
        item['entry_date'] = datetime.fromisoformat(item['entry_date']).date()
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    return item

# Define Models
class MoodEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entry_date: date
    mood_score: int = Field(..., ge=1, le=5, description="Mood score from 1-5")
    emoji: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }

class MoodEntryCreate(BaseModel):
    entry_date: date
    mood_score: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None

class MoodEntryUpdate(BaseModel):
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None

# Routes
@api_router.get("/")
async def root():
    return {"message": "Mood Tracker API"}

@api_router.get("/moods/options")
async def get_mood_options():
    return {"moods": MOODS}

@api_router.post("/moods", response_model=MoodEntry)
async def create_mood_entry(mood_data: MoodEntryCreate):
    # Check if entry already exists for this date
    existing_entry = await db.mood_entries.find_one({
        "entry_date": mood_data.entry_date.isoformat()
    })
    
    if existing_entry:
        raise HTTPException(status_code=400, detail="Mood entry already exists for this date")
    
    # Create mood entry with emoji
    mood_dict = mood_data.dict()
    mood_dict["emoji"] = MOODS[mood_data.mood_score]["emoji"]
    mood_entry = MoodEntry(**mood_dict)
    
    # Prepare for MongoDB storage
    entry_dict = prepare_for_mongo(mood_entry.dict())
    await db.mood_entries.insert_one(entry_dict)
    
    return mood_entry

@api_router.get("/moods", response_model=List[MoodEntry])
async def get_mood_entries(limit: Optional[int] = 100):
    entries = await db.mood_entries.find().sort("entry_date", -1).to_list(limit)
    return [MoodEntry(**parse_from_mongo(entry)) for entry in entries]

@api_router.get("/moods/{entry_date}")
async def get_mood_by_date(entry_date: str):
    entry = await db.mood_entries.find_one({"entry_date": entry_date})
    if not entry:
        raise HTTPException(status_code=404, detail="Mood entry not found for this date")
    return MoodEntry(**parse_from_mongo(entry))

@api_router.put("/moods/{entry_date}", response_model=MoodEntry)
async def update_mood_entry(entry_date: str, mood_update: MoodEntryUpdate):
    existing_entry = await db.mood_entries.find_one({"entry_date": entry_date})
    if not existing_entry:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    
    update_data = {}
    if mood_update.mood_score is not None:
        update_data["mood_score"] = mood_update.mood_score
        update_data["emoji"] = MOODS[mood_update.mood_score]["emoji"]
    if mood_update.notes is not None:
        update_data["notes"] = mood_update.notes
    
    if update_data:
        await db.mood_entries.update_one(
            {"entry_date": entry_date},
            {"$set": update_data}
        )
    
    updated_entry = await db.mood_entries.find_one({"entry_date": entry_date})
    return MoodEntry(**parse_from_mongo(updated_entry))

@api_router.delete("/moods/{entry_date}")
async def delete_mood_entry(entry_date: str):
    result = await db.mood_entries.delete_one({"entry_date": entry_date})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    return {"message": "Mood entry deleted successfully"}

@api_router.get("/moods/stats/summary")
async def get_mood_stats():
    # Get all mood entries
    entries = await db.mood_entries.find().to_list(1000)
    
    if not entries:
        return {
            "total_entries": 0,
            "average_mood": 0,
            "mood_distribution": {},
            "recent_trend": []
        }
    
    # Calculate statistics
    mood_scores = [entry["mood_score"] for entry in entries]
    total_entries = len(entries)
    average_mood = sum(mood_scores) / total_entries
    
    # Mood distribution
    mood_distribution = {}
    for score in mood_scores:
        mood_info = MOODS[score]
        key = f"{mood_info['emoji']} {mood_info['label']}"
        mood_distribution[key] = mood_distribution.get(key, 0) + 1
    
    # Recent trend (last 7 entries)
    recent_entries = sorted(entries, key=lambda x: x["entry_date"], reverse=True)[:7]
    recent_trend = [
        {
            "date": entry["entry_date"],
            "mood_score": entry["mood_score"],
            "emoji": entry["emoji"]
        }
        for entry in reversed(recent_entries)  # Reverse to get chronological order
    ]
    
    return {
        "total_entries": total_entries,
        "average_mood": round(average_mood, 2),
        "mood_distribution": mood_distribution,
        "recent_trend": recent_trend
    }

@api_router.get("/moods/export/csv")
async def export_moods_csv():
    entries = await db.mood_entries.find().sort("entry_date", 1).to_list(1000)
    
    if not entries:
        return {"csv_data": "Date,Mood Score,Emoji,Mood Label,Notes\n"}
    
    csv_lines = ["Date,Mood Score,Emoji,Mood Label,Notes"]
    
    for entry in entries:
        mood_label = MOODS[entry["mood_score"]]["label"]
        notes = (entry.get("notes", "") or "").replace('"', '""')  # Escape quotes for CSV
        csv_lines.append(
            f'{entry["entry_date"]},{entry["mood_score"]},"{entry["emoji"]}","{mood_label}","{notes}"'
        )
    
    return {"csv_data": "\n".join(csv_lines)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()