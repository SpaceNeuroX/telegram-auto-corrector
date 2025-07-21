from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="👤 Подключить user-бота", callback_data="connect_userbot"
        )
    )
    builder.row(InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))
    builder.row(InlineKeyboardButton(text="❓ Помощь", callback_data="help"))

    return builder.as_markup()


def get_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=" Параметры коррекции", callback_data="correction_settings"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🤖 Управление user-ботом", callback_data="userbot_settings"
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))

    return builder.as_markup()


def get_userbot_menu(
    is_connected: bool, is_active: bool = False
) -> InlineKeyboardMarkup:
    """Меню управления user-ботом"""
    builder = InlineKeyboardBuilder()

    if not is_connected:
        builder.row(
            InlineKeyboardButton(
                text="🔗 Подключить user-бота", callback_data="connect_userbot"
            )
        )
    else:
        if is_active:
            builder.row(
                InlineKeyboardButton(text="⏸️ Остановить", callback_data="stop_userbot")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="▶️ Запустить", callback_data="start_userbot")
            )

        builder.row(
            InlineKeyboardButton(text="🗑️ Отключить", callback_data="disconnect_userbot")
        )

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="settings"))

    return builder.as_markup()


def get_correction_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек коррекции"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📏 Мин. длина сообщения", callback_data="set_min_length"
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="settings"))

    return builder.as_markup()


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel"),
    )

    return builder.as_markup()


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса номера телефона"""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)
    )
    builder.row(KeyboardButton(text="❌ Отмена"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура "Назад" """
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))

    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены"""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))

    return builder.as_markup()


def get_code_input_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ввода кода подтверждения"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="1", callback_data="code_digit_1"),
        InlineKeyboardButton(text="2", callback_data="code_digit_2"),
        InlineKeyboardButton(text="3", callback_data="code_digit_3"),
    )

    builder.row(
        InlineKeyboardButton(text="4", callback_data="code_digit_4"),
        InlineKeyboardButton(text="5", callback_data="code_digit_5"),
        InlineKeyboardButton(text="6", callback_data="code_digit_6"),
    )

    builder.row(
        InlineKeyboardButton(text="7", callback_data="code_digit_7"),
        InlineKeyboardButton(text="8", callback_data="code_digit_8"),
        InlineKeyboardButton(text="9", callback_data="code_digit_9"),
    )

    builder.row(
        InlineKeyboardButton(text="⬅️ Удалить", callback_data="code_backspace"),
        InlineKeyboardButton(text="0", callback_data="code_digit_0"),
        InlineKeyboardButton(text="✅ Готово", callback_data="code_submit"),
    )

    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))

    return builder.as_markup()


def get_code_display_text(current_code: str) -> str:
    """Генерирует текст для отображения введенного кода"""
    code_display = ""
    for i in range(5):
        if i < len(current_code):
            code_display += f"[{current_code[i]}] "
        else:
            code_display += "[_] "

    return f"🔢 <b>Введите код подтверждения:</b>\n\n{code_display}\n\nИспользуйте кнопки ниже для ввода кода:"
