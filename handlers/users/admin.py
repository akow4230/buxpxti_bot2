from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import asyncio
import os
from data.config import ADMINS
from handlers.users.kontrakt import Form
from loader import dp, db, bot

class Form(StatesGroup):
    waiting_for_excel_file = State()
    waiting_for_dars_pdf = State()

class AdStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_text = State()

# Inline keyboards
skip_photo_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Skip Photo', callback_data='skip_photo'),
    InlineKeyboardButton('Cancel', callback_data='cancel')
)
skip_text_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Skip Text', callback_data='skip_text'),
    InlineKeyboardButton('Cancel', callback_data='cancel')
)
cancel_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Cancel', callback_data='cancel'))

@dp.callback_query_handler(lambda c: c.data == 'cancel', state="*")
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Handler to cancel any state."""
    await state.finish()
    await callback_query.answer("Process cancelled.")
    await bot.send_message(callback_query.from_user.id, "The process has been cancelled.")

@dp.message_handler(text="/reklama", user_id=ADMINS)
async def send_ad_prompt(message: types.Message):
    await message.answer("Please send the photo for the ad (or click 'Skip Photo'):", reply_markup=skip_photo_kb)
    await AdStates.waiting_for_photo.set()

@dp.message_handler(state=AdStates.waiting_for_photo, content_types=types.ContentType.PHOTO)
async def handle_ad_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Now send the text for the ad (or click 'Skip Text'):", reply_markup=skip_text_kb)
    await AdStates.waiting_for_text.set()

@dp.callback_query_handler(lambda c: c.data == 'skip_photo', state=AdStates.waiting_for_photo)
async def skip_photo(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await bot.send_message(callback_query.from_user.id, "Photo skipped. Now send the text for the ad (or click 'Skip Text'):", reply_markup=skip_text_kb)
    await AdStates.waiting_for_text.set()

@dp.message_handler(state=AdStates.waiting_for_text, content_types=types.ContentType.TEXT)
async def handle_ad_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()
    photo = data.get('photo')
    ad_text = data['text']
    users = await db.select_all_users()

    for user in users:
        user_id = user[3]
        try:
            if photo:
                await bot.send_photo(chat_id=user_id, photo=photo, caption=ad_text)
            else:
                await bot.send_message(chat_id=user_id, text=ad_text)
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Could not send message to {user_id}: {e}")

    await message.answer("Ad has been sent to all users!")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'skip_text', state=AdStates.waiting_for_text)
async def skip_text(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(text=None)
    data = await state.get_data()
    photo = data.get('photo')
    users = await db.select_all_users()

    for user in users:
        user_id = user[3]
        try:
            if photo:
                await bot.send_photo(chat_id=user_id, photo=photo)
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Could not send message to {user_id}: {e}")

    await bot.send_message(callback_query.from_user.id, "Ad (photo only) has been sent to all users!")
    await state.finish()

@dp.message_handler(text="/upload", user_id=ADMINS)
async def admin_upload_excel(message: types.Message):
    await message.answer("Yangi Excel faylni yuklang:", reply_markup=cancel_kb)
    await Form.waiting_for_excel_file.set()

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=Form.waiting_for_excel_file, user_id=ADMINS)
async def process_excel_file(message: types.Message, state: FSMContext):
    document = message.document
    if document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        try:
            file_path = 'files/bot.xlsx'
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            await document.download(destination_file=file_path)
            await message.answer("Yangi Excel fayl yuklandi va saqlandi!")
        except Exception as e:
            await message.answer(f"Faylni yuklashda xatolik yuz berdi: {str(e)}")
    else:
        await message.answer("Iltimos, faqat Excel faylni yuklang (.xlsx formatida).")

    await state.finish()

@dp.message_handler(text="/dars", user_id=ADMINS)
async def admin_upload_dars(message: types.Message):
    await message.answer("Yangi dars jadvalini yuklang (PDF formatida):", reply_markup=cancel_kb)
    await Form.waiting_for_dars_pdf.set()

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=Form.waiting_for_dars_pdf, user_id=ADMINS)
async def process_dars_pdf(message: types.Message, state: FSMContext):
    document = message.document
    if document.mime_type == 'application/pdf':
        try:
            file_path = 'files/dars.pdf'
            if os.path.exists(file_path):
                os.remove(file_path)
            await document.download(destination_file=file_path)
            await message.answer("Yangi dars jadvali yuklandi va saqlandi!")
            users = await db.select_all_users()
            for user in users:
                user_id = user[3]
                try:
                    await bot.send_message(chat_id=user_id, text="Dars jadvali yangilandi\nIltimos, tekshirib ko'ring.")
                    await asyncio.sleep(0.05)
                except Exception as e:
                    print(f"Could not send message to {user_id}: {e}")
        except Exception as e:
            await message.answer(f"Faylni yuklashda xatolik yuz berdi: {str(e)}")
    else:
        await message.answer("Iltimos, faqat PDF formatidagi faylni yuklang.")

    await state.finish()



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
