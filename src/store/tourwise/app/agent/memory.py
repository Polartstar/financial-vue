"""
多轮记忆模块 — 能力4：多轮对话记忆迭代
层级记忆系统：短期会话记忆 + 长期偏好记忆
支持对话上下文保留、用户偏好学习、方案动态调整
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from app.models.schemas import MemoryState, UserPreference

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    对话记忆管理器
    记忆层级：
      Level 1: 短期对话历史（当前会话的消息记录）
      Level 2: 用户偏好（从对话中提取的兴趣、预算、节奏等）
      Level 3: 当前行程方案（正在构建的计划）
      Level 4: 提及实体索引（对话中提到的城市、景点、美食）
    """

    def __init__(self, session_id: str = None, persist_dir: str = None):
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.persist_dir = persist_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "sessions"
        )
        os.makedirs(self.persist_dir, exist_ok=True)

        self._state: Optional[MemoryState] = None
        self._max_turns = 20

    @property
    def state(self) -> MemoryState:
        if self._state is None:
            self._load()
        return self._state

    def _persist_path(self) -> str:
        return os.path.join(self.persist_dir, f"{self.session_id}.json")

    def _load(self):
        """从磁盘加载记忆"""
        path = self._persist_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = MemoryState(**data)
                logger.debug(f"加载记忆: session={self.session_id}, "
                             f"history={len(self._state.history)}, "
                             f"preferences set={bool(self._state.preferences)}")
            except Exception as e:
                logger.warning(f"加载记忆失败: {e}")
                self._state = MemoryState(session_id=self.session_id)
        else:
            self._state = MemoryState(session_id=self.session_id)

    def _save(self):
        """持久化记忆到磁盘"""
        try:
            path = self._persist_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._state.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存记忆失败: {e}")

    def add_message(self, role: str, content: str, metadata: dict = None):
        """添加一条对话记录

        Args:
            role: "user" 或 "assistant"
            content: 消息内容
            metadata: 附加元数据（意图、子任务等）
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            entry["metadata"] = metadata

        self.state.history.append(entry)

        # 限制历史轮数
        if len(self.state.history) > self._max_turns * 2:
            self.state.history = self.state.history[-(self._max_turns * 2):]

        # 从用户消息中提取偏好
        if role == "user":
            self._extract_preferences(content)

        self._save()

    def _extract_preferences(self, text: str):
        """从用户消息中提取偏好信息"""
        import re
        prefs = self.state.preferences

        # 预算级别
        if re.search(r"(预算.*(\d+)|(\d+).*(预算|花))", text):
            budget_match = re.search(r"(\d+)", text)
            if budget_match:
                budget = int(budget_match.group(1))
                if budget < 1500:
                    prefs.budget_level = "economical"
                elif budget < 4000:
                    prefs.budget_level = "moderate"
                else:
                    prefs.budget_level = "luxury"

        # 节奏
        if re.search(r"(宽松|休闲|慢慢|不赶)", text):
            prefs.pace = "relaxed"
        elif re.search(r"(紧凑|赶|多.|排满)", text):
            prefs.pace = "intense"
        elif re.search(r"(正常|适中|一般)", text):
            prefs.pace = "normal"

        # 同行人
        if re.search(r"(父母|爸妈|老人)", text):
            prefs.companions = "parents"
        elif re.search(r"(孩子|小孩|亲子)", text):
            prefs.companions = "kids"
        elif re.search(r"(情侣|对象|女朋友|男朋友)", text):
            prefs.companions = "couple"
        elif re.search(r"(朋友)", text):
            prefs.companions = "friends"

        # 兴趣爱好
        interests_map = {
            r"(历史|文化|古迹|古建|博物馆)": "历史文化",
            r"(自然|风景|山水|湖|海|山)": "自然风光",
            r"(美食|吃|小吃|餐厅)": "美食体验",
            r"(购物|买|逛街)": "购物",
            r"(拍照|摄影|打卡)": "摄影打卡",
            r"(亲子|小孩|孩子)": "亲子",
            r"(爬山|徒步|户外|运动)": "户外运动",
        }
        for pattern, interest in interests_map.items():
            if re.search(pattern, text) and interest not in prefs.interests:
                prefs.interests.append(interest)

        # 城市偏好
        from app.agent.intent_recognizer import _CITY_PATTERN
        cities = _CITY_PATTERN.findall(text)
        for city in cities:
            if city not in prefs.preferred_cities:
                prefs.preferred_cities.append(city)

        # 更新记忆中的偏好
        self.state.preferences = prefs

    def get_history(self, max_turns: int = 10) -> list[dict]:
        """获取最近的对话历史"""
        return self.state.history[-max_turns * 2:] if self.state.history else []

    def get_context_summary(self) -> str:
        """生成对话上下文的自然语言摘要"""
        prefs = self.state.preferences
        parts = []

        if prefs.budget_level:
            budget_map = {"economical": "经济型", "moderate": "中等预算", "luxury": "豪华型"}
            parts.append(f"预算偏好: {budget_map.get(prefs.budget_level, prefs.budget_level)}")

        if prefs.pace:
            pace_map = {"relaxed": "宽松节奏", "normal": "正常节奏", "intense": "紧凑节奏"}
            parts.append(f"节奏偏好: {pace_map.get(prefs.pace, prefs.pace)}")

        if prefs.companions:
            comp_map = {
                "parents": "带父母", "kids": "亲子", "couple": "情侣",
                "friends": "朋友同行", "solo": "独自"
            }
            parts.append(f"同行: {comp_map.get(prefs.companions, prefs.companions)}")

        if prefs.interests:
            parts.append(f"兴趣: {'、'.join(prefs.interests)}")

        if prefs.preferred_cities:
            parts.append(f"关注城市: {'、'.join(prefs.preferred_cities)}")

        if self.state.current_plan:
            plan = self.state.current_plan
            plan_info = f"已有行程方案"
            if plan.get("city"):
                plan_info += f" ({plan['city']})"
            if plan.get("days"):
                plan_info += f" {plan['days']}天"
            parts.append(plan_info)

        summary = "；".join(parts) if parts else "无已记录的偏好"
        return f"[记忆摘要] {summary}"

    def save_plan(self, plan_data: dict):
        """保存当前行程方案"""
        self.state.current_plan = plan_data
        self._save()

    def get_plan(self) -> dict:
        """获取当前行程方案"""
        return self.state.current_plan

    def clear_session(self):
        """清除当前会话记忆"""
        self._state = MemoryState(session_id=self.session_id)
        self._save()

    def update_preferences(self, prefs: UserPreference):
        """直接更新用户偏好"""
        self.state.preferences = prefs
        self._save()

    @property
    def summary(self) -> str:
        return self.get_context_summary()


# 简单的会话工厂
_session_registry: dict[str, ConversationMemory] = {}


def get_memory(session_id: str = None) -> ConversationMemory:
    """获取或创建会话记忆实例"""
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    if session_id not in _session_registry:
        _session_registry[session_id] = ConversationMemory(session_id)
    return _session_registry[session_id]
