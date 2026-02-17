import razorpay
from config import RAZORPAY_KEY, RAZORPAY_SECRET

client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

def create_order(amount: int, receipt: str):
    return client.order.create({
        "amount": amount * 100,  # paise
        "currency": "INR",
        "receipt": receipt
    })
