from fastapi import FastAPI, Request, HTTPException
from db import orders
import razorpay
from config import WEBHOOK_SECRET
from bot import bot  # Shared bot instance
from coupon import get_coupon

app = FastAPI()

@app.post("/webhook/")
async def webhook_endpoint(request: Request):
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    
    try:
        razorpay.utility.verify_webhook_signature(body.decode(), signature, WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    if data.get("event") != "payment.captured":
        return {"status": "ok"}

    order_id = data["payload"]["payment"]["entity"]["order_id"]
    order = await orders.find_one({"gateway_order": order_id})
    if not order or order["status"] == "paid":
        return {"status": "ok"}

    await orders.update_one({"_id": order["_id"]}, {"$set": {"status": "paid"}})

    # Auto send coupons
    for _ in range(order["qty"]):
        code = await get_coupon(order["value"])
        if code:
            await bot.send_message(order["user_id"], f"🎟 Your coupon: `{code}`", parse_mode="Markdown")

    await bot.send_message(order["user_id"], "✅ Payment received! Coupons delivered.")
    return {"status": "ok"}
