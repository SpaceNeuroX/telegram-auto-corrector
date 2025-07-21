from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.keyboards import (
    get_settings_menu,
    get_userbot_menu,
    get_correction_settings_menu,
    get_main_menu,
    get_cancel_keyboard,
)
from bot.database.database import UserSettingsDatabase, UserBotDatabase
from bot.handlers.user_management import userbot_service

router = Router()


class SettingsStates(StatesGroup):
    waiting_for_min_length = State()


@router.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    """Главное меню настроек"""
    await show_settings_menu(callback.message, is_callback=True)


async def show_settings_menu(message_or_callback, is_callback=False):
    """Показать меню настроек"""
    settings_text = """
⚙️ <b>Настройки бота</b>

Здесь вы можете настроить:
• <i>Параметры обработки сообщений</i>
• <i>Управление user-ботом</i>
"""

    if is_callback:
        await message_or_callback.edit_text(
            settings_text, reply_markup=get_settings_menu(), parse_mode="HTML"
        )
    else:
        await message_or_callback.answer(
            settings_text, reply_markup=get_settings_menu(), parse_mode="HTML"
        )


@router.callback_query(F.data == "correction_settings")
async def correction_settings_handler(callback: CallbackQuery):
    """Настройки параметров коррекции"""
    user_id = callback.from_user.id

    settings = await UserSettingsDatabase.get_settings(user_id)
    min_length = settings.get("min_message_length", 10)

    settings_text = f"""
📝 <b>Параметры коррекции</b>

<b>Минимальная длина сообщения:</b> <code>{min_length}</code> символов
<i>Сообщения короче этой длины не будут обрабатываться</i>

💡 <u>Рекомендуется:</u> 10-20 символов
"""

    await callback.message.edit_text(
        settings_text, reply_markup=get_correction_settings_menu(), parse_mode="HTML"
    )


@router.callback_query(F.data == "set_min_length")
async def set_min_length_handler(callback: CallbackQuery, state: FSMContext):
    """Установка минимальной длины сообщения"""
    await callback.message.edit_text(
        "📏 <b>Минимальная длина сообщения</b>\n\n"
        "Введите минимальную длину сообщения в символах <i>(от 5 до 100)</i>:\n\n"
        "Пример: <code>15</code>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )

    await state.set_state(SettingsStates.waiting_for_min_length)


@router.message(SettingsStates.waiting_for_min_length, F.text.regexp(r"^\d+$"))
async def min_length_received_handler(message: Message, state: FSMContext):
    """Обработка новой минимальной длины"""
    length = int(message.text)
    user_id = message.from_user.id

    if length < 5 or length > 100:
        await message.answer(
            "❌ <b>Ошибка!</b>\n\n"
            "Длина должна быть от <code>5</code> до <code>100</code> символов.\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    success = await UserSettingsDatabase.update_setting(
        user_id, "min_message_length", length
    )

    if success:
        await message.answer(
            f"✅ <b>Готово!</b>\n\n"
            f"Минимальная длина установлена: <code>{length}</code> символов",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "❌ <b>Ошибка сохранения настройки</b>",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )

    await state.clear()


@router.message(SettingsStates.waiting_for_min_length)
async def invalid_min_length_handler(message: Message):
    """Обработка неверного формата длины"""
    await message.answer(
        "<blockquote>❌ <b>Неверный формат!</b>\n\n"
        "Введите число от <code>5</code> до <code>100</code></blockquote>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "userbot_settings")
async def userbot_settings_handler(callback: CallbackQuery):
    """Настройки управления user-ботом"""
    user_id = callback.from_user.id

    bot_data = await UserBotDatabase.get_user_bot(user_id)
    is_connected = bot_data is not None
    is_active = userbot_service.is_bot_active(user_id) if is_connected else False

    if is_connected:
        phone = bot_data["phone_number"]
        status = "🟢 Активен" if is_active else "🔴 Остановлен"

        settings_text = f"""
<blockquote expandable>
🤖 <b>Управление user-ботом</b>

<b>Статус:</b> {status}
<b>Номер телефона:</b> <code>{phone}</code>
<b>Дата подключения:</b> <i>{bot_data['created_at'].split(' ')[0]}</i>

<u>Выберите действие:</u>
</blockquote>
"""
    else:
        settings_text = """
<blockquote expandable>
🤖 <b>Управление user-ботом</b>

<b>Статус:</b> 🔴 Не подключен

Для работы автокоррекции необходимо подключить user-бота.
<i>Это ваш собственный аккаунт Telegram</i>, который будет автоматически 
исправлять ваши сообщения.
</blockquote>
"""

    await callback.message.edit_text(
        settings_text,
        reply_markup=get_userbot_menu(is_connected, is_active),
        parse_mode="HTML",
    )
