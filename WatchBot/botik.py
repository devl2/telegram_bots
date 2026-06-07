import asyncio
import logging
import sys
import os
import re
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

dp = Dispatcher()

phone_pattern = re.compile(r"^\+?\d{10,15}$")

categories = [
    "ремонт часов",
    "замена батарейки",
    "чистка/обслуживание",
    "другое"
]


class OrderForm(StatesGroup):
    ch_category = State()
    ch_name = State()
    contact_type = State()
    ch_phone = State()
    ch_telegram = State()
    ch_message = State()
    result = State()

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    kb = [
        [
            KeyboardButton(text="ремонт часов"),
            KeyboardButton(text="замена батарейки")
        ],
        [KeyboardButton(text="чистка/обслуживание")],
        [KeyboardButton(text="другое")]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.answer(f"Здравствуйте, {html.bold(message.from_user.full_name)}!",reply_markup=keyboard)

    await state.set_state(OrderForm.ch_category)


@dp.message(OrderForm.ch_category, F.text.in_(categories))
async def chosen_category(message: Message, state: FSMContext):
    await state.update_data(ch_category=message.text)

    kb = [
        [KeyboardButton(text=message.from_user.first_name)]
    ]

    keyboard = ReplyKeyboardMarkup(keyboard=kb,resize_keyboard=True)

    await state.set_state(OrderForm.ch_name)

    await message.answer("Как вас зовут?",reply_markup=keyboard)


@dp.message(OrderForm.ch_category)
async def wrong_category(message: Message):
    await message.answer("Выберите категорию с помощью кнопок.")


@dp.message(OrderForm.ch_name)
async def save_name(message: Message, state: FSMContext):
    await state.update_data(ch_name=message.text)

    kb = [
        [
            KeyboardButton(text="Телефон"),
            KeyboardButton(text="Telegram")
        ]
    ]

    keyboard = ReplyKeyboardMarkup(keyboard=kb,resize_keyboard=True)

    await state.set_state(OrderForm.contact_type)

    await message.answer("Как с вами связаться?",reply_markup=keyboard)

@dp.message(OrderForm.contact_type, F.text == "Телефон")
async def choose_phone(message: Message, state: FSMContext):

    kb = [[KeyboardButton(
        text="Отправить номер",
        request_contact=True
    )]]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await state.set_state(OrderForm.ch_phone)

    await message.answer(
        "Укажите номер телефона:",
        reply_markup=keyboard
    )

@dp.message(OrderForm.contact_type, F.text == "Telegram")
async def choose_telegram(message: Message, state: FSMContext):

    await state.set_state(OrderForm.ch_telegram)

    await message.answer(
        "Введите ваш Telegram username.\n\nПример: @ivanov"
    )

@dp.message(OrderForm.ch_telegram)
async def save_telegram(message: Message, state: FSMContext):

    username = message.text.strip()

    if not username.startswith("@"):
        await message.answer("Username должен начинаться с @")
        return

    await state.update_data(contact=username)

    await state.set_state(OrderForm.ch_message)

    await message.answer("Комментарий к заказу:", reply_markup=ReplyKeyboardRemove())

@dp.message(OrderForm.ch_phone, F.contact)
async def phone_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.contact.phone_number)

    await state.set_state(OrderForm.ch_message)

    await message.answer("Комментарий к заказу:",reply_markup=ReplyKeyboardRemove())


@dp.message(OrderForm.ch_phone)
async def phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()

    if not phone_pattern.match(phone):
        await message.answer("Введите корректный номер телефона.\n"
                             "Например: +79991234567")
        return

    await state.update_data(contact=phone)

    await state.set_state(OrderForm.ch_message)

    await message.answer("Комментарий к заказу:",reply_markup=ReplyKeyboardRemove())


@dp.message(OrderForm.ch_message)
async def comment(message: Message, state: FSMContext):
    await state.update_data(ch_message=message.text)

    kb = [
        [
            KeyboardButton(text="да"),
            KeyboardButton(text="нет")
        ]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await state.set_state(OrderForm.result)

    await message.answer(f"Ваш комментарий:\n\n{message.text}\n\nИзменить?", reply_markup=keyboard)


@dp.message(OrderForm.result, F.text.lower() == "да")
async def comment_yes(message: Message, state: FSMContext):
    await state.set_state(OrderForm.ch_message)

    await message.answer("Введите новый комментарий:", reply_markup=ReplyKeyboardRemove())


@dp.message(OrderForm.result, F.text.lower() == "нет")
async def result(message: Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()

    admin_message = (
        "ПОСТУПИЛА НОВАЯ ЗАЯВКА\n\n"
        f"Категория: {user_data['ch_category']}\n"
        f"Имя: {user_data['ch_name']}\n"
        f"Телефон/Telegram: {user_data['contact']}\n"
        f"Комментарий: {user_data['ch_message']}"
    )

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_message
    )

    await message.answer(
        "✅ Ваша заявка принята!\n"
        "Мы свяжемся с вами в ближайшее время.",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.clear()


async def main():
    bot = Bot(token=TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )

    asyncio.run(main())