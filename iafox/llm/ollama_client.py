"""
Cliente para comunicacao com Ollama
"""

import asyncio
from typing import AsyncGenerator, Optional
import httpx
from pydantic import BaseModel
from ..core.config import config


class Message(BaseModel):
    """Mensagem de chat"""
    role: str  # "system", "user", "assistant"
    content: str


class OllamaClient:
    """Cliente para API do Ollama"""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.host = host or config.ollama.host
        self.model = model or config.ollama.model
        self.timeout = timeout or config.ollama.timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtem cliente HTTP"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.host,
                timeout=httpx.Timeout(self.timeout)
            )
        return self._client

    async def close(self):
        """Fecha conexao"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_models(self) -> list[dict]:
        """Lista modelos disponiveis"""
        client = await self._get_client()
        response = await client.get("/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])

    async def check_model(self, model: Optional[str] = None) -> bool:
        """Verifica se modelo esta disponivel"""
        model = model or self.model
        models = await self.list_models()
        return any(m.get("name", "").startswith(model.split(":")[0]) for m in models)

    async def pull_model(self, model: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """Baixa modelo (streaming)"""
        model = model or self.model
        client = await self._get_client()

        async with client.stream(
            "POST",
            "/api/pull",
            json={"name": model},
            timeout=None  # Download pode demorar
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    yield json.loads(line)

    async def chat(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> AsyncGenerator[str, None] | str:
        """
        Envia mensagem para o modelo

        Args:
            messages: Lista de mensagens
            model: Modelo a usar (opcional)
            system: System prompt (opcional)
            temperature: Temperatura (0-1)
            stream: Se deve fazer streaming

        Returns:
            Resposta do modelo (string ou generator)
        """
        model = model or self.model
        client = await self._get_client()

        # Prepara mensagens
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        for msg in messages:
            msgs.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": model,
            "messages": msgs,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }

        if stream:
            return self._stream_chat(client, payload)
        else:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()["message"]["content"]

    async def _stream_chat(
        self,
        client: httpx.AsyncClient,
        payload: dict
    ) -> AsyncGenerator[str, None]:
        """Streaming de resposta"""
        import json

        async with client.stream(
            "POST",
            "/api/chat",
            json=payload,
            timeout=None
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> AsyncGenerator[str, None] | str:
        """
        Geracao simples (sem historico)
        """
        model = model or self.model
        client = await self._get_client()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        if stream:
            return self._stream_generate(client, payload)
        else:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            return response.json()["response"]

    async def _stream_generate(
        self,
        client: httpx.AsyncClient,
        payload: dict
    ) -> AsyncGenerator[str, None]:
        """Streaming de geracao"""
        import json

        async with client.stream(
            "POST",
            "/api/generate",
            json=payload,
            timeout=None
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]


# Instancia global
ollama = OllamaClient()
