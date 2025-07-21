import google.generativeai as genai
import json
import re
import os
import logging
from typing import Optional
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """Сервис для работы с ИИ (Gemini)"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не найден в переменных окружения")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    async def correct_text(self, text: str) -> str:
        """Исправление орфографических и грамматических ошибок"""
        try:
            prompt = f"""
Ты - профессиональный редактор русского языка. Твоя задача - исправить ВСЕ орфографические, грамматические, пунктуационные и стилистические ошибки в тексте.

ПРАВИЛА ИСПРАВЛЕНИЯ:
- Исправь все опечатки и орфографические ошибки
- Исправь грамматические ошибки (падежи, времена, согласования)
- Расставь правильную пунктуацию
- Исправь порядок слов, если он неправильный
- Замени неподходящие слова на правильные синонимы
- Сохрани исходный смысл и стиль сообщения
- Не добавляй лишних слов, не убирай важную информацию
- Сохрани эмоциональную окраску (разговорный стиль, сленг и т.д.)

ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО исправленный текст в следующем JSON формате:
{{"corrected_text": "исправленный текст здесь"}}

ИСХОДНЫЙ ТЕКСТ: {text}

ОТВЕТ:"""

            response = await self.model.generate_content_async(prompt)
            response_text = response.text.strip()

            return self._extract_corrected_text(response_text, text)

        except Exception as e:
            logger.error(f"Ошибка при исправлении текста: {e}")
            return text

    def _extract_corrected_text(self, response_text: str, original_text: str) -> str:
        """Извлечение исправленного текста из ответа ИИ"""
        try:

            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                corrected_text = result.get("corrected_text", original_text)
            else:

                corrected_text = response_text.strip("\"'{}")
                if corrected_text.startswith("corrected_text"):
                    corrected_text = corrected_text.split(":", 1)[-1].strip("\"'")

        except (json.JSONDecodeError, KeyError):

            corrected_text = response_text.strip()
            prefixes = ["corrected_text:", "Исправленный текст:", "Ответ:", "ОТВЕТ:"]
            for prefix in prefixes:
                if corrected_text.startswith(prefix):
                    corrected_text = corrected_text[len(prefix) :].strip()

            corrected_text = corrected_text.strip("\"'{}")

        return corrected_text if corrected_text else original_text

    def has_significant_changes(self, original: str, processed: str) -> bool:
        """Проверка, есть ли существенные изменения между оригиналом и обработанным текстом"""
        if original == processed:
            return False

        original_normalized = re.sub(r"\s+", " ", original.strip())
        processed_normalized = re.sub(r"\s+", " ", processed.strip())

        if original_normalized == processed_normalized:
            return False

        original_words = re.findall(r"\w+", original.lower())
        processed_words = re.findall(r"\w+", processed.lower())

        if (
            len(processed_words) == 0
            or abs(len(original_words) - len(processed_words))
            > len(original_words) * 0.5
        ):
            return False

        distance = self._levenshtein_distance(
            original_normalized.lower(), processed_normalized.lower()
        )
        similarity = 1 - (
            distance / max(len(original_normalized), len(processed_normalized))
        )

        if similarity < 0.6:
            logger.warning(
                f"Слишком большие изменения (схожесть: {similarity:.2f}), пропускаем"
            )
            return False

        return distance > 0

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Вычисление расстояния Левенштейна"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
