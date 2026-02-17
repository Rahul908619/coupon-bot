from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client.coupon_bot

users = db.users
orders = db.orders
coupons = db.coupons
settings = db.settings
logs = db.logs
