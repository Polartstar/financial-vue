"""
TourWise 配置模块
支持从环境变量和 .env 文件加载配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 国内 HuggingFace 被墙, 跳过模型下载, 使用哈希嵌入
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 加载 .env 文件
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """全局配置"""

    # --- LLM 提供者 ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "rule")

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    # DashScope
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen-max")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --- 嵌入模型 ---
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
    )

    # --- 知识库路径 ---
    KNOWLEDGE_BASE_PATH: str = str(
        os.getenv("KNOWLEDGE_BASE_PATH", str(PROJECT_ROOT / "data" / "knowledge_base"))
    )
    CHROMA_PERSIST_DIR: str = str(
        os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "data" / "chroma_db"))
    )

    # --- 应用 ---
    APP_PORT: int = int(os.getenv("APP_PORT", "7860"))
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "20"))

    # 内置知识数据路径
    ATTRACTIONS_DATA: str = str(
        PROJECT_ROOT / "app" / "rag" / "data" / "attractions.json"
    )
    CUISINE_DATA: str = str(PROJECT_ROOT / "app" / "rag" / "data" / "cuisine.json")
    TRAVEL_TIPS_DATA: str = str(
        PROJECT_ROOT / "app" / "rag" / "data" / "travel_tips.json"
    )


settings = Settings()
