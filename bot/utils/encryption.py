import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logger = logging.getLogger(__name__)

class SessionEncryption:
    """Класс для шифрования и дешифрования сессий"""
    
    def __init__(self):
        self._fernet = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ленивая инициализация - загружаем ключ только при первом использовании"""
        if self._initialized:
            return
            
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY не найден в переменных окружения!")
        
        # Создаем ключ для Fernet из нашего секретного ключа
        self._fernet = self._create_fernet_key(encryption_key)
        self._initialized = True
    
    def _create_fernet_key(self, encryption_key: str) -> Fernet:
        """Создание ключа Fernet из строки"""
        # Используем PBKDF2 для создания 32-байтного ключа
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'telegram_session_salt',  # Фиксированная соль
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        return Fernet(key)
    
    def encrypt_session(self, session_string: str) -> str:
        """Шифрование строки сессии"""
        try:
            self._ensure_initialized()
            
            if not session_string:
                return ""
            
            encrypted_data = self._fernet.encrypt(session_string.encode('utf-8'))
            # Возвращаем в base64 для хранения в БД
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Ошибка шифрования сессии: {e}")
            raise
    
    def decrypt_session(self, encrypted_session: str) -> str:
        """Дешифрование строки сессии"""
        try:
            self._ensure_initialized()
            
            if not encrypted_session:
                return ""
            
            # Декодируем из base64
            encrypted_data = base64.b64decode(encrypted_session.encode('utf-8'))
            # Дешифруем
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Ошибка дешифрования сессии: {e}")
            raise

# Глобальный экземпляр для использования в других модулях
session_crypto = SessionEncryption()
