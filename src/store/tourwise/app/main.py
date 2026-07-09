"""
TourWise 主入口 — FastAPI 应用
"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.agent.travel_agent import TravelAgent, get_agent
from app.agent.memory import ConversationMemory, get_memory
from app.rag.knowledge_base import KnowledgeBase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# 全局实例
agent: TravelAgent = None
kb: KnowledgeBase = None


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    intent: str = ""
    confidence: float = 0.0
    memory_summary: str = ""


class KBStatus(BaseModel):
    total_documents: int
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global agent, kb
    logger.info("TourWise 启动中...")

    # 初始化知识库
    kb = KnowledgeBase()
    doc_count = kb.initialize()
    logger.info(f"知识库就绪: {doc_count} 条文档")

    # 初始化智能体
    agent = get_agent(kb)
    logger.info("智能体初始化完成")

    yield

    logger.info("TourWise 关闭")


app = FastAPI(
    title="TourWise API",
    description="智能文旅行程规划助手 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "TourWise",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "kb_status": "/kb/status",
            "docs": "/docs",
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """对话接口"""
    if not agent:
        raise HTTPException(status_code=503, detail="智能体未就绪")

    memory = get_memory(request.session_id)
    result = agent.process(request.message, memory)

    return ChatResponse(
        response=result["response"],
        intent=result["intent"],
        confidence=result["confidence"],
        memory_summary=result.get("memory_summary", ""),
    )


@app.get("/kb/status", response_model=KBStatus)
async def kb_status():
    """知识库状态"""
    if not kb:
        raise HTTPException(status_code=503, detail="知识库未就绪")
    return KBStatus(
        total_documents=kb.vs.count(),
        status="ready",
    )


@app.post("/kb/rebuild")
async def rebuild_kb():
    """重建知识库索引"""
    if not kb:
        raise HTTPException(status_code=503, detail="知识库未就绪")
    count = kb.initialize(force=True)
    return KBStatus(total_documents=count, status="rebuilt")


def run_api():
    """以 API 模式启动"""
    import uvicorn
    logger.info(f"启动 API 服务: http://{settings.APP_HOST}:{settings.APP_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
    )
