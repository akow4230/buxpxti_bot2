import asyncpg
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from loader import dp, db, bot
from data.config import ADMINS


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    try:
        user = await db.add_user(telegram_id=message.from_user.id,
                                 full_name=message.from_user.full_name,
                                 username=message.from_user.username)
        await message.answer("Xush kelibsiz!")
        # ADMINGA xabar beramiz
        count = await db.count_users()
        msg = f"{user[1]} bazaga qo'shildi.\nBazada {count} ta foydalanuvchi bor."
        await bot.send_message(chat_id=855893763, text=msg)
    except asyncpg.exceptions.UniqueViolationError:
        user = await db.select_user(telegram_id=message.from_user.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Ma'lumotnoma olish", callback_data='malumotnoma'),
        InlineKeyboardButton("Chaqiruv qog'ozi", callback_data='chaqiruv'),
        InlineKeyboardButton("Dars jadvali", callback_data='timetable'),
        InlineKeyboardButton("Kontrakt tolo'vi haqida ma'lumot", callback_data='kontrakt'),
        InlineKeyboardButton("To'lov shartnoma", callback_data='shartnoma'),
        InlineKeyboardButton("Taklif va shikoyat", callback_data='taklif'),
        # InlineKeyboardButton("Fanlardan qarzdorlik va o'zlashtirganlik haqida ma'lumot olish", callback_data='qarz'),
    )
    await message.answer(
        """Assalomu alaykum \n<b>"Buxoro psixologiya va xorijiy tillar instituti"</b> elektron ma'lumotlarni olish xizmati.\n"""
        "Xizmatdan foydalanish uchun quyidagi tugmalardan birini tanlang!",
        reply_markup=keyboard,parse_mode=ParseMode.HTML)


