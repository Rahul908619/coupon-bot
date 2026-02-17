import os
from motor.motor_asyncio import AsyncIOMotorClient

# Single MONGO_URL source
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError("MONGO_URL not set in environment")

client = AsyncIOMotorClient(MONGO_URL)
db = client.coupon_bot

# Collections
users = db.users
orders = db.orders
coupons = db.coupons
settings = db.settings
logs = db.logs

# Test connection
async def test_connection():
    try:
        await db.command("ping")
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
