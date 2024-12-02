import aiohttp
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from handlers.users.main import send_welcome
from loader import dp, db, bot
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext


class Form(StatesGroup):
    waiting_for_login2 = State()
    waiting_for_password2 = State()


@dp.callback_query_handler(Text(equals="qarz"))
async def handle_chaqiruv_hemis(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "HEMIS Student axborot tizimi\nTalaba ID sini kiriting:")
    await Form.waiting_for_login2.set()


@dp.message_handler(state=Form.waiting_for_login2)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("HEMIS Student axborot tizimi\nParolni kiriting:")
    await Form.waiting_for_password2.set()


@dp.message_handler(state=Form.waiting_for_password2)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
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

                    # Fetching student profile data
                    async with session.get(
                            'https://student.buxpxti.uz/rest/v1/account/me', headers=headers
                    ) as profile_resp:
                        profile_json1 = await profile_resp.json()
                        profile_data1 = profile_json1.get('data', {})
                        print(profile_data1)

                        # Extract the current semester code
                        current_semester_code = profile_data1['semester']['code']
                        print(current_semester_code)  # For debugging purposes

                    # Fetching subject list
                    async with session.get(
                            'https://student.buxpxti.uz/rest/v1/education/subject-list', headers=headers
                    ) as profile_resp:
                        profile_json = await profile_resp.json()
                        profile_data = profile_json.get('data', {})
                        filtered_subjects = [
                            {
                                "subject_name": subject['curriculumSubject']['subject']['name'],
                                "_semester": subject['_semester'],
                                "grade": subject['overallScore']['grade'],
                                "credit": subject['curriculumSubject']['credit']
                            }
                            for subject in profile_data
                            if subject['overallScore']['grade'] < 59 and subject['_semester'] != current_semester_code
                        ]

                        message_text = ""
                        if len(filtered_subjects) == 0:
                            message_text = "Sizni fanlardan qarzingiz yo'q."
                        else:
                            total_credits = sum(subject['credit'] for subject in filtered_subjects)
                            for i, filtered_subject in enumerate(filtered_subjects, start=1):
                                message_text += (
                                    f"<b>🏷{i}</b>\n"
                                    f"<b>📘 Fan:</b> {filtered_subject['subject_name']}\n"
                                     f"<b>📎 Semester:</b> {int(filtered_subject['_semester']) - 10}-semester\n"
                                    f"<b>📋 Jamlangan bal:</b> 100/{filtered_subject['grade']}\n"
                                    f"<b>📊 Kredit miqdori:</b> {filtered_subject['credit']}\n"
                                    f"--------------------------\n\n"
                                )
                            message_text += (
                                f"Sizning umumiy {len(filtered_subjects)} fandan qarzingiz bor.\n"
                                f"Umumiy kredit miqdori: {total_credits}"
                            )
                    await message.answer(message_text, parse_mode="HTML")
                else:
                    await message.answer("Login yoki parol xato. Iltimos, qayta urinib ko'ring.")
        except Exception as e:
            await message.answer(f"Xatolik yuz berdi: {str(e)}")

    await state.finish()
    await send_welcome(message)
