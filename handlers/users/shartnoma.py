from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram import types
from handlers.users.main import send_welcome
from loader import dp, bot
import aiohttp
import aiofiles
import os


class Form(StatesGroup):
    waiting_for_login_sh = State()
    waiting_for_password_sh = State()


@dp.callback_query_handler(Text(equals="shartnoma"))
async def handle_malumotnoma(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
                           "Iltimos passport seriya raqamini kiriting (2ta harf, 7ta raqam) \nMasalan <b>AB1234567</b>:")
    await Form.waiting_for_login_sh.set()


@dp.message_handler(state=Form.waiting_for_login_sh)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Iltimos passport JSHR raqamini kiriting (14 ta raqam) \nMasalan <b>1234567891011</b>:")
    await Form.waiting_for_password_sh.set()


@dp.message_handler(state=Form.waiting_for_password_sh)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    await message.answer("Iltimos biroz kuting...")

    data = await state.get_data()
    login = data.get('login')

    api_url = f"https://qabul.buxpxti.uz/api/?jshir={password}&passport={login}"
    headers = {
        "Authorization": "Bearer 6d8f01f8c8f1e8f385415ee0894055f2"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, headers=headers) as response:
                print(response.status)

                if response.status == 200:
                    file_path = "./shartnoma.pdf"

                    # Save the PDF file locally
                    async with aiofiles.open(file_path, "wb") as file:
                        await file.write(await response.read())

                    # Send the PDF file to the user
                    await bot.send_document(message.chat.id, types.InputFile(file_path), caption="Shartnoma fayli")

                    # Delete the file after sending it
                    os.remove(file_path)
                else:
                    # Handle non-200 responses
                    error_text = f"Xatolik yuz berdi: {response.status}. Iltimos, ma'lumotlaringizni tekshiring va qayta urinib ko'ring."
                    await message.answer(error_text)

        except aiohttp.ClientError as e:
            # Handle network errors or other aiohttp exceptions
            await message.answer("Serverga ulanishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
    print(message)
    try:
        await state.finish()
    except Exception as e:
        print(e)
    await send_welcome(message)
