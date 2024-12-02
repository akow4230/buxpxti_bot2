import os
import tempfile

import aiohttp
import fitz
from aiogram import  types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup

from handlers.users.app import search_in_sheet_by_passport_pin
from loader import dp, db, bot
from data.config import ADMINS
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from handlers.users.generate_pdf import generate_pdf_with_qr
from handlers.users.read_pdf import get_next_row_text_with_pages

file_path = 'files/bot.xlsx'
file_path_dars =  'files/dars.pdf'
ADMIN_IDS = [855893763]
class Form(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_course_selection = State()
    waiting_for_name_input = State()
    waiting_for_excel_file = State()  # New state for Excel file upload











async def convert_pdf_page_to_image(pdf_path, page_number, output_path):
    pdf_document = fitz.open(pdf_path)

    if page_number < 1 or page_number > len(pdf_document):
        raise ValueError("Page number is out of range.")

    page = pdf_document[page_number - 1]  # page_number is 1-based
    pix = page.get_pixmap()
    pix.save(output_path)
    print(f"Saved page {page_number} as {output_path}")
    return output_path

@dp.callback_query_handler(Text(equals="timetable"))
async def handle_timetable(callback_query: types.CallbackQuery):
    new_buttons = get_next_row_text_with_pages(file_path_dars, "DARS JADVALI")
    await bot.answer_callback_query(callback_query.id)  # Acknowledge the callback query
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for button in new_buttons:
        name = button['name']  # Extract name
        page = button['page']  # Extract page number
        buttons.append(InlineKeyboardButton(name, callback_data=f'page_{page}'))
    for i in range(0, len(buttons), 2):
        keyboard.row(*buttons[i:i+2])
    print(f"Created {len(new_buttons)} buttons.")  # Debugging line
    await bot.send_message(
        callback_query.from_user.id,
        "Guruhingizni tanlang!:",  # You can customize the message here
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('page_'))
async def return_png_timetable(callback_query: types.CallbackQuery):
    page_number = int(callback_query.data.split('_')[1])  # Extract page number from callback_data
    pdf_path = "files/dars.pdf"
    output_path = f"page_{page_number}.png"  # Define output image path
    try:
        image_path = await convert_pdf_page_to_image(pdf_path, page_number, output_path)
        await bot.send_photo(callback_query.from_user.id, types.InputFile(image_path))  # Send image to the user
        await send_welcome(callback_query.message)
    except ValueError as e:
        await bot.send_message(callback_query.from_user.id, str(e))













@dp.callback_query_handler(Text(equals="chaqiruv"))
async def handle_chaqiruv_hemis(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "HEMIS Student axborot tizimi\nTalaba ID sini kiriting:")
    await Form.waiting_for_login.set()


@dp.message_handler(state=Form.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("HEMIS Student axborot tizimi\nParolni kiriting:")
    await Form.waiting_for_password.set()



@dp.message_handler(state=Form.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    login = data.get('login')
    await message.answer("Iltimos biroz kuting...")
    async with aiohttp.ClientSession() as session:
        login_payload = {"login": login, "password": password}
        try:
            async with session.post(
                    'https://student.buxpxti.uz/rest/v1/auth/login', json=login_payload
            ) as resp:
                login_response = await resp.json()
                if login_response.get("success"):
                    token = login_response["data"]["token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(
                            'https://student.buxpxti.uz/rest/v1/account/me', headers=headers
                    ) as profile_resp:
                        profile_json = await profile_resp.json()
                        profile_data = profile_json.get('data', {})
                        print(profile_data)
                        full_name = profile_data.get('full_name', 'N/A')
                        passport_pin = profile_data.get('passport_pin', 'N/A')
                        level_name = profile_data.get('level', {}).get('name', 'N/A')
                        link = profile_data.get('validateUrl', 'N/A')
                        specialty_name = profile_data.get('specialty', {}).get('name', 'N/A')
                        semester_name = profile_data.get('semester', {}).get('name', 'N/A')
                        user_info = f"F.I.O: {full_name}\nKurs: {level_name}"
                        print(user_info, passport_pin, specialty_name, semester_name)
                        data = await search_in_sheet_by_passport_pin(level_name, passport_pin, file_path)

                        if 'kontrakt' not in data or 'tolov' not in data:
                            await message.answer("Sizning ma'lumotlaringiz ma'lumotlar bazasidan topilmadi!")
                            await send_welcome(message)
                        else:
                            kontrakt = int(data['kontrakt'])
                            tolov = int(data['tolov'])

                            if kontrakt * 0.25 > tolov:
                                # Delete old message and send new one
                                await message.answer(
                                    "Siz yetarlicha to'lov qilmaganligingiz sababli "
                                    "chaqiruv qog'ozi ololmaysiz."
                                )
                            else:
                                full_info = f"{user_info}\nKontrakt: {kontrakt}\nTo'lov: {tolov}"

                                # Generate PDF file with QR code and get BytesIO
                                pdf_file = await generate_pdf_with_qr(
                                    link, full_name, level_name, specialty_name, semester_name
                                )

                                pdf_file.seek(0)
                                await bot.send_document(
                                    message.chat.id,
                                    types.InputFile(pdf_file, filename='malumotnoma.pdf')
                                )

                                await message.answer(full_info)
                else:
                    await message.answer("Login yoki parol xato. Iltimos, qayta urinib ko'ring.")
        except Exception as e:
            await message.answer(f"Xatolik yuz berdi: {str(e)}")


    await state.finish()
    await send_welcome(message)

@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Amal bekor qilindi.")




async def send_welcome(message: types.Message):
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
        reply_markup=keyboard, parse_mode=ParseMode.HTML)