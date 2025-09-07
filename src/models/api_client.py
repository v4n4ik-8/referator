import requests
import json
import time
from typing import Optional
from config import TOGETHER_API_KEY


class APIError(Exception):
    """Базовый класс для ошибок API"""
    def __init__(self, message: str, user_message: str):
        self.message = message
        self.user_message = user_message
        super().__init__(self.message)


class RateLimitError(APIError):
    """Ошибка превышения лимита запросов"""
    def __init__(self):
        super().__init__(
            "Rate limit exceeded",
            "К сожалению, мы достигли лимита запросов. 🥺\n\n"
            "Это означает, что наш сервис сейчас очень популярен!\n"
            "Пожалуйста, подождите немного и попробуйте снова через 5-10 минут.\n\n"
            "Если вы часто сталкиваетесь с этой проблемой, вы можете поддержать проект, "
            "чтобы мы могли увеличить лимиты. 💝"
        )


class NetworkError(APIError):
    """Ошибка сети"""
    def __init__(self):
        super().__init__(
            "Network error",
            "Упс! Кажется, возникли проблемы с подключением к сервису. 🌐\n\n"
            "Проверьте ваше интернет-соединение и попробуйте снова.\n"
            "Если проблема повторяется, возможно, наш сервис временно недоступен."
        )


class APIResponseError(APIError):
    """Ошибка ответа API"""
    def __init__(self, status_code: int):
        messages = {
            401: "Ой! Похоже, у нас проблемы с авторизацией. 🔑\n"
                 "Мы уже работаем над этим. Попробуйте позже!",
            403: "Доступ к сервису временно ограничен. 🚫\n"
                 "Мы уже разбираемся с этим. Попробуйте через несколько минут.",
            500: "Произошла ошибка при обработке запроса. 🔧\n\n"
                 "Возможные причины:\n"
                 "• Слишком длинный или сложный запрос\n"
                 "• Временные проблемы с сервисом\n"
                 "• Превышены лимиты на генерацию\n\n"
                 "Попробуйте:\n"
                 "1. Уменьшить количество символов\n"
                 "2. Упростить формулировку темы\n"
                 "3. Подождать пока разраб не пофиксит\n"
                 "4. Перезайти в программу завтра.",
            502: "Сервис временно недоступен. ⚡\n"
                 "Перезайди в программу через пару минут.",
            503: "Сервис перегружен. 🏃\n"
                 "Слишком много студентов пишут рефераты одновременно! "
                 "Подожди немного и попробуй снова.",
            504: "Сервер не отвечает. ⏳\n"
                 "Возможно, запрос слишком сложный. Попробуй уменьшить объём текста."
        }
        super().__init__(
            f"API error: {status_code}",
            messages.get(status_code, "Произошла неожиданная ошибка. 😢\n"
                                      "Мы уже работаем над её устранением.")
        )


class APIClient:
    def __init__(self, base_delay: int = 5, max_retries: int = 3):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.api_key = TOGETHER_API_KEY
        self.base_url = "https://api.together.xyz/v1/chat/completions"
        self.model = "meta-llama/Llama-3-70b-chat-hf"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def make_request(self, prompt: str, attempt: int = 0) -> Optional[str]:
        """Выполняет запрос к Together.ai с повторными попытками"""
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
        }

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                data=json.dumps(data),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    raise APIResponseError(500)

            elif response.status_code == 429:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                    return self.make_request(prompt, attempt + 1)
                raise RateLimitError()

            else:
                raise APIResponseError(response.status_code)

        except requests.exceptions.RequestException:
            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)
                return self.make_request(prompt, attempt + 1)
            raise NetworkError()

        except Exception:
            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** attempt)
                time.sleep(delay)
                return self.make_request(prompt, attempt + 1)
            raise APIResponseError(500)

    def get_essay_structure(self, topic: str, num_chapters: int, language: str = "Русский", discipline: str = "") -> str:
        """Получает структуру реферата"""
        prompt = f"""Создай структуру реферата по учебной дисциплине "{discipline}" на тему "{topic}".

                        Язык генерации: {language}

                        Структура должна включать:
                        1. Введение
                        2. {num_chapters} глав(ы) - каждая должна раскрывать отдельный аспект темы

                        Требования:
                        - Главы должны идти в логическом порядке
                        - Каждая глава должна иметь четкую связь с темой
                        - Названия должны быть научными и формальными
                        - Не добавляй никаких пояснений или комментариев

                        Формат ответа - просто список:
                        Введение
                        Глава 1. [Название]
                        Глава 2. [Название]
                        ..."""

        return self.make_request(prompt)

    def generate_section_content(self, topic: str, section_name: str, symbols_per_chapter: int, language: str = "Русский") -> str:
        """Генерирует содержимое раздела"""
        if "Введение" in section_name:
            prompt = f"""Напиши введение для реферата на тему "{topic}".

                        Язык генерации: {language}

                        Требования:
                        - Объём примерно 2000 символов
                        - Должно включать актуальность темы
                        - Должно описывать цель и задачи исследования
                        - Текст должен быть научным и формальным
                        - Не используй цитаты или ссылки
                        - Не добавляй заголовок "Введение" в начало текста"""
        else:
            prompt = f"""Напиши содержание для главы "{section_name}" реферата на тему "{topic}".

                        Язык генерации: {language}

                        Требования:
                        - Объём примерно {symbols_per_chapter} символов
                        - Текст должен быть научным и формальным
                        - Раскрой тему максимально полно
                        - Не используй цитаты или ссылки
                        - Не добавляй название главы в начало текста"""

        return self.make_request(prompt)
