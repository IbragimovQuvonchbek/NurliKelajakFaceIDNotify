import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties

API_BASE = "http://127.0.0.1:8000/api/v1"

# Replace with your actual bot token
BOT_TOKEN = "8061178459:AAFffd5n0Vd_NQIxz8dAdD2SbGEA-H9dxGQ"


# FSM States
class AddStudentState(StatesGroup):
    waiting_for_student_id = State()


# Set up logging
logging.basicConfig(level=logging.INFO)
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


@dp.message(F.text == "/start")
async def handle_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)

    async with httpx.AsyncClient() as client:
        # Check if TelegramClient exists
        response = await client.get(f"{API_BASE}/telegram-get/", params={"telegram_id": telegram_id})

        if response.status_code == 404:
            # Register new client
            register_resp = await client.post(f"{API_BASE}/telegram-create/", json={"telegram_id": telegram_id})
            if register_resp.status_code == 201:
                await message.answer("✅ Siz ro'yxatdan o'tdingiz!")
            else:
                await message.answer("❌ Xatolik yuz berdi (ro'yxatdan o'tishda).")
                return
        elif response.status_code == 200:
            await message.answer("👋 Assalomu alaykum! Siz avval ro'yxatdan o'tgansiz.")

    # Show add student button
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➕ Student ID qo'shish")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Iltimos, tanlang:", reply_markup=keyboard)


@dp.message(F.text == "➕ Student ID qo'shish")
async def ask_student_id(message: Message, state: FSMContext):
    await message.answer("🆔 Iltimos, student ID kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddStudentState.waiting_for_student_id)


@dp.message(AddStudentState.waiting_for_student_id)
async def receive_student_id(message: Message, state: FSMContext):
    student_id = message.text.strip()
    telegram_id = str(message.from_user.id)

    # Call API to add student
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/student-create/",
            json={"student_id": student_id, "telegram_id": telegram_id}
        )

    if response.status_code == 201:
        await message.answer(f"✅ Student ID <b>{student_id}</b> muvaffaqiyatli qo‘shildi!")
    else:
        await message.answer("❌ Student ID qo‘shishda xatolik yuz berdi.")

    await state.clear()

    # Offer again
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➕ Student ID qo'shish")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Yana biror amal bajarmoqchimisiz?", reply_markup=keyboard)


# Entry point
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
