from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.keyboards import get_main_menu, get_back_keyboard
from bot.database.database import UserDatabase

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()

    user = message.from_user
    await UserDatabase.add_user(
        user_id=user.id, username=user.username, first_name=user.first_name
    )

    welcome_text = f"""
🎉 <b>Добро пожаловать в AutoCorrect Bot!</b>

Привет, <i>{user.first_name}</i>! 👋

Этот бот поможет тебе:
• <b>Исправлять ошибки</b> в твоих сообщениях
• <b>Настраивать режимы работы</b> под твои нужды
• <b>Повышать качество</b> твоих текстов

🔒 <b>Мы не храним ваши переписки</b>, а все сессии сохраняются только в зашифрованном виде.

<code>Нажми на кнопку ниже, чтобы начать 👇</code>
"""

    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    help_text = """
<blockquote expandable>
📖 <b>Справка по боту</b>

<b>🔧 Основные функции:</b>
• <b>Коррекция</b> - исправление орфографических и грамматических ошибок
• <b>Автоматическая обработка</b> - умный анализ и улучшение текста

<b>⚙️ Настройки:</b>
• <i>Минимальная длина сообщения</i> для обработки
• <i>Включение/выключение режимов</i>
• <i>Управление user-ботом</i>

<b>🤖 User-бот:</b>
Для работы нужно подключить твой собственный аккаунт Telegram как бота. 
<u>Это безопасно</u> - мы используем официальный API Telegram.

<b>🔒 Безопасность:</b>
• Мы не храним ваши сообщения
• Можете отключить бота в любой момент
• Используется официальный API Telegram

<b>💡 Команды:</b>
<code>/start</code> - Главное меню
<code>/help</code> - Эта справка
<code>/settings</code> - Быстрые настройки
</blockquote>
"""

    await message.answer(help_text, reply_markup=get_back_keyboard(), parse_mode="HTML")


@router.message(Command("settings"))
async def quick_settings_handler(message: Message):
    """Быстрый доступ к настройкам"""
    from bot.handlers.settings import show_settings_menu

    await show_settings_menu(message)


@router.callback_query(F.data == "help")
async def help_callback_handler(callback: CallbackQuery):
    """Обработчик кнопки помощи"""
    help_text = """
📖 <b>Справка по боту</b>

<b>🔧 Основные функции:</b>
• <b>Коррекция</b> - исправление орфографических и грамматических ошибок
• <b>Автоматическая обработка</b> - умный анализ и улучшение текста

<b>⚙️ Настройки:</b>
• <i>Минимальная длина сообщения</i> для обработки
• <i>Включение/выключение режимов</i>
• <i>Управление user-ботом</i>

<b>🤖 User-бот:</b>
Для работы нужно подключить твой собственный аккаунт Telegram как бота. 
<u>Это безопасно</u> - мы используем официальный API Telegram.

<b>🔒 Безопасность:</b>
• Мы не храним ваши сообщения
• Можете отключить бота в любой момент
• Используется официальный API Telegram

<b>💡 Команды:</b>
<code>/start</code> - Главное меню
<code>/help</code> - Эта справка
<code>/settings</code> - Быстрые настройки
"""

    await callback.message.edit_text(
        help_text, reply_markup=get_back_keyboard(), parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    welcome_text = """
🏠 <b>Главное меню</b>

<i>Выберите действие:</i>
"""

    await callback.message.edit_text(
        welcome_text, reply_markup=get_main_menu(), parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Действие отменено</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )
