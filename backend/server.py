from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 720

# Pydantic Models
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    profile_photo: Optional[str] = None
    created_at: str

class AuthResponse(BaseModel):
    token: str
    user: UserResponse

class TripCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    cover_photo: Optional[str] = None

class TripUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cover_photo: Optional[str] = None
    is_public: Optional[bool] = None

class TripResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    cover_photo: Optional[str] = None
    is_public: bool
    share_token: str
    created_at: str

class StopCreate(BaseModel):
    city_id: str
    start_date: str
    end_date: str
    order: int

class StopResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    trip_id: str
    city_id: str
    start_date: str
    end_date: str
    order: int
    city_name: Optional[str] = None
    city_country: Optional[str] = None

class TripActivityCreate(BaseModel):
    activity_id: str
    date: str
    time: Optional[str] = None
    cost: float
    notes: Optional[str] = None

class TripActivityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    stop_id: str
    activity_id: str
    date: str
    time: Optional[str] = None
    cost: float
    notes: Optional[str] = None
    activity_name: Optional[str] = None

class TripCostCreate(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None

class TripCostResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    trip_id: str
    category: str
    amount: float
    description: Optional[str] = None

class CityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    country: str
    region: Optional[str] = None
    cost_index: int
    popularity: int
    description: Optional[str] = None
    image_url: Optional[str] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    city_id: str
    category: str
    cost: float
    duration: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None

# Auth helpers
def create_jwt_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    user_id = verify_jwt_token(token)
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user_id

# Auth routes
@api_router.post("/auth/signup", response_model=AuthResponse)
async def signup(user_data: UserSignup):
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    user_id = secrets.token_urlsafe(16)
    
    user_doc = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password.decode('utf-8'),
        "profile_photo": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    token = create_jwt_token(user_id)
    
    user_response = UserResponse(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        profile_photo=None,
        created_at=user_doc["created_at"]
    )
    
    return AuthResponse(token=token, user=user_response)

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_jwt_token(user['id'])
    user_response = UserResponse(**user)
    
    return AuthResponse(token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

# Trip routes
@api_router.post("/trips", response_model=TripResponse)
async def create_trip(trip_data: TripCreate, user_id: str = Depends(get_current_user)):
    trip_id = secrets.token_urlsafe(16)
    share_token = secrets.token_urlsafe(32)
    
    trip_doc = {
        "id": trip_id,
        "user_id": user_id,
        "name": trip_data.name,
        "description": trip_data.description,
        "start_date": trip_data.start_date,
        "end_date": trip_data.end_date,
        "cover_photo": trip_data.cover_photo,
        "is_public": False,
        "share_token": share_token,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trips.insert_one(trip_doc)
    return TripResponse(**trip_doc)

@api_router.get("/trips", response_model=List[TripResponse])
async def get_trips(user_id: str = Depends(get_current_user)):
    trips = await db.trips.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    return [TripResponse(**trip) for trip in trips]

@api_router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, user_id: str = Depends(get_current_user)):
    trip = await db.trips.find_one({"id": trip_id, "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return TripResponse(**trip)

@api_router.put("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, trip_data: TripUpdate, user_id: str = Depends(get_current_user)):
    trip = await db.trips.find_one({"id": trip_id, "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    update_data = {k: v for k, v in trip_data.model_dump().items() if v is not None}
    if update_data:
        await db.trips.update_one({"id": trip_id}, {"$set": update_data})
        trip.update(update_data)
    
    return TripResponse(**trip)

@api_router.delete("/trips/{trip_id}")
async def delete_trip(trip_id: str, user_id: str = Depends(get_current_user)):
    result = await db.trips.delete_one({"id": trip_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    await db.stops.delete_many({"trip_id": trip_id})
    stops = await db.stops.find({"trip_id": trip_id}, {"_id": 0}).to_list(1000)
    for stop in stops:
        await db.trip_activities.delete_many({"stop_id": stop['id']})
    await db.trip_costs.delete_many({"trip_id": trip_id})
    
    return {"message": "Trip deleted successfully"}

@api_router.get("/trips/shared/{share_token}", response_model=TripResponse)
async def get_shared_trip(share_token: str):
    trip = await db.trips.find_one({"share_token": share_token, "is_public": True}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or not public")
    return TripResponse(**trip)

# Stop routes
@api_router.post("/trips/{trip_id}/stops", response_model=StopResponse)
async def create_stop(trip_id: str, stop_data: StopCreate, user_id: str = Depends(get_current_user)):
    trip = await db.trips.find_one({"id": trip_id, "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    city = await db.cities.find_one({"id": stop_data.city_id}, {"_id": 0})
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    stop_id = secrets.token_urlsafe(16)
    stop_doc = {
        "id": stop_id,
        "trip_id": trip_id,
        "city_id": stop_data.city_id,
        "start_date": stop_data.start_date,
        "end_date": stop_data.end_date,
        "order": stop_data.order
    }
    
    await db.stops.insert_one(stop_doc)
    
    response = StopResponse(**stop_doc)
    response.city_name = city['name']
    response.city_country = city['country']
    return response

@api_router.get("/trips/{trip_id}/stops", response_model=List[StopResponse])
async def get_stops(trip_id: str, user_id: str = Depends(get_current_user)):
    trip = await db.trips.find_one({"id": trip_id, "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    stops = await db.stops.find({"trip_id": trip_id}, {"_id": 0}).sort("order", 1).to_list(1000)
    
    for stop in stops:
        city = await db.cities.find_one({"id": stop['city_id']}, {"_id": 0})
        if city:
            stop['city_name'] = city['name']
            stop['city_country'] = city['country']
    
    return [StopResponse(**stop) for stop in stops]

@api_router.delete("/stops/{stop_id}")
async def delete_stop(stop_id: str, user_id: str = Depends(get_current_user)):
    stop = await db.stops.find_one({"id": stop_id}, {"_id": 0})
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    trip = await db.trips.find_one({"id": stop['trip_id'], "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await db.stops.delete_one({"id": stop_id})
    await db.trip_activities.delete_many({"stop_id": stop_id})
    
    return {"message": "Stop deleted successfully"}

# Trip Activity routes
@api_router.post("/stops/{stop_id}/activities", response_model=TripActivityResponse)
async def add_activity_to_stop(stop_id: str, activity_data: TripActivityCreate, user_id: str = Depends(get_current_user)):
    stop = await db.stops.find_one({"id": stop_id}, {"_id": 0})
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    trip = await db.trips.find_one({"id": stop['trip_id'], "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    activity = await db.activities.find_one({"id": activity_data.activity_id}, {"_id": 0})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    trip_activity_id = secrets.token_urlsafe(16)
    trip_activity_doc = {
        "id": trip_activity_id,
        "stop_id": stop_id,
        "activity_id": activity_data.activity_id,
        "date": activity_data.date,
        "time": activity_data.time,
        "cost": activity_data.cost,
        "notes": activity_data.notes
    }
    
    await db.trip_activities.insert_one(trip_activity_doc)
    
    response = TripActivityResponse(**trip_activity_doc)
    response.activity_name = activity['name']
    return response

@api_router.get("/stops/{stop_id}/activities", response_model=List[TripActivityResponse])
async def get_stop_activities(stop_id: str, user_id: str = Depends(get_current_user)):
    stop = await db.stops.find_one({"id": stop_id}, {"_id": 0})
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    trip = await db.trips.find_one({"id": stop['trip_id'], "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    trip_activities = await db.trip_activities.find({"stop_id": stop_id}, {"_id": 0}).to_list(1000)
    
    for ta in trip_activities:
        activity = await db.activities.find_one({"id": ta['activity_id']}, {"_id": 0})
        if activity:
            ta['activity_name'] = activity['name']
    
    return [TripActivityResponse(**ta) for ta in trip_activities]

@api_router.delete("/trip-activities/{activity_id}")
async def delete_trip_activity(activity_id: str, user_id: str = Depends(get_current_user)):
    trip_activity = await db.trip_activities.find_one({"id": activity_id}, {"_id": 0})
    if not trip_activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    stop = await db.stops.find_one({"id": trip_activity['stop_id']}, {"_id": 0})
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    trip = await db.trips.find_one({"id": stop['trip_id'], "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await db.trip_activities.delete_one({"id": activity_id})
    return {"message": "Activity deleted successfully"}

# Cost routes
@api_router.post("/trips/{trip_id}/costs", response_model=TripCostResponse)
async def add_trip_cost(trip_id: str, cost_data: TripCostCreate, user_id: str = Depends(get_current_user)):
    trip = await db.trips.find_one({"id": trip_id, "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    cost_id = secrets.token_urlsafe(16)
    cost_doc = {
        "id": cost_id,
        "trip_id": trip_id,
        "category": cost_data.category,
        "amount": cost_data.amount,
        "description": cost_data.description
    }
    
    await db.trip_costs.insert_one(cost_doc)
    return TripCostResponse(**cost_doc)

@api_router.get("/trips/{trip_id}/costs", response_model=List[TripCostResponse])
async def get_trip_costs(trip_id: str, user_id: str = Depends(get_current_user)):
    trip = await db.trips.find_one({"id": trip_id, "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    costs = await db.trip_costs.find({"trip_id": trip_id}, {"_id": 0}).to_list(1000)
    return [TripCostResponse(**cost) for cost in costs]

@api_router.delete("/costs/{cost_id}")
async def delete_cost(cost_id: str, user_id: str = Depends(get_current_user)):
    cost = await db.trip_costs.find_one({"id": cost_id}, {"_id": 0})
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
    
    trip = await db.trips.find_one({"id": cost['trip_id'], "user_id": user_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await db.trip_costs.delete_one({"id": cost_id})
    return {"message": "Cost deleted successfully"}

# City routes
@api_router.get("/cities", response_model=List[CityResponse])
async def get_cities(search: Optional[str] = None, country: Optional[str] = None):
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if country:
        query["country"] = country
    
    cities = await db.cities.find(query, {"_id": 0}).limit(50).to_list(50)
    return [CityResponse(**city) for city in cities]

@api_router.get("/cities/{city_id}", response_model=CityResponse)
async def get_city(city_id: str):
    city = await db.cities.find_one({"id": city_id}, {"_id": 0})
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return CityResponse(**city)

# Activity routes
@api_router.get("/activities", response_model=List[ActivityResponse])
async def get_activities(city_id: Optional[str] = None, category: Optional[str] = None, search: Optional[str] = None):
    query = {}
    if city_id:
        query["city_id"] = city_id
    if category:
        query["category"] = category
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    activities = await db.activities.find(query, {"_id": 0}).limit(50).to_list(50)
    return [ActivityResponse(**activity) for activity in activities]

@api_router.get("/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(activity_id: str):
    activity = await db.activities.find_one({"id": activity_id}, {"_id": 0})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ActivityResponse(**activity)

# User profile routes
@api_router.get("/users/profile", response_model=UserResponse)
async def get_user_profile(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

@api_router.put("/users/profile", response_model=UserResponse)
async def update_user_profile(profile_data: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        user.update(update_data)
    
    return UserResponse(**user)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
