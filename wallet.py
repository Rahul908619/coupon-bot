from db import users

async def add_balance(user_id: int, amount: float):
    await users.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

async def use_balance(user_id: int, amount: float):
    u = await users.find_one({"user_id": user_id})
    if not u or u.get("balance", 0) < amount:
        return False
    await users.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}})
    return True

async def get_balance(user_id: int):
    u = await users.find_one({"user_id": user_id})
    return u.get("balance", 0) if u else 0
