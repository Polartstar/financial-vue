"""
任务拆解与执行模块 — 能力2：自主任务拆解与推理
将复杂文旅需求拆解为多步子任务，按序执行
"""

import logging
import re
import uuid
from typing import Callable

from app.models.schemas import IntentType, SubTask, TaskPlan

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    任务规划器
    核心能力：将复杂的用户需求拆解为可执行的子任务序列
    """

    def __init__(self):
        self._executors: dict[str, Callable] = {}

    def register_executor(self, task_type: str, executor_fn: Callable):
        """注册子任务执行器"""
        self._executors[task_type] = executor_fn

    def decompose(self, intent: IntentType, user_request: str, entities: dict,
                  context: dict = None) -> TaskPlan:
        """
        将用户需求拆解为子任务序列

        Args:
            intent: 识别到的意图
            user_request: 原始用户输入
            entities: 提取的实体（城市、天数、预算等）
            context: 额外上下文（用户偏好、历史等）

        Returns:
            TaskPlan: 包含子任务列表的执行计划
        """
        task_id = f"plan_{uuid.uuid4().hex[:8]}"
        sub_tasks: list[SubTask] = []

        if intent == IntentType.PLAN_TRIP:
            sub_tasks = self._decompose_trip_planning(entities, context)

        elif intent == IntentType.QUERY_ATTRACTION:
            sub_tasks = self._decompose_attraction_query(entities, user_request)

        elif intent == IntentType.RECOMMEND_FOOD:
            sub_tasks = self._decompose_food_recommendation(entities, user_request)

        elif intent == IntentType.TRAVEL_TIP:
            sub_tasks = self._decompose_travel_tip(entities, user_request)

        elif intent == IntentType.ADJUST_PLAN:
            sub_tasks = self._decompose_plan_adjustment(entities, user_request, context)

        elif intent == IntentType.BUDGET_QUERY:
            sub_tasks = self._decompose_budget_query(entities)

        else:
            # 一般问答：单步处理
            sub_tasks = [
                SubTask(
                    step_id="general_qa",
                    name="一般问答处理",
                    description=f"回答用户的一般性文旅问题",
                )
            ]

        plan = TaskPlan(
            task_id=task_id,
            intent=intent,
            user_request=user_request,
            sub_tasks=sub_tasks,
            context=context or {},
            current_step=0,
            total_steps=len(sub_tasks),
        )

        logger.info(
            f"任务拆解: [{intent.value}] {len(sub_tasks)}个子任务\n"
            + "\n".join(f"  [{s.step_id}] {s.name}: {s.description}"
                        for s in sub_tasks)
        )

        return plan

    def _decompose_trip_planning(self, entities: dict, context: dict = None) -> list[SubTask]:
        """行程规划任务拆解"""
        days = entities.get("days", 3)
        cities = entities.get("cities", [])
        budget = entities.get("budget", None)
        companions = entities.get("companions", "")

        sub_tasks = [
            SubTask(
                step_id="analyze_demand",
                name="需求分析",
                description=f"分析{'、'.join(cities) if cities else '目标城市'} "
                           f"{days}天行程需求，考虑同行{companions if companions else '一般'}情况"
                           f"{'，预算'+str(budget) if budget else ''}",
            ),
            SubTask(
                step_id="search_attractions",
                name="景点搜索与筛选",
                description=f"从知识库检索{'、'.join(cities) if cities else '相关'}景点，"
                           f"筛选适合{days}天行程的景点",
            ),
            SubTask(
                step_id="search_food",
                name="美食推荐查询",
                description="检索当地特色美食和推荐餐厅信息",
            ),
            SubTask(
                step_id="search_tips",
                name="旅行贴士检索",
                description="检索交通、季节、注意事项等相关贴士",
            ),
            SubTask(
                step_id="arrange_route",
                name="路线编排",
                description=f"将筛选的景点编排为{days}天的合理行程路线，考虑地理位置和交通",
            ),
            SubTask(
                step_id="generate_schedule",
                name="生成行程方案",
                description="整合所有信息，生成完整行程表（含景点、美食、预算建议）",
            ),
        ]
        return sub_tasks

    def _decompose_attraction_query(self, entities: dict, user_request: str) -> list[SubTask]:
        """景点咨询任务拆解"""
        attractions = entities.get("attractions", [])
        cities = entities.get("cities", [])

        if attractions:
            target = attractions[0]
        elif cities:
            target = cities[0]
        else:
            target = "未知景点"

        return [
            SubTask(
                step_id="search_attraction_info",
                name="景点信息检索",
                description=f"从知识库检索「{target}」的详细信息",
            ),
            SubTask(
                step_id="extract_detail",
                name="提取详细信息",
                description=f"提取{target}的门票、开放时间、游览建议等用户关心的信息",
            ),
            SubTask(
                step_id="generate_answer",
                name="生成回答",
                description="将检索到的信息整理成用户友好的回答",
            ),
        ]

    def _decompose_food_recommendation(self, entities: dict, user_request: str) -> list[SubTask]:
        """美食推荐任务拆解"""
        cities = entities.get("cities", [])
        city = cities[0] if cities else ""

        return [
            SubTask(
                step_id="search_local_food",
                name="本地美食检索",
                description=f"检索{city}的特色美食和推荐餐厅" if city else "检索美食推荐",
            ),
            SubTask(
                step_id="filter_by_preference",
                name="按偏好筛选",
                description="根据用户口味和预算偏好进行筛选过滤",
            ),
            SubTask(
                step_id="recommend",
                name="生成推荐",
                description="整理推荐结果并给出具体餐厅建议",
            ),
        ]

    def _decompose_travel_tip(self, entities: dict, user_request: str) -> list[SubTask]:
        """旅行贴士任务拆解"""
        cities = entities.get("cities", [])
        keywords = []

        if "交通" in user_request:
            keywords.append("交通")
        if "住宿" in user_request:
            keywords.append("住宿")
        if "季节" in user_request or "天气" in user_request:
            keywords.append("季节")
        if "安全" in user_request or "注意" in user_request:
            keywords.append("安全")

        if not keywords:
            keywords.append("综合")

        target = cities[0] if cities else "通用"
        return [
            SubTask(
                step_id="search_tips",
                name="贴士检索",
                description=f"检索{target}的{','.join(keywords)}相关旅行建议",
            ),
            SubTask(
                step_id="organize_tips",
                name="整理建议",
                description="按类别整理检索到的旅行贴士",
            ),
        ]

    def _decompose_plan_adjustment(self, entities: dict, user_request: str,
                                   context: dict = None) -> list[SubTask]:
        """调整方案任务拆解"""
        # 检查是否有已有方案
        has_existing_plan = bool(context and context.get("has_plan"))

        sub_tasks = [
            SubTask(
                step_id="analyze_change",
                name="变更需求分析",
                description="分析用户希望如何调整行程",
            ),
            SubTask(
                step_id="fetch_current_plan",
                name="读取当前方案",
                description="获取已有的行程方案" if has_existing_plan else "确定调整基线",
            ),
            SubTask(
                step_id="apply_changes",
                name="执行调整",
                description="根据需求调整行程方案",
            ),
            SubTask(
                step_id="generate_new_plan",
                name="生成新方案",
                description="输出调整后的完整行程方案",
            ),
        ]
        return sub_tasks

    def _decompose_budget_query(self, entities: dict) -> list[SubTask]:
        """预算查询任务拆解"""
        cities = entities.get("cities", [])
        target = cities[0] if cities else "通用"

        return [
            SubTask(
                step_id="search_cost_info",
                name="费用信息检索",
                description=f"检索{target}的景区门票、餐饮、住宿等费用参考",
            ),
            SubTask(
                step_id="calculate_budget",
                name="预算估算",
                description="根据检索到的信息估算旅游总花费",
            ),
            SubTask(
                step_id="saving_tips",
                name="省钱建议",
                description="提供省钱技巧和性价比选择建议",
            ),
        ]

    def execute(self, plan: TaskPlan, executor_map: dict = None) -> list[str]:
        """
        顺序执行子任务

        Args:
            plan: 任务计划
            executor_map: 子任务执行器映射 {step_id: callable}

        Returns:
            各子任务的执行结果列表
        """
        results = []
        executor_map = executor_map or self._executors

        for i, sub_task in enumerate(plan.sub_tasks):
            plan.current_step = i
            sub_task.status = "running"
            logger.info(f"执行子任务 [{i+1}/{plan.total_steps}]: {sub_task.name}")

            # 查找匹配的执行器
            executor = executor_map.get(sub_task.step_id)
            if executor:
                try:
                    result = executor(sub_task, plan.context)
                    sub_task.result = str(result)
                    sub_task.status = "done"
                except Exception as e:
                    sub_task.result = f"执行失败: {e}"
                    sub_task.status = "failed"
                    logger.warning(f"子任务失败 [{sub_task.step_id}]: {e}")
            else:
                sub_task.result = f"暂未实现执行器: {sub_task.step_id}"
                sub_task.status = "done"

            results.append(sub_task.result)

        return results
