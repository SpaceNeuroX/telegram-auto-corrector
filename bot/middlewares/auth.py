from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from bot.database.database import UserDatabase


class AuthMiddleware(BaseMiddleware):
    """Middleware для аутентификации и регистрации пользователей"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User = data.get("event_from_user")

        if user:

            db_user = await UserDatabase.get_user(user.id)

            if not db_user:

                await UserDatabase.add_user(
                    user_id=user.id, username=user.username, first_name=user.first_name
                )

            data["db_user"] = db_user

        return await handler(event, data)
