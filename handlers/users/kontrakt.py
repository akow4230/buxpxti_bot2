from select import select

from loader import dp
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import types
from handlers.users.main import send_welcome
from loader import bot

from handlers.users.app import search_in_sheet_by_passport_pin_payment
file_path = 'files/bot.xlsx'

# Define a new state group
class Form(StatesGroup):
    waiting_for_course_selection = State()  # State for course selection
    waiting_for_jshr = State()  # State for JSHR input


# Inline keyboard for course selection
def get_course_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    courses = ["1-kurs", "2-kurs", "3-kurs", "4-kurs"]
    buttons = [InlineKeyboardButton(text=course, callback_data=course) for course in courses]
    keyboard.add(*buttons)
    return keyboard


@dp.callback_query_handler(Text(equals="kontrakt"))
async def handle_kontrakt(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, "Kursingizni tanlang:", reply_markup=get_course_keyboard())
    await Form.waiting_for_course_selection.set()  # Set the state to wait for course selection


@dp.callback_query_handler(state=Form.waiting_for_course_selection)
async def process_course_selection(callback_query: CallbackQuery, state: FSMContext):
    selected_course = callback_query.data
    await state.update_data(selected_course=selected_course)  # Store the selected course in FSM context

    await bot.send_message(callback_query.from_user.id, "Pasport JSHR'ingizni kiriting:")
    await Form.waiting_for_jshr.set()  # Set the next state to wait for JSHR input


@dp.message_handler(state=Form.waiting_for_jshr)
async def process_jshr(message: types.Message, state: FSMContext):
    await message.answer("Iltimos biroz kuting!")
    jshr = message.text
    data = await state.get_data()
    selected_course = data.get('selected_course')
    data = await search_in_sheet_by_passport_pin_payment(selected_course, jshr, file_path)
    if data:
        message_text=f"<b>F.I.Sh: </b>{data['F.I.Sh']}\n<b>Kontrakt miqdori: </b>{data['kontrakt']}\n<b>To'landi: </b>{data['tolov']}\n<b> Qarzi:</b> {data['qarzi']}\n <b>Ortiqcha to'lov: </b>{data['ortiqcha']}"
        await message.answer(message_text)
    else:
        await message.answer("JSHR xato yoki bazadan topilmadi. \n Iltiomos qayta urinib ko'ring!")
    await state.finish()  # Finish the state after processing
    await send_welcome(message)  # Redirect to the welcome message or any further steps
