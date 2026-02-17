from db import users
from wallet import add_balance

async def set_ref(user_id: int, ref_id: int):
    if user_id == ref_id:
        return
    await users.update_one({"user_id": user_id}, {"$set": {"ref_by": ref_id}}, upsert=True)

async def reward_referrer(new_user_id: int, amount: float = 5.0):
    u = await users.find_one({"user_id": new_user_id})
    if u and u.get("ref_by"):
        await add_balance(u["ref_by"], amount)
