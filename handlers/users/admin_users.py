from sre_parse import State

from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from loader import dp, db, bot
from data.config import ADMINS

# FSM for /write command
class WriteToUserForm(StatesGroup):
    user_id = State()
    message = State()

# /show command handler to display all users
@dp.message_handler(text="/show", user_id=ADMINS)
async def show_all_users(message: types.Message):
    print("hi")
    users = await db.select_all_users()
    if users:
        user_list = "\n".join(
            [f"ID: {user['telegram_id']}, Ism: {user['full_name']}, Username: @{user['username']}" for user in users]
        )
        await message.answer(f"Foydalanuvchilar:\n\n{user_list}", parse_mode=ParseMode.HTML)
    else:
        await message.answer("Hozirda foydalanuvchilar ro'yxati bo'sh.")

# /write command handler to initiate message sending to a specific user
@dp.message_handler(text="/write", user_id=855893763)
async def write_to_user_start(message: types.Message):
    await message.answer("Foydalanuvchi ID raqamini kiriting:")
    await WriteToUserForm.user_id.set()

# Handler to capture user ID
@dp.message_handler(state=WriteToUserForm.user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():  # Ensure it's a numeric ID
        await state.update_data(user_id=int(user_id))
        await message.answer("Yubormoqchi bo'lgan xabaringizni yozing:")
        await WriteToUserForm.message.set()
    else:
        await message.answer("Iltimos, to'g'ri foydalanuvchi ID raqamini kiriting.")

# Handler to capture and send the message
@dp.message_handler(state=WriteToUserForm.message)
async def process_user_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data["user_id"]
    user_message = message.text

    try:
        await bot.send_message(chat_id=user_id, text=user_message)
        await message.answer(f"Xabar foydalanuvchiga (ID: {user_id}) yuborildi.")
    except Exception as e:
        await message.answer(f"Xabarni yuborishda xatolik yuz berdi: {e}")
    finally:
        await state.finish()
