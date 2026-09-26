from abc import ABC, abstractmethod
import json
import httpx

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


def get_ai_provider() -> AIProvider:
    if settings.ai_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAICompatibleProvider()
    return MockAIProvider()
