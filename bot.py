import asyncio
import sqlite3
from datetime import datetime, time, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = "8327551613:AAF-JoZY848kXCFUOna2HBeOQlzVMIcR2rc"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
# подключение к базе
conn = sqlite3.connect("reminders.db", check_same_thread=False)


with conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        user_id INTEGER PRIMARY KEY,
        hour INTEGER,
        minute INTEGER
    )
    """)


# здесь будем хранить задачу напоминания
reminder_tasks = {}


# 🔹 Приветствие
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Установить время напоминания 💊", callback_data="set_time")
    keyboard.button(text="Отключить напоминания 🛑", callback_data="stop_reminder")
    keyboard.adjust(1)

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

    user_time = message.text
    user_id = message.from_user.id

    try:
        hours, minutes = map(int, user_time.split(":"))
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
    except ValueError:
        await message.answer("Некорректное время. Введи в формате HH:MM.")
        return

    # сохраняем время в базу
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO reminders (user_id, hour, minute) VALUES (?, ?, ?)",
            (user_id, hours, minutes)
        )
    # если у пользователя уже есть задача — отменяем
    if user_id in reminder_tasks:
        reminder_tasks[user_id].cancel()

    reminder_tasks[user_id] = asyncio.create_task(
        reminder(user_id, message.chat.id, hours, minutes)
    )

    await message.answer(
        f"Отлично! 😊\n"
        f"Я буду напоминать тебе каждый день в {user_time} 💊"
    )


# 🔹 Функция напоминания
async def reminder(user_id: int, chat_id: int, hour: int, minute: int):

    target_time = time(hour, minute)

    try:
        while True:
            now = datetime.now()
            reminder_datetime = datetime.combine(now.date(), target_time)

            if now > reminder_datetime:
                reminder_datetime += timedelta(days=1)

            wait_seconds = (reminder_datetime - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            await bot.send_message(chat_id, "💊 Напоминание: пора выпить таблетку!")

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        return



async def stop_reminder_for_user(message_or_callback_message: types.Message):

    user_id = message_or_callback_message.from_user.id

    # удаляем время из базы
    with conn:
        conn.execute("DELETE FROM reminders WHERE user_id=?", (user_id,))

    # останавливаем задачу напоминания
    if user_id in reminder_tasks:
        reminder_tasks[user_id].cancel()
        del reminder_tasks[user_id]

    await message_or_callback_message.answer("Ок ✅ Напоминания отключены.")

@dp.callback_query(F.data == "stop_reminder")
async def stop_from_button(callback: types.CallbackQuery):
    await stop_reminder_for_user(callback.message)
    await callback.answer()


@dp.message(Command("stop"))
async def stop_from_command(message: types.Message):
    await stop_reminder_for_user(message)


# 🔹 Загрузка напоминаний из базы при запуске бота
async def load_reminders():
    rows = conn.execute("SELECT user_id, hour, minute FROM reminders").fetchall()

    for user_id, hour, minute in rows:
        reminder_tasks[user_id] = asyncio.create_task(
            reminder(user_id, user_id, hour, minute)
        )


# 🔹 Запуск бота
async def main():
    print("Бот запущен")

    await load_reminders()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
