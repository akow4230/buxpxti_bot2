from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import  types
from handlers.users.main import send_welcome
from loader import dp, bot
import aiohttp


import aiofiles  # to handle async file operations
import os




class Form(StatesGroup):
    waiting_for_login1 = State()
    waiting_for_password1 = State()
    waiting_for_course_selection1 = State()
    waiting_for_name_input1 = State()
    waiting_for_excel_file1 = State()  # New state for Excel file upload


@dp.callback_query_handler(Text(equals="malumotnoma"))
async def handle_malumotnoma(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "HEMIS Student axborot tizimi\nTalaba ID sini kiriting:")
    await Form.waiting_for_login1.set()


@dp.message_handler(state=Form.waiting_for_login1)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("HEMIS Student axborot tizimi\nParolni kiriting:")
    await Form.waiting_for_password1.set()





@dp.message_handler(state=Form.waiting_for_password1)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    await message.answer("Iltimos biroz kuting...")
    data = await state.get_data()
    login = data.get('login')

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
                            'https://student.buxpxti.uz/rest/v1/student/reference', headers=headers
                    ) as profile_resp:
                        profile_json = await profile_resp.json()
                        profile_data = profile_json.get('data', [])

                        if profile_data:
                            # Extract required data
                            file_url = profile_data[0]['file']  # Assuming you need the latest file
                            async with session.get(file_url, headers=headers) as file_resp:
                                file_name = f"{login}_reference.pdf"

                                # Download and save the file temporarily
                                async with aiofiles.open(file_name, 'wb') as f:
                                    await f.write(await file_resp.read())

                                # Send the file to the user
                                await bot.send_document(
                                    chat_id=message.from_user.id,
                                    document=types.InputFile(file_name)
                                )

                                # Delete the file from the server after sending
                                os.remove(file_name)

                        else:
                            await message.answer("Ma'lumot topilmadi.")

                else:
                    await message.answer("Login yoki parol xato. Iltimos, qayta urinib ko'ring.")

        except Exception as e:
            await message.answer(f"Xatolik yuz berdi: {str(e)}")

    await state.finish()
    await send_welcome(message)
