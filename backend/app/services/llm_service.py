from app.core.llm import LLMClient


class LLMService:
    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or LLMClient()

    async def chat(self, prompt: str) -> str:
        return await self.client.chat(prompt)


llm_service = LLMService()

