import os
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import re
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
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

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

ИСХОДНЫЙ ТЕКСТ: {text}
"""
            
            response_schema = {
                "type": "object",
                "properties": {
                    "corrected_text": {
                        "type": "string",
                        "description": "Исправленный текст без дополнительных комментариев"
                    }
                },
                "required": ["corrected_text"]
            }
            
            
            generation_config = GenerationConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,  
                max_output_tokens=2048,
            )
            
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            
            try:
                response_json = json.loads(response.text)
                corrected_text = response_json.get("corrected_text", "").strip()
                
                
                if corrected_text:
                    return corrected_text
                else:
                    logger.warning("Получен пустой исправленный текст")
                    return text
                    
            except json.JSONDecodeError as json_error:
                logger.error(f"Ошибка парсинга JSON: {json_error}")
                logger.error(f"Ответ модели: {response.text}")
                return text
                
        except Exception as e:
            logger.error(f"Ошибка при исправлении текста: {e}")
            return text

    def _extract_corrected_text(self, response_text: str, original_text: str) -> str:
        """Резервный метод для извлечения исправленного текста (если JSON не сработает)"""
        try:
            
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed.get("corrected_text", original_text)
            
            return original_text
            
        except Exception:
            return original_text

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
