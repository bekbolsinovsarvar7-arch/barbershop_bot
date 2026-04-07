import asyncio
import logging
import sqlite3
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

API_TOKEN = os.getenv("8323998350:AAFuTxFKpAB06oLJ1ZV4DYXSymojMmkNxnE")
ADMIN_ID = 1642665028

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# DATABASE
conn = sqlite3.connect("barber.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    time TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    visits INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT
)
""")

conn.commit()

# FUNCTIONS
def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def add_booking(user_id, username, time):
    cursor.execute("INSERT INTO bookings (user_id, username, time) VALUES (?, ?, ?)",
                   (user_id, username, time))
    cursor.execute("UPDATE users SET visits = visits + 1 WHERE user_id = ?", (user_id,))
    conn.commit()

def get_bookings():
    cursor.execute("SELECT time FROM bookings")
    return [row[0] for row in cursor.fetchall()]

def get_all_bookings():
    cursor.execute("SELECT username, time FROM bookings")
    return cursor.fetchall()

def get_visits(user_id):
    cursor.execute("SELECT visits FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def delete_booking(time):
    cursor.execute("DELETE FROM bookings WHERE time = ?", (time,))
    conn.commit()

def add_photo(file_id):
    cursor.execute("INSERT INTO portfolio (file_id) VALUES (?)", (file_id,))
    conn.commit()

def get_photos():
    cursor.execute("SELECT file_id FROM portfolio")
    return [row[0] for row in cursor.fetchall()]

# START
@dp.message(Command("start"))
async def start(message: types.Message):
    add_user(message.from_user.id)

    keyboard = [
        [KeyboardButton(text="📅 Navbat olish"), KeyboardButton(text="💈 Xizmatlar")],
        [KeyboardButton(text="📸 Portfolio"), KeyboardButton(text="⭐ Bonus")],
        [KeyboardButton(text="📍 Lokatsiya")]
    ]

    if message.from_user.id == ADMIN_ID:
        keyboard.append([KeyboardButton(text="👑 Admin panel")])

    kb = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    await message.answer("Xush kelibsiz 💈 Barber botga!", reply_markup=kb)

# SERVICES
@dp.message(F.text == "💈 Xizmatlar")
async def services(message: types.Message):
    await message.answer("💈 Soch — 30k\n🧔 Soqol — 20k\n🔥 Kompleks — 45k")

# BOOKING
@dp.message(F.text == "📅 Navbat olish")
async def booking(message: types.Message):
    booked = get_bookings()
    times = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]

    available = [t for t in times if t not in booked]

    if not available:
        await message.answer("Bugun bo‘sh vaqt yo‘q ❌")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t)] for t in available],
        resize_keyboard=True
    )

    await message.answer("⏰ Bo‘sh vaqtni tanlang:", reply_markup=kb)

# SAVE BOOKING
@dp.message(F.text.contains(":") & ~F.text.startswith("❌"))
async def save_booking(message: types.Message):
    add_booking(message.from_user.id, message.from_user.username, message.text)

    asyncio.create_task(reminder(message.chat.id, message.text))

    await message.answer(f"✅ Siz {message.text} ga yozildingiz!")

# REMINDER
async def reminder(chat_id, time):
    await asyncio.sleep(30)
    await bot.send_message(chat_id, f"⏰ Eslatma: sizda {time} da zapis bor!")

# BONUS
@dp.message(F.text == "⭐ Bonus")
async def bonus(message: types.Message):
    visits = get_visits(message.from_user.id)

    if visits >= 5:
        await message.answer("🎉 Sizga 1 ta BEPUL xizmat!")
    else:
        await message.answer(f"⭐ Siz {visits}/5 marta kelgansiz")

# PORTFOLIO
@dp.message(F.text == "📸 Portfolio")
async def portfolio(message: types.Message):
    photos = get_photos()

    if not photos:
        await message.answer("Hozircha rasmlar yo‘q ❌")
        return

    for p in photos:
        await message.answer_photo(p)

# ADMIN PHOTO
@dp.message(F.photo)
async def save_portfolio_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    file_id = message.photo[-1].file_id
    add_photo(file_id)

    await message.answer("✅ Rasm qo‘shildi!")

# LOCATION
@dp.message(F.text == "📍 Lokatsiya")
async def location(message: types.Message):
    await message.answer_location(41.2995, 69.2401)

# ADMIN PANEL
@dp.message(F.text == "👑 Admin panel")
async def admin_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Barcha zapislar")],
            [KeyboardButton(text="❌ Zapis o‘chirish")]
        ],
        resize_keyboard=True
    )

    await message.answer("Admin panel", reply_markup=kb)

@dp.message(F.text == "📋 Barcha zapislar")
async def all_bookings(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    bookings = get_all_bookings()

    if not bookings:
        await message.answer("Zapis yo‘q")
        return

    text = ""
    for i, (user, time) in enumerate(bookings, start=1):
        text += f"{i}. @{user} — {time}\n"

    await message.answer(text)

@dp.message(F.text == "❌ Zapis o‘chirish")
async def delete_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Qaysi vaqtni o‘chirasiz?")

@dp.message(F.text.contains(":") & (F.from_user.id == ADMIN_ID))
async def delete_handler(message: types.Message):
    delete_booking(message.text)
    await message.answer("❌ O‘chirildi")

# RUN
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
