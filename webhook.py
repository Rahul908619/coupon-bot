import os
import razorpay
from fastapi import FastAPI, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, WEBHOOK_SECRET, BOT_TOKEN
from bot import bot  # Shared bot instance

# Database direct connect (no db.py import)
client = AsyncIOMotorClient(MONGO_URL)
db = client.coupon_bot
orders = db.orders
coupons = db.coupons

app = FastAPI(title="Coupon Bot Webhook")

@app.get("/")
async def health_check():
    return {"status": "Coupon Bot Webhook Active ✅"}

@app.post("/webhook/")
async def webhook_endpoint(request: Request):
    # Raw body + signature
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    
    # Verify signature first
    try:
        razorpay.utility.verify_webhook_signature(
            body.decode('utf-8'), 
            signature, 
            WEBHOOK_SECRET
        )
    except Exception as e:
        print(f"Webhook signature failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse JSON
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Only process payment.captured
    if data.get("event") != "payment.captured":
        return {"status": "ok", "event": data.get("event")}

    print(f"Payment captured: {data['payload']['payment']['entity']['id']}")

    # Find order
    order_id = data["payload"]["payment"]["entity"]["order_id"]
    order = await orders.find_one({"gateway_order": order_id})
    
    if not order or order.get("status") == "paid":
        print(f"Order {order_id} already processed or not found")
        return {"status": "ok"}

    # Mark as paid
    await orders.update_one(
        {"_id": order["_id"]}, 
        {"$set": {"status": "paid", "payment_id": data["payload"]["payment"]["entity"]["id"]}}
    )
    print(f"Order {order_id} marked as paid")

    # Send coupons automatically
    user_id = order["user_id"]
    value = order["value"]
    qty = order["qty"]
    
    sent_coupons = []
    for i in range(qty):
        coupon_code = await coupons.find_one_and_update(
            {"value": value, "status": "unused"},
            {"$set": {"status": "used"}},
            projection={"_id": False, "code": True}
        )
        
        if coupon_code and "code" in coupon_code:
            sent_coupons.append(coupon_code["code"])
            await bot.send_message(
                user_id, 
                f"🎟 Coupon #{i+1}: `{coupon_code['code']}`", 
                parse_mode="Markdown"
            )
    
    # Final confirmation
    if sent_coupons:
        await bot.send_message(
            user_id, 
            f"✅ Payment successful! Delivered {len(sent_coupons)} coupons of ₹{value} each.\n"
            f"💰 Amount: ₹{order['amount']}"
        )
    else:
        await bot.send_message(
            user_id, 
            "⚠️ Payment received but no coupons available. Contact admin."
        )

    print(f"Sent {len(sent_coupons)} coupons to user {user_id}")
    return {"status": "ok", "coupons_sent": len(sent_coupons)}

# Railway port support
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("webhook:app", host="0.0.0.0", port=port, reload=False)
