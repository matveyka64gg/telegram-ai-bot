import os
import asyncio
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from openai import OpenAI

# ───────────────
# ENV
# ───────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN is missing")
    sys.exit()

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY is missing")
    sys.exit()

# ───────────────
# BOT INIT
# ───────────────
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# ───────────────
# DATA STORAGE
# ───────────────
memory = {}
user_model = {}
user_persona = {}
user_character = {}

MODELS = {
    "llama": "llama-3.1-8b-instant",
    "mixtral": "mixtral-8x7b-32768"
}

# ───────────────
# KEYBOARD
# ───────────────
def model_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🤖 llama"),
                KeyboardButton(text="⚡ mixtral")
            ]
        ],
        resize_keyboard=True
    )

# ───────────────
# START
# ───────────────
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id

    memory[user_id] = []
    user_model[user_id] = MODELS["llama"]
    user_persona[user_id] = ""
    user_character[user_id] = "Ты полезный AI помощник."

    await message.answer(
        "🤖 БОТ ЗАПУЩЕН\n\n"
        "Команды:\n"
        "/persona — описать себя\n"
        "/character — задать характер бота\n"
        "/reset — очистить память\n\n"
        "👇 Выбери модель:",
        reply_markup=model_keyboard()
    )

# ───────────────
# MAIN HANDLER
# ───────────────
@dp.message()
async def handler(message: types.Message):
    user_id = message.from_user.id
    text = message.text or ""

    if user_id not in memory:
        memory[user_id] = []
        user_model[user_id] = MODELS["llama"]
        user_persona[user_id] = ""
        user_character[user_id] = "Ты полезный AI помощник."

    # ───── MODEL SELECT
    if text in ["🤖 llama", "⚡ mixtral"]:
        model_key = "llama" if "llama" in text else "mixtral"
        user_model[user_id] = MODELS[model_key]

        await message.answer(
            f"✅ Модель выбрана: {model_key}",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # ───── PERSONA
    if text.startswith("/persona"):
        user_persona[user_id] = text.replace("/persona", "").strip()
        await message.answer("🧠 Persona сохранена")
        return

    # ───── CHARACTER
    if text.startswith("/character"):
        user_character[user_id] = text.replace("/character", "").strip()
        await message.answer("🎭 Character обновлён")
        return

    # ───── RESET
    if text == "/reset":
        memory[user_id] = []
        await message.answer("🧹 память очищена")
        return

    # ───── CHAT MEMORY
    memory[user_id].append({"role": "user", "content": text})
    history = memory[user_id][-15:]

    try:
        response = client.chat.completions.create(
            model=user_model[user_id],
            messages=[
                {"role": "system", "content": user_character[user_id]},
                {"role": "system", "content": f"Информация о пользователе: {user_persona[user_id]}"},
                *history
            ]
        )

        answer = response.choices[0].message.content

    except Exception as e:
        answer = f"❌ Ошибка API: {str(e)}"

    memory[user_id].append({"role": "assistant", "content": answer})

    await message.answer(answer)

# ───────────────
# RUN
# ───────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())