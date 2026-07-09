#!/usr/bin/env python3
"""
TourWise — 智能文旅行程规划助手
启动入口

用法:
    python run.py              # 启动 Web UI (Gradio)
    python run.py --api        # 启动 API (FastAPI)
    python run.py --init-kb    # 初始化知识库
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tourwise")


def main():
    parser = argparse.ArgumentParser(description="TourWise 智能文旅行程规划助手")
    parser.add_argument("--api", action="store_true", help="以 API 模式启动")
    parser.add_argument("--init-kb", action="store_true", help="初始化知识库")
    parser.add_argument("--port", type=int, default=0, help="端口号")
    parser.add_argument("--host", type=str, default="", help="监听地址")
    args = parser.parse_args()

    from app.config import settings

    # 覆盖端口
    if args.port:
        settings.APP_PORT = args.port
    if args.host:
        settings.APP_HOST = args.host

    # 初始化知识库
    from app.rag.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()

    if args.init_kb:
        logger.info("初始化知识库...")
        count = kb.initialize(force=True)
        print(f"\n[OK] 知识库构建完成！共索引 {count} 条数据。\n")
        return

    if args.api:
        # API 模式
        logger.info(f"启动 API 模式: http://{settings.APP_HOST}:{settings.APP_PORT}")
        from app.main import run_api
        run_api()
    else:
        # Web UI 模式 (Gradio)
        doc_count = kb.initialize()
        logger.info(f"知识库已就绪 ({doc_count} 条文档)")

        from app.agent.travel_agent import get_agent
        agent = get_agent(kb)

        # 预热：首次 Embedding 和 Ollama 调用
        if hasattr(agent, '_llm_enabled') and agent._llm_enabled:
            from app.agent.llm_client import llm_call
            logger.info('预热 LLM 模型...')
            llm_call('你是一个文旅助手', '你好')
            logger.info('LLM 预热完成')

        from app.web.interface import create_interface
        interface = create_interface(agent)

        logger.info(f"启动 Web UI: http://{settings.APP_HOST}:{settings.APP_PORT}")
        interface.launch(
            server_name=settings.APP_HOST,
            server_port=settings.APP_PORT,
            share=False,
        )


if __name__ == "__main__":
    main()
