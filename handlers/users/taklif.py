from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from loader import dp, bot
from data.config import ADMINS
from handlers.users.main import send_welcome

class ComplaintForm(StatesGroup):
    name = State()
    group = State()
    phone = State()
    message = State()

# Cancel button keyboard
cancel_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('❌ Taklif yuborishni bekor qilish', callback_data='cancel'))

@dp.callback_query_handler(Text(equals="taklif"))
async def handle_taklif(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(
        callback_query.from_user.id,
        "Taklif yoki shikoyatingizni yuborish uchun ism familyangizni kiriting.",
        reply_markup=cancel_kb
    )
    await ComplaintForm.name.set()

@dp.callback_query_handler(Text(equals="cancel"), state="*")
async def cancel_process(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler to cancel any complaint process at any state."""
    await state.finish()
    await callback_query.answer("Yuborish bekor qilindi.")
    await bot.send_message(callback_query.from_user.id, "Taklif yuborish jarayoni bekor qilindi.")

@dp.message_handler(state=ComplaintForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Guruh kiriting:", reply_markup=cancel_kb)
    await ComplaintForm.next()

@dp.message_handler(state=ComplaintForm.group)
async def process_group(message: types.Message, state: FSMContext):
    await state.update_data(group=message.text)
    await message.answer("Telefon raqamingizni kiriting:", reply_markup=cancel_kb)
    await ComplaintForm.next()

@dp.message_handler(state=ComplaintForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Shikoyatingiz yoki taklifingizni matn ko'rinishida yuboring:", reply_markup=cancel_kb)
    await ComplaintForm.next()

@dp.message_handler(state=ComplaintForm.message)
async def process_message(message: types.Message, state: FSMContext):
    await state.update_data(message=message.text)
    user_data = await state.get_data()

    telegram_name = message.from_user.full_name
    telegram_username = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    telegram_id = message.from_user.id

    msg = (
        f"Yangi shikoyat/taklif:\n\n"
        f"👤 Ism: {user_data['name']}\n"
        f"📚 Guruh: {user_data['group']}\n"
        f"📞 Telefon: {user_data['phone']}\n"
        f"💬 Xabar: {user_data['message']}\n\n"
        f"👤 Telegram Ismi: {telegram_name}\n"
        f"🏷️ Telegram Username: {telegram_username}\n"
        f"🆔 Telegram ID: {telegram_id}"
    )

    try:
        await bot.send_message(chat_id=ADMINS[0], text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        print("Error sending message to admin:", e)

    await message.answer("Shikoyat yoki taklifingiz uchun rahmat! Xabaringiz adminlarga yuborildi.")
    await send_welcome(message)
    await state.finish()

@dp.errors_handler(exception=Exception)
async def global_error_handler(update, error):
    return True  # Prevents the propagation of errors
