import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, COUPON_TYPES
from db import users, orders, settings
from payment import create_order
from coupon import get_coupon, get_stock
from wallet import get_balance, use_balance, add_balance
from referral import set_ref, reward_referrer
from admin import set_price, broadcast, bulk_upload

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class BuyStates(StatesGroup):
    waiting_qty = State()

@dp.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    await users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id, "joined_at": asyncio.get_event_loop().time()}}, upsert=True)
    
    # Referral check (parse /start ref123)
    if len(msg.text.split()) > 1:
        ref = int(msg.text.split()[1])
        await set_ref(user_id, ref)
        await reward_referrer(user_id)
        await msg.answer("✅ Referred! Check /balance")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"₹{v}", callback_data=f"buy_{v}")] for v in COUPON_TYPES
    ])
    await msg.answer("Select coupon value:", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_callback(call: types.CallbackQuery, state: FSMContext):
    value = int(call.data.split("_")[1])
    await state.set_data({"value": value})
    await state.set_state(BuyStates.waiting_qty)
    await call.message.answer("Enter quantity:")

@dp.message(BuyStates.waiting_qty)
async def process_qty(msg: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        value = data["value"]
        qty = int(msg.text)
        stock = await get_stock(value)
        if stock < qty:
            await msg.answer(f"❌ Only {stock} left for ₹{value}")
            await state.clear()
            return

        s = await settings.find_one({})
        price_per = s.get(f"coupon_{value}", 30) if s else 30
        total = price_per * qty
        receipt = f"rcpt_{msg.from_user.id}_{asyncio.get_event_loop().time()}"

        order = create_order(total, receipt)
        await orders.insert_one({
            "gateway_order": order["id"],
            "user_id": msg.from_user.id,
            "value": value,
            "qty": qty,
            "amount": total,
            "status": "pending"
        })

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Check Payment", callback_data=f"check_{order['id']}")]
        ])
        await msg.answer(f"Pay ₹{total}\n\n🔗 https://rzp.io/i/{order['id']}", reply_markup=kb)
        await state.clear()
    except ValueError:
        await msg.answer("❌ Enter valid number")

@dp.message(Command("balance"))
async def balance(msg: types.Message):
    bal = await get_balance(msg.from_user.id)
    await msg.answer(f"💰 Your balance: ₹{bal:.2f}")

@dp.message(Command("setprice"))
async def cmd_set_price(msg: types.Message):
    await set_price(msg)

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: types.Message):
    await broadcast(msg, bot)

@dp.message(F.document)
async def handle_doc(msg: types.Message):
    await bulk_upload(msg, bot)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
