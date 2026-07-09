"""
TourWise 数据模型定义
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class IntentType(str, Enum):
    """用户意图类型"""
    PLAN_TRIP = "plan_trip"              # 行程规划
    QUERY_ATTRACTION = "query_attraction"  # 景点咨询
    RECOMMEND_FOOD = "recommend_food"      # 美食推荐
    TRAVEL_TIP = "travel_tip"              # 旅行贴士
    ADJUST_PLAN = "adjust_plan"            # 调整方案
    BUDGET_QUERY = "budget_query"          # 预算查询
    WEATHER_QUERY = "weather_query"        # 天气查询
    GENERAL_QA = "general_qa"              # 一般问答
    GREETING = "greeting"                  # 打招呼
    UNKNOWN = "unknown"                    # 未识别


class IntentResult(BaseModel):
    """意图识别结果"""
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict = Field(default_factory=dict)
    raw_text: str = ""


class SubTask(BaseModel):
    """子任务定义"""
    step_id: str
    name: str
    description: str
    status: str = "pending"  # pending | running | done | failed
    result: str = ""


class TaskPlan(BaseModel):
    """任务拆解计划"""
    task_id: str
    intent: IntentType
    user_request: str
    sub_tasks: list[SubTask] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    current_step: int = 0
    total_steps: int = 0


class UserPreference(BaseModel):
    """用户偏好"""
    budget_level: str = ""      # economical | moderate | luxury
    pace: str = ""              # relaxed | normal | intense
    interests: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    companions: str = ""        # solo | couple | family | friends
    preferred_cities: list[str] = Field(default_factory=list)


class MemoryState(BaseModel):
    """记忆状态"""
    session_id: str
    history: list[dict] = Field(default_factory=list)
    preferences: UserPreference = Field(default_factory=UserPreference)
    current_plan: dict = Field(default_factory=dict)
    mentioned_entities: dict = Field(default_factory=dict)


class Attraction(BaseModel):
    """景点数据模型"""
    name: str
    city: str
    category: str = ""          # 自然风光/历史文化/主题乐园/...
    description: str = ""
    opening_hours: str = ""
    ticket_price: str = ""
    rating: float = 0.0
    tags: list[str] = Field(default_factory=list)
    best_season: str = ""
    tips: str = ""
    duration: str = ""          # 建议游览时长
    image_url: str = ""


class Cuisine(BaseModel):
    """美食数据模型"""
    name: str
    city: str
    category: str = ""
    description: str = ""
    restaurant_recommendations: list[str] = Field(default_factory=list)
    price_range: str = ""
    must_try: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TravelTip(BaseModel):
    """旅行贴士"""
    title: str
    category: str = ""          # 交通/住宿/季节/安全/...
    city: str = ""
    content: str = ""
    tags: list[str] = Field(default_factory=list)
