import asyncio
from datetime import datetime, time, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = "8327551613:AAF-JoZY848kXCFUOna2HBeOQlzVMIcR2rc"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# здесь будем хранить задачу напоминания
reminder_task = None


# 🔹 Приветствие
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Установить время напоминания 💊",
        callback_data="set_time"
    )

    await message.answer(
        "Привет! Я бот, который напомнит тебе выпить таблетку 💊\n\n"
        "Нажми кнопку ниже, чтобы установить время напоминания.",
        reply_markup=keyboard.as_markup()
    )


# 🔹 Нажатие на кнопку
@dp.callback_query(F.data == "set_time")
async def ask_time(callback: types.CallbackQuery):
    await callback.message.answer(
        "Введи время в формате HH:MM\n"
        "Например: 08:30 или 19:45"
    )
    await callback.answer()


# 🔹 Ввод времени
@dp.message(F.text.regexp(r"^\d{1,2}:\d{2}$"))
async def save_time(message: types.Message):
    global reminder_task

    user_time = message.text

    # проверка корректности времени
    try:
        hours, minutes = map(int, user_time.split(":"))
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
    except ValueError:
        await message.answer("Некорректное время. Введи в формате HH:MM.")
        return

    # если напоминание уже было — отменяем
    if reminder_task:
        reminder_task.cancel()

    reminder_task = asyncio.create_task(
        reminder(message.chat.id, hours, minutes)
    )

    await message.answer(
        f"Отлично! 😊\n"
        f"Я буду напоминать тебе каждый день в {user_time} 💊"
    )


# 🔹 Функция напоминания
async def reminder(chat_id: int, hour: int, minute: int):
    target_time = time(hour, minute)

    while True:
        now = datetime.now()
        reminder_datetime = datetime.combine(now.date(), target_time)

        if now > reminder_datetime:
            reminder_datetime += timedelta(days=1)

        wait_seconds = (reminder_datetime - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        await bot.send_message(
            chat_id,
            "💊 Напоминание: пора выпить таблетку!",
        )

        await asyncio.sleep(1)


# 🔹 Запуск бота
async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())