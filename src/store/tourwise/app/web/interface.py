"""
TourWise Web 界面 — 使用 Gradio ChatInterface
"""

import logging
import time

import gradio as gr

from app.agent.travel_agent import TravelAgent
from app.agent.memory import ConversationMemory, get_memory

logger = logging.getLogger(__name__)

# 全局状态
_agent: TravelAgent = None
_sessions: dict[str, ConversationMemory] = {}


def set_agent(agent: TravelAgent):
    global _agent
    _agent = agent


def _get_memory(session_key: str) -> ConversationMemory:
    if session_key not in _sessions:
        _sessions[session_key] = get_memory(f"web_{session_key}")
    return _sessions[session_key]


def agent_chat(message: str, history: list) -> str:
    """Agent 聊天函数 (ChatInterface 回调)"""
    if _agent is None:
        return "系统尚未就绪，请稍后再试。"

    # 获取会话记忆 (用 history 长度作为 session key 简化)
    session_key = f"hist_{len(history)}"
    memory = _get_memory(session_key)

    try:
        result = _agent.process(message, memory)
        return result.get("response", "抱歉，处理出错了。")
    except Exception as e:
        logger.error(f"Agent 处理出错: {e}", exc_info=True)
        return f"处理时出错了: {e}"


def create_interface(agent: TravelAgent = None) -> gr.ChatInterface:
    """创建 ChatInterface 界面"""
    if agent:
        set_agent(agent)

    examples = [
        "帮我规划一个3天北京游，预算3000，带父母",
        "故宫门票多少钱?",
        "成都有什么好吃的推荐?",
        "去西安旅游有什么注意事项?",
        "我想去成都玩，预算2000够吗?",
    ]

    demo = gr.ChatInterface(
        fn=agent_chat,
        title="TourWise -- 智能文旅行程规划助手",
        description="基于 Agent 技术的智慧文旅行程规划系统。",
        examples=examples,

    )

    return demo
