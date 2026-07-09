"""
LLM 客户端模块 — 支持 Ollama / DashScope / OpenAI 等后端
"""

import json
import logging
import re
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._client: Optional[httpx.Client] = None

    @property
    def client(self):
        if self._client is None:
            self._client = httpx.Client(timeout=60.0)
        return self._client

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """调用 LLM 聊天接口"""
        if self.provider == "ollama":
            return self._call_ollama(system_prompt, user_prompt, temperature)
        elif self.provider == "dashscope":
            return self._call_dashscope(system_prompt, user_prompt, temperature)
        elif self.provider == "openai":
            return self._call_openai(system_prompt, user_prompt, temperature)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    # ─── Ollama ───

    def _call_ollama(self, system: str, user: str, temperature: float) -> str:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        try:
            resp = self.client.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Ollama 调用失败: {e}")
            return ""

    # ─── DashScope (通义千问) ───

    def _call_dashscope(self, system: str, user: str, temperature: float) -> str:
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.DASHSCOPE_MODEL,
            "input": {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
            },
            "parameters": {
                "temperature": temperature,
                "result_format": "message",
            },
        }
        try:
            resp = self.client.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"DashScope 调用失败: {e}")
            return ""

    # ─── OpenAI 兼容 ───

    def _call_openai(self, system: str, user: str, temperature: float) -> str:
        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        try:
            resp = self.client.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"OpenAI 调用失败: {e}")
            return ""


_global_llm: Optional[LLMClient] = None


def get_llm() -> Optional[LLMClient]:
    """获取 LLM 客户端（仅在配置了 provider 时有效）"""
    global _global_llm
    if _global_llm is None:
        provider = settings.LLM_PROVIDER
        if provider and provider != "rule":
            _global_llm = LLMClient()
            logger.info(f"LLM 客户端初始化: provider={provider}")
    return _global_llm


def llm_call(system: str, user: str, temperature: float = 0.3) -> str:
    """便捷 LLM 调用（失败时返回空字符串）"""
    client = get_llm()
    if client is None:
        return ""
    return client.chat(system, user, temperature)
