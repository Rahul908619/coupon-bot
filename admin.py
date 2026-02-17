from aiogram import types
from config import ADMIN_ID
from db import settings, users, coupons
from wallet import add_balance

async def set_price(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, value, price = msg.text.split()
        await settings.update_one({}, {"$set": {f"coupon_{value}": int(price)}}, upsert=True)
        await msg.answer(f"✅ Price for ₹{value} set to ₹{price}")
    except:
        await msg.answer("❌ Use: /setprice 500 40")

async def broadcast(msg: types.Message, bot):
    if msg.from_user.id != ADMIN_ID:
        return
    text = msg.text.split(maxsplit=1)[1] if len(msg.text.split()) > 1 else "Hello!"
    async for u in users.find():
        try:
            await bot.send_message(u["user_id"], text)
        except:
            pass
    await msg.answer("📢 Broadcast sent!")

async def bulk_upload(msg: types.Message, bot):
    if msg.from_user.id != ADMIN_ID or not msg.document:
        return
    file = await bot.get_file(msg.document.file_id)
    data = await bot.download_file(file.file_path)
    lines = [line.strip() for line in data.decode().splitlines() if line.strip()]
    value = 500  # Default; change via command like /bulk 1000
    await coupons.insert_many([{"code": c, "value": value, "status": "unused"} for c in lines])
    await msg.answer(f"✅ Uploaded {len(lines)} coupons of ₹{value}")
