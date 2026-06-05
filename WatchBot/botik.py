import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram.types import KeyboardButton
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

category = ["ремонт часов", "замена батарейки", "чистка/обслуживание", "другое"]

class OrderForm(StatesGroup):
    ch_category = State()
    ch_name = State()
    ch_phone = State()
    ch_message = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    kb = [
            [
                KeyboardButton(text = "ремонт часов"),
                KeyboardButton(text = "замена батарейки")
            ],
            [KeyboardButton(text = "чистка/обслуживание")],
            [KeyboardButton(text = "другое")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard = kb, resize_keyboard=True)
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=keyboard)
    await state.set_state(OrderForm.ch_category)

@dp.message(OrderForm.ch_category, F.text.in_(category))
async def chosen_category(message: Message, state: FSMContext) -> None:
    await state.update_data(ch_category=message.text.lower())
    kb = [
        [KeyboardButton(text = message.from_user.first_name)]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard = kb, resize_keyboard=True)
    await state.set_state(OrderForm.ch_name)
    await message.answer("Как вас зовут?", reply_markup=keyboard)

@dp.message(OrderForm.ch_name)
async def saveName(message: Message, state: FSMContext) -> None:
    await state.update_data(ch_name=message.text.lower())
    await state.set_state(OrderForm.ch_phone)
    await message.answer("Ваш номер телефона")

@dp.message(OrderForm.ch_phone)
async def phone(message: Message, state: FSMContext) -> None:
    await state.update_data(ch_phone=message.text.lower())
    await state.set_state(OrderForm.ch_message)
    await message.answer("Комментарий к заказу")

@dp.message(OrderForm.ch_message)
async def comment(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    await message.answer("Ваше обращение:\n" 
                         "Причина обращения: ", f"{user_data['ch_category']}\n", 
                         "Ваше имя: ", f"{user_data['ch_name']}",
                         "Номер телефона: ", f"{user_data['ch_phone']}",
                         "Комментарий: ", message.text.lower())

@dp.message()
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())