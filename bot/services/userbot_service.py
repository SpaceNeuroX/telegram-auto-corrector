import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
)
from typing import Optional, Dict, Any
import re
from dotenv import load_dotenv


load_dotenv()

from bot.services.ai_service import AIService
from bot.database.database import UserSettingsDatabase

logger = logging.getLogger(__name__)


class UserBotService:
    """Сервис для управления user-ботами"""

    def __init__(self):
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.active_bots: Dict[int, TelegramClient] = {}
        self.ai_service = AIService()

    async def create_session(self, phone_number: str) -> Dict[str, Any]:
        """Создание новой сессии user-бота"""
        try:

            client = TelegramClient(StringSession(), self.api_id, self.api_hash)

            await client.connect()

            await client.send_code_request(phone_number)

            return {
                "success": True,
                "client": client,
                "phone_number": phone_number,
                "message": "Код отправлен на указанный номер",
            }

        except PhoneNumberInvalidError:
            return {"success": False, "message": "Неверный номер телефона"}
        except FloodWaitError as e:
            return {
                "success": False,
                "message": f"Слишком много попыток. Попробуйте через {e.seconds} секунд",
            }
        except Exception as e:
            logger.error(f"Ошибка создания сессии: {e}")
            return {"success": False, "message": f"Ошибка: {str(e)}"}

    async def verify_code(
        self, client: TelegramClient, phone_number: str, code: str
    ) -> Dict[str, Any]:
        """Проверка кода подтверждения"""
        try:
            await client.sign_in(phone_number, code)

            session_string = client.session.save()

            return {
                "success": True,
                "session_string": session_string,
                "message": "Авторизация успешна",
            }

        except PhoneCodeInvalidError:
            return {"success": False, "message": "Неверный код подтверждения"}
        except SessionPasswordNeededError:
            return {
                "success": False,
                "message": "Требуется 2FA пароль",
                "needs_password": True,
            }
        except Exception as e:
            logger.error(f"Ошибка проверки кода: {e}")
            return {"success": False, "message": f"Ошибка: {str(e)}"}

    async def verify_password(
        self, client: TelegramClient, password: str
    ) -> Dict[str, Any]:
        """Проверка 2FA пароля"""
        try:
            await client.sign_in(password=password)

            session_string = client.session.save()

            return {
                "success": True,
                "session_string": session_string,
                "message": "Авторизация успешна",
            }

        except Exception as e:
            logger.error(f"Ошибка проверки пароля: {e}")
            return {"success": False, "message": f"Неверный пароль: {str(e)}"}

    async def start_user_bot(self, user_id: int, session_string: str) -> bool:
        """Запуск user-бота"""
        try:

            if user_id in self.active_bots:
                await self.stop_user_bot(user_id)

            client = TelegramClient(
                StringSession(session_string), self.api_id, self.api_hash
            )

            await client.connect()

            await self._setup_handlers(client, user_id)

            self.active_bots[user_id] = client

            logger.info(f"User-бот для пользователя {user_id} запущен")
            return True

        except Exception as e:
            logger.error(f"Ошибка запуска user-бота: {e}")
            return False

    async def stop_user_bot(self, user_id: int) -> bool:
        """Остановка user-бота"""
        try:
            if user_id in self.active_bots:
                client = self.active_bots[user_id]
                await client.disconnect()
                del self.active_bots[user_id]
                logger.info(f"User-бот для пользователя {user_id} остановлен")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка остановки user-бота: {e}")
            return False

    def is_bot_active(self, user_id: int) -> bool:
        """Проверка, активен ли user-бот"""
        return user_id in self.active_bots

    async def _setup_handlers(self, client: TelegramClient, user_id: int):
        """Настройка обработчиков событий для user-бота"""

        @client.on(events.MessageEdited(outgoing=True))
        @client.on(events.NewMessage(outgoing=True))
        async def auto_correct_handler(event):
            try:

                settings = await UserSettingsDatabase.get_settings(user_id)

                if not settings.get("auto_correct_enabled", True):
                    return

                message = event.message

                if len(message.text) < settings.get("min_message_length", 10):
                    return

                if message.text.startswith("/"):
                    return

                if re.match(
                    r"^[\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+$",
                    message.text,
                ):
                    return

                logger.info(f"Обрабатываем сообщение пользователя {user_id}")

                original_text = message.text

                processed_text = await self.ai_service.correct_text(original_text)
                action_type = "correction"

                if self.ai_service.has_significant_changes(
                    original_text, processed_text
                ):
                    logger.info(f"Сообщение пользователя {user_id} исправлено")

                    await message.edit(processed_text)

                    logger.info("✅ Сообщение обработано!")
                else:
                    logger.info("✅ Изменений не требуется")

            except Exception as e:
                logger.error(
                    f"❌ Ошибка при обработке сообщения пользователя {user_id}: {e}"
                )

        asyncio.create_task(client.run_until_disconnected())
