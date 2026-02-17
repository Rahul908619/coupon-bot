from db import coupons

async def get_coupon(value: int):
    c = await coupons.find_one({"value": value, "status": "unused"})
    if not c:
        return None
    await coupons.update_one({"_id": c["_id"]}, {"$set": {"status": "used"}})
    return c["code"]

async def get_stock(value: int):
    return await coupons.count_documents({"value": value, "status": "unused"})
