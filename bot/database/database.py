import aiosqlite
import os
from typing import Optional, List, Dict, Any
import json
import logging
from bot.utils.encryption import session_crypto

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")





async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                phone_number TEXT,
                session_string TEXT,
                is_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                correction_mode BOOLEAN DEFAULT TRUE,
                min_message_length INTEGER DEFAULT 10,
                auto_correct_enabled BOOLEAN DEFAULT TRUE,
                settings_json TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )

        await db.commit()
    
    logger.info("База данных инициализирована")


class UserDatabase:
    """Класс для работы с пользователями в базе данных"""

    @staticmethod
    async def add_user(
        user_id: int, username: str = None, first_name: str = None
    ) -> bool:
        """Добавление нового пользователя"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                    (user_id, username, first_name),
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False

    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    @staticmethod
    async def update_phone_number(user_id: int, phone_number: str) -> bool:
        """Обновление номера телефона пользователя"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "UPDATE users SET phone_number = ? WHERE user_id = ?",
                    (phone_number, user_id),
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления номера телефона: {e}")
            return False


class UserBotDatabase:
    """Класс для работы с user-ботами в базе данных"""

    @staticmethod
    async def add_user_bot(
        user_id: int, phone_number: str, session_string: str
    ) -> bool:
        """Добавление user-бота с шифрованием сессии"""
        try:
            
            try:
                if session_crypto:
                    encrypted_session = session_crypto.encrypt_session(session_string)
                    logger.info(f"Сессия для пользователя {user_id} зашифрована")
                else:
                    logger.warning("Шифрование недоступно, сохраняем сессию без шифрования!")
                    encrypted_session = session_string
            except Exception as encrypt_error:
                logger.error(f"Ошибка шифрования сессии: {encrypt_error}")
                logger.warning("Сохраняем сессию без шифрования")
                encrypted_session = session_string
                
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "INSERT INTO user_bots (user_id, phone_number, session_string, is_active) VALUES (?, ?, ?, ?)",
                    (user_id, phone_number, encrypted_session, True),
                )
                await db.commit()
                logger.info(f"Сессия для пользователя {user_id} сохранена с шифрованием")
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления user-бота: {e}")
            return False

    @staticmethod
    async def get_user_bot(user_id: int) -> Optional[Dict[str, Any]]:
        """Получение user-бота пользователя с дешифрованием сессии"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_bots WHERE user_id = ? AND is_active = TRUE ORDER BY created_at DESC LIMIT 1",
                    (user_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        bot_data = dict(row)
                        
                        if session_crypto and bot_data.get('session_string'):
                            try:
                                bot_data['session_string'] = session_crypto.decrypt_session(bot_data['session_string'])
                                logger.info(f"Сессия для пользователя {user_id} дешифрована")
                            except Exception as e:
                                logger.error(f"Ошибка дешифрования сессии для пользователя {user_id}: {e}")
                                
                                logger.warning("Возможно, сессия сохранена без шифрования")
                        elif not session_crypto:
                            logger.warning("Шифрование недоступно, используем сессию как есть")
                        return bot_data
                    return None
        except Exception as e:
            logger.error(f"Ошибка получения user-бота: {e}")
            return None

    @staticmethod
    async def deactivate_user_bot(user_id: int) -> bool:
        """Деактивация user-бота"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "UPDATE user_bots SET is_active = FALSE WHERE user_id = ?",
                    (user_id,),
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка деактивации user-бота: {e}")
            return False


class UserSettingsDatabase:
    """Класс для работы с настройками пользователей"""

    @staticmethod
    async def get_settings(user_id: int) -> Dict[str, Any]:
        """Получение настроек пользователя"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        settings = dict(row)

                        try:
                            settings["additional_settings"] = json.loads(
                                settings.get("settings_json", "{}")
                            )
                        except:
                            settings["additional_settings"] = {}
                        return settings
                    else:

                        await UserSettingsDatabase.create_default_settings(user_id)
                        return await UserSettingsDatabase.get_settings(user_id)
        except Exception as e:
            logger.error(f"Ошибка получения настроек: {e}")
            return {}

    @staticmethod
    async def create_default_settings(user_id: int) -> bool:
        """Создание настроек по умолчанию"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO user_settings (user_id) VALUES (?)",
                    (user_id,),
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка создания настроек по умолчанию: {e}")
            return False

    @staticmethod
    async def update_setting(user_id: int, setting_name: str, value: Any) -> bool:
        """Обновление конкретной настройки"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                if setting_name in ["correction_mode", "auto_correct_enabled"]:
                    await db.execute(
                        f"UPDATE user_settings SET {setting_name} = ? WHERE user_id = ?",
                        (value, user_id),
                    )
                elif setting_name == "min_message_length":
                    await db.execute(
                        "UPDATE user_settings SET min_message_length = ? WHERE user_id = ?",
                        (value, user_id),
                    )
                else:

                    current_settings = await UserSettingsDatabase.get_settings(user_id)
                    additional = current_settings.get("additional_settings", {})
                    additional[setting_name] = value
                    await db.execute(
                        "UPDATE user_settings SET settings_json = ? WHERE user_id = ?",
                        (json.dumps(additional), user_id),
                    )

                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления настройки: {e}")
            return False



