from abc import ABC, abstractmethod
import httpx
from google import genai

from ..config import settings


class AIProvider(ABC):
    @abstractmethod
    def draft(self, system: str, user: str) -> str:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def draft(self, system: str, user: str) -> str:
        return ""


class OpenAICompatibleProvider(AIProvider):
    def draft(self, system: str, user: str) -> str:
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.openai_model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        response = httpx.post(url, json=payload, headers=headers, timeout=45)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class GeminiProvider(AIProvider):
    def draft(self, system: str, user: str) -> str:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"{system}\n\n{user}",
        )
        return response.text


def get_ai_provider() -> AIProvider:
    provider = settings.ai_provider.lower()
    if provider == "gemini" and settings.gemini_api_key:
        return GeminiProvider()
    if provider == "openai" and settings.openai_api_key:
        return OpenAICompatibleProvider()
    return MockAIProvider()
