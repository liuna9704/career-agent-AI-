import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMError(RuntimeError):
    pass


class LLMConfigurationError(LLMError):
    pass


class LLMClient:
    """OpenAI-compatible chat completion client used by all AI services."""

    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
        self.model = os.getenv("LLM_MODEL", "").strip()
        self.timeout = float(os.getenv("LLM_TIMEOUT", "60"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    async def chat(self, prompt: str) -> str:
        if not self.configured:
            raise LLMConfigurationError("LLM尚未配置，请设置LLM_API_KEY、LLM_BASE_URL和LLM_MODEL")

        endpoint = self.base_url
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMError("大模型服务调用失败，请检查模型配置或稍后重试") from exc

