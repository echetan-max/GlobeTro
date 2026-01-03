import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

cities_data = [
    {
        "id": secrets.token_urlsafe(16),
        "name": "Paris",
        "country": "France",
        "region": "Europe",
        "cost_index": 85,
        "popularity": 95,
        "description": "The City of Light, known for its art, culture, and cuisine",
        "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Tokyo",
        "country": "Japan",
        "region": "Asia",
        "cost_index": 80,
        "popularity": 90,
        "description": "A vibrant metropolis blending tradition and modernity",
        "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "New York",
        "country": "USA",
        "region": "North America",
        "cost_index": 90,
        "popularity": 92,
        "description": "The city that never sleeps, center of culture and finance",
        "image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Barcelona",
        "country": "Spain",
        "region": "Europe",
        "cost_index": 70,
        "popularity": 88,
        "description": "Mediterranean paradise with stunning architecture",
        "image_url": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Bali",
        "country": "Indonesia",
        "region": "Asia",
        "cost_index": 40,
        "popularity": 85,
        "description": "Tropical paradise with beautiful beaches and temples",
        "image_url": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "London",
        "country": "UK",
        "region": "Europe",
        "cost_index": 95,
        "popularity": 93,
        "description": "Historic capital with world-class museums and culture",
        "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Dubai",
        "country": "UAE",
        "region": "Middle East",
        "cost_index": 85,
        "popularity": 87,
        "description": "Futuristic city with luxury shopping and architecture",
        "image_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Sydney",
        "country": "Australia",
        "region": "Oceania",
        "cost_index": 88,
        "popularity": 86,
        "description": "Harbor city with iconic landmarks and beaches",
        "image_url": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Rome",
        "country": "Italy",
        "region": "Europe",
        "cost_index": 75,
        "popularity": 91,
        "description": "Ancient city with remarkable history and cuisine",
        "image_url": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800"
    },
    {
        "id": secrets.token_urlsafe(16),
        "name": "Bangkok",
        "country": "Thailand",
        "region": "Asia",
        "cost_index": 35,
        "popularity": 84,
        "description": "Bustling city with vibrant street life and temples",
        "image_url": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=800"
    }
]

async def seed_activities(cities):
    activities_data = []
    categories = ["Sightseeing", "Adventure", "Food & Dining", "Culture", "Shopping", "Entertainment", "Nature"]
    
    activity_templates = {
        "Paris": [
            ("Eiffel Tower Visit", "Sightseeing", 25, "2-3 hours", "Iconic landmark with breathtaking views"),
            ("Louvre Museum Tour", "Culture", 17, "3-4 hours", "World's largest art museum"),
            ("Seine River Cruise", "Sightseeing", 15, "1 hour", "Romantic boat ride through Paris"),
            ("Montmartre Walking Tour", "Culture", 30, "2-3 hours", "Explore historic artist quarter"),
        ],
        "Tokyo": [
            ("Tokyo Skytree", "Sightseeing", 20, "2 hours", "Tallest structure in Japan"),
            ("Sushi Making Class", "Food & Dining", 80, "3 hours", "Learn authentic sushi preparation"),
            ("Sensoji Temple Visit", "Culture", 0, "1-2 hours", "Ancient Buddhist temple"),
            ("Shibuya Crossing Tour", "Sightseeing", 15, "2 hours", "Experience the world's busiest intersection"),
        ],
        "New York": [
            ("Statue of Liberty", "Sightseeing", 25, "3-4 hours", "Iconic American symbol"),
            ("Central Park Tour", "Nature", 0, "2-3 hours", "Urban oasis in Manhattan"),
            ("Broadway Show", "Entertainment", 150, "2-3 hours", "World-class theater experience"),
            ("Empire State Building", "Sightseeing", 42, "2 hours", "Legendary skyscraper with panoramic views"),
        ],
        "Barcelona": [
            ("Sagrada Familia Tour", "Culture", 26, "2 hours", "Gaudi's masterpiece basilica"),
            ("Park Güell Visit", "Sightseeing", 10, "2 hours", "Colorful park with mosaic art"),
            ("Tapas Food Tour", "Food & Dining", 60, "3 hours", "Authentic Spanish cuisine experience"),
            ("Gothic Quarter Walk", "Culture", 20, "2 hours", "Medieval streets and architecture"),
        ],
        "Bali": [
            ("Ubud Rice Terraces", "Nature", 5, "2-3 hours", "Stunning emerald landscapes"),
            ("Tanah Lot Temple", "Culture", 3, "1-2 hours", "Sea temple at sunset"),
            ("Surfing Lesson", "Adventure", 35, "2 hours", "Learn to surf in paradise"),
            ("Balinese Cooking Class", "Food & Dining", 40, "4 hours", "Traditional Indonesian cuisine"),
        ],
        "London": [
            ("Tower of London", "Culture", 32, "3 hours", "Historic castle and crown jewels"),
            ("British Museum", "Culture", 0, "2-3 hours", "World cultures and history"),
            ("Thames River Cruise", "Sightseeing", 18, "1 hour", "See landmarks from the water"),
            ("Afternoon Tea Experience", "Food & Dining", 45, "2 hours", "Traditional British tea service"),
        ],
        "Dubai": [
            ("Burj Khalifa Observation", "Sightseeing", 40, "2 hours", "World's tallest building"),
            ("Desert Safari", "Adventure", 70, "6 hours", "Dune bashing and BBQ dinner"),
            ("Dubai Mall Shopping", "Shopping", 0, "3-4 hours", "Luxury shopping paradise"),
            ("Gold Souk Visit", "Shopping", 0, "1-2 hours", "Traditional gold market"),
        ],
        "Sydney": [
            ("Opera House Tour", "Culture", 25, "1 hour", "Iconic architectural marvel"),
            ("Harbour Bridge Climb", "Adventure", 250, "3 hours", "Climb the famous bridge"),
            ("Bondi Beach", "Nature", 0, "3-4 hours", "Famous surf beach"),
            ("Taronga Zoo", "Entertainment", 50, "4 hours", "Wildlife with harbour views"),
        ],
        "Rome": [
            ("Colosseum Tour", "Culture", 16, "2 hours", "Ancient Roman amphitheater"),
            ("Vatican Museums", "Culture", 17, "3 hours", "Sistine Chapel and art treasures"),
            ("Trevi Fountain Visit", "Sightseeing", 0, "30 min", "Baroque masterpiece"),
            ("Food Tour in Trastevere", "Food & Dining", 55, "3 hours", "Authentic Roman cuisine"),
        ],
        "Bangkok": [
            ("Grand Palace", "Culture", 15, "2-3 hours", "Ornate royal complex"),
            ("Floating Market Tour", "Sightseeing", 25, "3 hours", "Traditional market on water"),
            ("Thai Massage", "Entertainment", 20, "1-2 hours", "Authentic relaxation"),
            ("Street Food Tour", "Food & Dining", 30, "3 hours", "Explore Bangkok's food scene"),
        ]
    }
    
    for city in cities:
        city_name = city['name']
        if city_name in activity_templates:
            for activity_name, category, cost, duration, description in activity_templates[city_name]:
                activities_data.append({
                    "id": secrets.token_urlsafe(16),
                    "name": activity_name,
                    "city_id": city['id'],
                    "category": category,
                    "cost": float(cost),
                    "duration": duration,
                    "description": description,
                    "image_url": city['image_url']
                })
    
    return activities_data

async def seed_database():
    print("Seeding database...")
    
    await db.cities.delete_many({})
    await db.activities.delete_many({})
    
    await db.cities.insert_many(cities_data)
    print(f"Inserted {len(cities_data)} cities")
    
    activities = await seed_activities(cities_data)
    if activities:
        await db.activities.insert_many(activities)
        print(f"Inserted {len(activities)} activities")
    
    print("Database seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_database())
