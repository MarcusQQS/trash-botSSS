import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from collections import defaultdict

TOKEN = os.getenv("TOKEN")
DATA_FILE = "trash.json"
ADMIN_IDS = [967075066]  # 🔐 ЗАМЕНИ на свой Telegram ID

def is_admin(user_id):
    return user_id in ADMIN_IDS

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return defaultdict(int, data)
    return defaultdict(int)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

trash_counts = load_data()
user_ids = {}

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🗑 Вынес мусор")
    builder.button(text="📊 Посмотреть статистику")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: Message):
    name = message.from_user.first_name
    user_ids[name] = message.from_user.id
    await message.answer(
        "Привет! Нажимай кнопки ниже:",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda msg: msg.text == "🗑 Вынес мусор")
async def handle_trash(message: Message):
    user = message.from_user.first_name
    trash_counts[user] += 1
    save_data(trash_counts)
    await message.answer(f"{user}, ты вынес мусор {trash_counts[user]} раз(а)!")

    min_count = min(trash_counts.values())
    for name, count in trash_counts.items():
        if count == min_count and name != user:
            user_id = user_ids.get(name)
            if user_id:
                try:
                    await bot.send_message(user_id, "🔔 Твоя очередь вынести мусор!")
                except Exception:
                    pass

@dp.message(lambda msg: msg.text == "📊 Посмотреть статистику")
async def stats(message: Message):
    if not trash_counts:
        await message.answer("Ещё никто не выносил мусор.")
        return
    stats_text = "📊 Статистика выноса мусора:\n"
    for user, count in sorted(trash_counts.items(), key=lambda x: -x[1]):
        stats_text += f"• {user}: {count}\n"
    await message.answer(stats_text)

# --- АДМИН КОМАНДЫ ---

@dp.message(Command("reset"))
async def reset_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только админ может сбросить статистику.")
        return
    trash_counts.clear()
    save_data(trash_counts)
    await message.answer("✅ Статистика сброшена.")

@dp.message(Command("remove"))
async def remove_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только админ может удалять пользователей.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи имя: /remove Иван")
        return
    name = args[1]
    if name in trash_counts:
        del trash_counts[name]
        save_data(trash_counts)
        await message.answer(f"❌ {name} удалён из статистики.")
    else:
        await message.answer("Имя не найдено.")

@dp.message(Command("add"))
async def add_count(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только админ может изменять счёт.")
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Формат: /add Иван 2")
        return
    name, amount = args[1], args[2]
    try:
        amount = int(amount)
    except ValueError:
        await message.answer("Число указано неправильно.")
        return
    trash_counts[name] += amount
    save_data(trash_counts)
    await message.answer(f"✅ Добавлено {amount} {name} (итого: {trash_counts[name]})")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
