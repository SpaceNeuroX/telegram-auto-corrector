from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Contact
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telethon import TelegramClient
import re

from bot.keyboards.keyboards import (
    get_phone_request_keyboard,
    get_cancel_keyboard,
    get_main_menu,
    get_userbot_menu,
    get_confirmation_keyboard,
    get_code_input_keyboard,
    get_code_display_text,
)
from bot.database.database import UserBotDatabase, UserDatabase
from bot.services.userbot_service import UserBotService

router = Router()


class UserBotConnection(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()


temp_clients = {}
userbot_service = UserBotService()


@router.callback_query(F.data == "connect_userbot")
async def connect_userbot_handler(callback: CallbackQuery, state: FSMContext):
    """Начало процесса подключения user-бота"""
    user_id = callback.from_user.id

    existing_bot = await UserBotDatabase.get_user_bot(user_id)
    if existing_bot:
        await callback.message.edit_text(
            "⚠️ <b>Внимание!</b>\n\n"
            "У вас уже есть подключенный user-бот!\n\n"
            "Если хотите подключить новый, сначала отключите текущий в настройках.",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        "📱 <b>Подключение user-бота</b>\n\n"
        "Для работы бота нужно подключить ваш аккаунт Telegram.\n\n"
        "<b>🔒 Это безопасно:</b>\n"
        "• <i>Используется официальный API Telegram</i>\n"
        "• <i>Данные хранятся только у вас</i>\n"
        "• <i>Можете отключить в любой момент</i>\n\n"
        "<u>Отправьте свой номер телефона кнопкой ниже:</u>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )

    await callback.message.answer(
        "📱 Нажмите кнопку ниже, чтобы отправить номер телефона:",
        reply_markup=get_phone_request_keyboard(),
        parse_mode="HTML",
    )

    await state.set_state(UserBotConnection.waiting_for_phone)


@router.message(UserBotConnection.waiting_for_phone, F.contact)
async def phone_received_handler(message: Message, state: FSMContext):
    """Обработка полученного номера телефона"""
    phone_number = message.contact.phone_number
    user_id = message.from_user.id

    await message.answer("⏳ Отправляем код подтверждения...", reply_markup=None)

    result = await userbot_service.create_session(phone_number)

    if result["success"]:

        temp_clients[user_id] = {
            "client": result["client"],
            "phone_number": phone_number,
        }

        await message.answer(
            f"📲 <b>Код отправлен!</b>\n\n"
            f"Код подтверждения отправлен на номер:\n"
            f"<code>{phone_number}</code>\n\n"
            f"⚠️ <b>Важно:</b> Используйте кнопки ниже для ввода кода.\n"
            f"Не отправляйте код как обычное сообщение!\n\n"
            f"{get_code_display_text('')}",
            reply_markup=get_code_input_keyboard(),
        )

        await state.update_data(current_code="")
        await state.set_state(UserBotConnection.waiting_for_code)
    else:
        await message.answer(
            f"❌ <b>Ошибка:</b> {result['message']}\n\n"
            "Попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=get_main_menu(),
        )
        await state.clear()


@router.message(UserBotConnection.waiting_for_phone, F.text == "❌ Отмена")
async def cancel_phone_handler(message: Message, state: FSMContext):
    """Отмена ввода номера телефона"""
    await state.clear()
    await message.answer("❌ Подключение отменено", reply_markup=get_main_menu())


@router.message(UserBotConnection.waiting_for_phone)
async def invalid_phone_handler(message: Message):
    """Обработка неверного формата номера"""
    await message.answer(
        "❌ Пожалуйста, используйте кнопку для отправки номера телефона",
        reply_markup=get_phone_request_keyboard(),
    )


@router.callback_query(F.data.startswith("code_digit_"))
async def code_digit_handler(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на цифру"""
    data = await state.get_data()
    current_code = data.get("current_code", "")

    if len(current_code) >= 5:
        await callback.answer("Код уже состоит из 5 цифр!", show_alert=True)
        return

    digit = callback.data.split("_")[-1]
    new_code = current_code + digit

    await state.update_data(current_code=new_code)

    await callback.message.edit_text(
        f"📲 <b>Код отправлен!</b>\n\n"
        f"Код подтверждения отправлен на номер.\n\n"
        f"⚠️ <b>Важно:</b> Используйте кнопки ниже для ввода кода.\n"
        f"Не отправляйте код как обычное сообщение!\n\n"
        f"{get_code_display_text(new_code)}",
        reply_markup=get_code_input_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "code_backspace")
async def code_backspace_handler(callback: CallbackQuery, state: FSMContext):
    """Обработка удаления последней цифры"""
    data = await state.get_data()
    current_code = data.get("current_code", "")

    if len(current_code) == 0:
        await callback.answer("Код уже пустой!", show_alert=True)
        return

    new_code = current_code[:-1]
    await state.update_data(current_code=new_code)

    await callback.message.edit_text(
        f"📲 <b>Код отправлен!</b>\n\n"
        f"Код подтверждения отправлен на номер.\n\n"
        f"⚠️ <b>Важно:</b> Используйте кнопки ниже для ввода кода.\n"
        f"Не отправляйте код как обычное сообщение!\n\n"
        f"{get_code_display_text(new_code)}",
        reply_markup=get_code_input_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "code_submit")
async def code_submit_handler(callback: CallbackQuery, state: FSMContext):
    """Обработка отправки кода"""
    data = await state.get_data()
    current_code = data.get("current_code", "")
    user_id = callback.from_user.id

    if len(current_code) != 5:
        await callback.answer("Код должен состоять из 5 цифр!", show_alert=True)
        return

    if user_id not in temp_clients:
        await callback.message.edit_text(
            "❌ Сессия истекла. Начните подключение заново.",
            reply_markup=get_main_menu(),
        )
        await state.clear()
        return

    client_data = temp_clients[user_id]
    client = client_data["client"]
    phone_number = client_data["phone_number"]

    await callback.message.edit_text(
        "⏳ <b>Проверяем код...</b>", parse_mode="HTML"
    )

    result = await userbot_service.verify_code(client, phone_number, current_code)

    if result["success"]:

        session_string = result["session_string"]
        success = await UserBotDatabase.add_user_bot(
            user_id, phone_number, session_string
        )

        if success:
            await callback.message.edit_text(
                "✅ <b>User-бот успешно подключен!</b>\n\n"
                "Теперь вы можете:\n"
                "• <i>Настроить режимы работы</i>\n"
                "• <i>Запустить автокоррекцию</i>\n"
                "• <i>Изменить параметры обработки</i>\n\n"
                "<u>Перейдите в настройки для управления ботом.</u>",
                reply_markup=get_main_menu(),
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка сохранения данных.</b>\n\nПопробуйте еще раз.",
                reply_markup=get_main_menu(),
                parse_mode="HTML",
            )

        if user_id in temp_clients:
            await temp_clients[user_id]["client"].disconnect()
            del temp_clients[user_id]

        await state.clear()

    elif result.get("needs_password"):
        await callback.message.edit_text(
            "🔐 <b>Требуется 2FA пароль</b>\n\n"
            "Введите пароль двухфакторной аутентификации:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        await state.set_state(UserBotConnection.waiting_for_password)
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка:</b> {result['message']}\n\n"
            "Попробуйте еще раз или начните подключение заново.\n\n"
            f"{get_code_display_text('')}",
            reply_markup=get_code_input_keyboard(),
        )

        await state.update_data(current_code="")


@router.message(UserBotConnection.waiting_for_code)
async def invalid_code_text_handler(message: Message):
    """Предупреждение о неправильном способе ввода кода"""
    await message.answer(
        "⚠️ <b>Внимание!</b>\n\n"
        "Не отправляйте код как обычное сообщение!\n"
        "Telegram может автоматически отозвать код.\n\n"
        "Используйте кнопки выше для ввода кода.",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(UserBotConnection.waiting_for_password)
async def password_received_handler(message: Message, state: FSMContext):
    """Обработка 2FA пароля"""
    password = message.text
    user_id = message.from_user.id

    if user_id not in temp_clients:
        await message.answer(
            "❌ Сессия истекла. Начните подключение заново.",
            reply_markup=get_main_menu(),
        )
        await state.clear()
        return

    client_data = temp_clients[user_id]
    client = client_data["client"]
    phone_number = client_data["phone_number"]

    await message.answer("⏳ Проверяем пароль...")

    result = await userbot_service.verify_password(client, password)

    if result["success"]:

        session_string = result["session_string"]
        success = await UserBotDatabase.add_user_bot(
            user_id, phone_number, session_string
        )

        if success:
            await message.answer(
                "✅ <b>User-бот успешно подключен!</b>\n\n"
                "Теперь вы можете:\n"
                "• Настроить режимы работы\n"
                "• Запустить автокоррекцию\n"
                "• Изменить параметры обработки\n\n"
                "Перейдите в настройки для управления ботом.",
                reply_markup=get_main_menu(),
            )
        else:
            await message.answer(
                "❌ Ошибка сохранения данных. Попробуйте еще раз.",
                reply_markup=get_main_menu(),
            )

        if user_id in temp_clients:
            await temp_clients[user_id]["client"].disconnect()
            del temp_clients[user_id]

        await state.clear()
    else:
        await message.answer(
            f"❌ <b>Ошибка:</b> {result['message']}\n\n" "Попробуйте еще раз.",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "start_userbot")
async def start_userbot_handler(callback: CallbackQuery):
    """Запуск user-бота"""
    user_id = callback.from_user.id

    bot_data = await UserBotDatabase.get_user_bot(user_id)
    if not bot_data:
        await callback.message.edit_text(
            "❌ <b>User-бот не найден.</b>\n\nПодключите его сначала.",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        "⏳ <b>Запускаем user-бота...</b>", parse_mode="HTML"
    )

    success = await userbot_service.start_user_bot(user_id, bot_data["session_string"])

    if success:
        await callback.message.edit_text(
            "✅ <b>User-бот запущен!</b>\n\n"
            "Теперь ваши сообщения будут автоматически обрабатываться согласно настройкам.\n\n"
            "<u>Вы можете изменить режимы работы в настройках.</u>",
            reply_markup=get_userbot_menu(True, True),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Ошибка запуска user-бота.</b>\n\n"
            "<b>Возможные причины:</b>\n"
            "• <i>Проблемы с сетью</i>\n"
            "• <i>Истекшая сессия</i>\n"
            "• <i>Блокировка аккаунта</i>\n\n"
            "<u>Попробуйте позже или переподключите бота.</u>",
            reply_markup=get_userbot_menu(True, False),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "stop_userbot")
async def stop_userbot_handler(callback: CallbackQuery):
    """Остановка user-бота"""
    user_id = callback.from_user.id

    await callback.message.edit_text("⏳ Останавливаем user-бота...")

    success = await userbot_service.stop_user_bot(user_id)

    if success:
        await callback.message.edit_text(
            "⏸️ <b>User-бот остановлен</b>\n\n"
            "Автокоррекция временно отключена.\n"
            "Вы можете запустить бота снова в любое время.",
            reply_markup=get_userbot_menu(True, False),
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка остановки user-бота", reply_markup=get_userbot_menu(True, True)
        )


@router.callback_query(F.data == "disconnect_userbot")
async def disconnect_userbot_handler(callback: CallbackQuery):
    """Отключение user-бота"""
    user_id = callback.from_user.id

    await callback.message.edit_text(
        "⚠️ <b>Отключение user-бота</b>\n\n"
        "Вы уверены, что хотите полностью отключить user-бота?\n\n"
        "После отключения вам потребуется заново пройти процедуру подключения.",
        reply_markup=get_confirmation_keyboard("disconnect"),
    )


@router.callback_query(F.data == "confirm_disconnect")
async def confirm_disconnect_handler(callback: CallbackQuery):
    """Подтверждение отключения user-бота"""
    user_id = callback.from_user.id

    await userbot_service.stop_user_bot(user_id)

    success = await UserBotDatabase.deactivate_user_bot(user_id)

    if success:
        await callback.message.edit_text(
            "✅ <b>User-бот отключен</b>\n\n"
            "Все данные удалены. Вы можете подключить нового бота в любое время.",
            reply_markup=get_main_menu(),
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка отключения user-бота", reply_markup=get_userbot_menu(True, False)
        )
