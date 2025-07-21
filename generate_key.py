#!/usr/bin/env python3
"""
Утилита для генерации ключа шифрования сессий
"""
import secrets
import string

def generate_encryption_key(length: int = 64) -> str:
    """Генерирует случайный ключ для шифрования"""
    alphabet = string.ascii_letters + string.digits + "_-"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    key = generate_encryption_key()
    print("🔐 Сгенерированный ключ шифрования:")
    print(f"ENCRYPTION_KEY={key}")
    print("\n📝 Добавьте эту строку в ваш .env файл")
    print("⚠️  ВАЖНО: Сохраните этот ключ в надежном месте!")
    print("   Если потеряете ключ, все сохраненные сессии станут недоступными.")
