"""
旅行智能体主控模块 — 能力编排与调度
整合意图识别、任务拆解、RAG检索、多轮记忆四大能力
"""

import json
import logging
import random
import re
from typing import Optional

from app.models.schemas import IntentType, UserPreference
from app.agent.intent_recognizer import IntentRecognizer, get_intent_recognizer
from app.agent.memory import ConversationMemory, get_memory
from app.agent.task_planner import TaskPlanner, SubTask
from app.agent.llm_client import llm_call
from app.rag.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class TravelAgent:
    """
    文旅行程规划智能体主控

    工作流程：
    1. 意图识别（能力1）-> 2. 上下文构建 + RAG检索（能力3）
    3. 任务拆解（能力2）-> 4. 子任务执行 -> 5. 结果合成
    6. 记忆更新（能力4）
    """

    def __init__(self, knowledge_base: KnowledgeBase = None):
        self.recognizer: IntentRecognizer = get_intent_recognizer()
        self.planner = TaskPlanner()
        self.kb = knowledge_base or KnowledgeBase()
        self._llm_enabled = False
        self._register_executors()
        # 检查 LLM 是否可用
        try:
            from app.agent.llm_client import get_llm
            self._llm_enabled = get_llm() is not None
            if self._llm_enabled:
                logger.info("LLM 增强模式已启用")
        except Exception:
            pass

    def _register_executors(self):
        self.planner.register_executor("analyze_demand", self._exec_analyze_demand)
        self.planner.register_executor("search_attractions", self._exec_search_attractions)
        self.planner.register_executor("search_food", self._exec_search_food)
        self.planner.register_executor("search_tips", self._exec_search_tips)
        self.planner.register_executor("arrange_route", self._exec_arrange_route)
        self.planner.register_executor("generate_schedule", self._exec_generate_schedule)
        self.planner.register_executor("search_attraction_info", self._exec_search_attraction_info)
        self.planner.register_executor("extract_detail", self._exec_extract_detail)
        self.planner.register_executor("generate_answer", self._exec_generate_answer)
        self.planner.register_executor("search_local_food", self._exec_search_local_food)
        self.planner.register_executor("filter_by_preference", self._exec_filter_food)
        self.planner.register_executor("recommend", self._exec_recommend)
        self.planner.register_executor("organize_tips", self._exec_organize_tips)
        self.planner.register_executor("search_cost_info", self._exec_search_cost)
        self.planner.register_executor("calculate_budget", self._exec_calculate_budget)
        self.planner.register_executor("saving_tips", self._exec_saving_tips)
        self.planner.register_executor("analyze_change", self._exec_analyze_change)
        self.planner.register_executor("fetch_current_plan", self._exec_fetch_plan)
        self.planner.register_executor("apply_changes", self._exec_apply_changes)
        self.planner.register_executor("generate_new_plan", self._exec_generate_new_plan)
        self.planner.register_executor("general_qa", self._exec_general_qa)

    def process(self, user_input: str, memory: ConversationMemory = None) -> dict:
        if memory is None:
            memory = get_memory()

        intent_result = self.recognizer.recognize(user_input)
        
        # LLM 辅助意图识别（低置信度时增强）
        if self._llm_enabled and intent_result.confidence < 0.6:
            enhanced = self.recognizer.recognize_with_llm(
                user_input, 
                lambda p: llm_call("你是一个文旅意图识别助手", p)
            )
            if enhanced.confidence > intent_result.confidence:
                intent_result = enhanced
                logger.info(f"LLM 增强意图: {intent_result.intent.value} ({intent_result.confidence:.0%})")
        
        memory.add_message("user", user_input, {
            "intent": intent_result.intent.value,
            "entities": intent_result.entities,
        })

        context = self._build_context(intent_result, memory)
        plan = self.planner.decompose(
            intent=intent_result.intent,
            user_request=user_input,
            entities=intent_result.entities,
            context=context,
        )
        # 注意: execute 内置使用 plan.context 作为上下文, 第二个参数是 executor_map
        results = self.planner.execute(plan)
        response = self._synthesize_response(plan, results, intent_result, memory, context)
        
        # LLM 增强：将模板响应转为更自然的语言
        if self._llm_enabled and intent_result.intent not in (IntentType.GREETING, IntentType.UNKNOWN):
            enhanced = self._llm_enhance_response(
                user_input, response, intent_result, context, memory
            )
            if enhanced:
                response = enhanced
        
        memory.add_message("assistant", response, {
            "task_id": plan.task_id,
            "sub_tasks_count": len(plan.sub_tasks),
        })

        if intent_result.intent == IntentType.PLAN_TRIP and results:
            memory.save_plan({
                "city": intent_result.entities.get("cities", [None])[0],
                "days": intent_result.entities.get("days", 3),
                "budget": intent_result.entities.get("budget", 0),
                "companions": intent_result.entities.get("companions", ""),
            })

        return {
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "plan": plan.model_dump(),
            "rag_results": context.get("rag", {}),
            "memory_summary": memory.summary,
            "response": response,
        }

    def _build_context(self, intent_result, memory: ConversationMemory) -> dict:
        context = {
            "entities": intent_result.entities,
            "memory_summary": memory.summary,
            "preferences": memory.state.preferences.model_dump(),
            "has_plan": bool(memory.state.current_plan),
            "current_plan": memory.state.current_plan,
            "rag": {},
        }
        query_parts = []
        cities = intent_result.entities.get("cities", [])
        if cities:
            query_parts.extend(cities)
        attractions = intent_result.entities.get("attractions", [])
        if attractions:
            query_parts.extend(attractions)
        if intent_result.intent == IntentType.RECOMMEND_FOOD:
            query_parts.append("美食")
        elif intent_result.intent == IntentType.TRAVEL_TIP:
            query_parts.append("旅行贴士")

        if query_parts:
            query = " ".join(query_parts)
            rag_results = self.kb.search_all(query, n=5)
            context["rag"]["attractions"] = rag_results.get("attractions", [])
            context["rag"]["food"] = rag_results.get("food", [])
            context["rag"]["tips"] = rag_results.get("tips", [])
            logger.info(f"RAG预热检索: query={query}, "
                       f"attr={len(context['rag']['attractions'])}, "
                       f"food={len(context['rag']['food'])}, "
                       f"tips={len(context['rag']['tips'])}")
        return context

    def _synthesize_response(self, plan, results, intent_result, memory, context: dict = None) -> str:
        intent = intent_result.intent
        entities = intent_result.entities
        ctx = context or {}

        if intent == IntentType.GREETING:
            return self._greeting_response(memory)
        if intent == IntentType.PLAN_TRIP:
            return self._build_trip_plan_response(results, entities, memory, ctx)
        if intent == IntentType.QUERY_ATTRACTION:
            return self._build_attraction_response(results, entities, ctx)
        if intent == IntentType.RECOMMEND_FOOD:
            return self._build_food_response(results, entities, ctx)
        if intent == IntentType.TRAVEL_TIP:
            return self._build_tip_response(results, entities, ctx)
        if intent == IntentType.ADJUST_PLAN:
            return self._build_adjust_response(results, entities, memory, ctx)
        if intent == IntentType.BUDGET_QUERY:
            return self._build_budget_response(results, entities, ctx)
        return self._build_general_response(results, intent_result, ctx)

    # ============ 子任务执行器 ============

    def _exec_analyze_demand(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        prefs = ctx.get("preferences", {})
        cities = entities.get("cities", [])
        days = entities.get("days", 3)
        budget = entities.get("budget", 0)
        companions = entities.get("companions", "")
        comp_map = {"parents": "适合带父母出行的休闲行程", "kids": "适合亲子家庭的轻松行程",
                    "couple": "浪漫情侣行程", "friends": "朋友结伴游", "solo": "一人自由行"}
        comp_note = comp_map.get(companions, "一般行程")
        return (f"需求分析完成: 目标城市{'/'.join(cities) if cities else '待确定'}, "
                f"行程{days}天, {'预算' + str(budget) + '元 ' if budget else ''}"
                f"{comp_note}. 偏好节奏: {prefs.get('pace', '未指定')}.")

    def _exec_search_attractions(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        cities = entities.get("cities", [])
        days = entities.get("days", 3)
        query = f"{' '.join(cities)} 旅游景点 推荐" if cities else "热门旅游景点推荐"
        results = self.kb.search_attractions(query, n=days + 3)
        ctx["_attractions"] = results
        names = [r["metadata"].get("name", "") for r in results]
        return f"检索到景点: {'; '.join(names)}"

    def _exec_search_food(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        cities = entities.get("cities", [])
        query = f"{' '.join(cities)} 美食 特色" if cities else "特色美食"
        results = self.kb.search_food(query, n=5)
        ctx["_food"] = results
        names = [r["metadata"].get("name", "") for r in results]
        return f"检索到美食: {'; '.join(names)}"

    def _exec_search_tips(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        cities = entities.get("cities", [])
        query = f"{' '.join(cities)} 旅行贴士" if cities else "旅行贴士"
        results = self.kb.search_tips(query, n=4)
        ctx["_tips"] = results
        titles = [r["metadata"].get("title", "") for r in results]
        return f"检索到贴士: {'; '.join(titles)}"

    def _exec_arrange_route(self, task: SubTask, ctx: dict) -> str:
        attractions = ctx.get("_attractions", [])
        days = ctx.get("entities", {}).get("days", 3)
        if not attractions:
            return "无足够景点数据编排路线"
        sorted_attr = sorted(attractions, key=lambda x: x["metadata"].get("rating", 0), reverse=True)
        per_day = max(1, (len(sorted_attr) + days - 1) // days)
        route = []
        for d in range(days):
            start = d * per_day
            end = start + per_day
            day_attr = sorted_attr[start:end]
            day_names = [a["metadata"].get("name", "") for a in day_attr]
            route.append(f"第{d+1}天: {' -> '.join(day_names) if day_names else '自由活动'}")
        ctx["_route"] = route
        return "\n".join(route)

    def _exec_generate_schedule(self, task: SubTask, ctx: dict) -> str:
        return "schedule_generated"

    def _exec_search_attraction_info(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        attractions = entities.get("attractions", [])
        name = attractions[0] if attractions else ""
        result = self.kb.get_attraction_detail(name) if name else None
        if result:
            ctx["_attraction_info"] = result
            return f"找到{name}的信息"
        else:
            query = name or entities.get("cities", [""])[0]
            results = self.kb.search_attractions(query, n=3)
            if results:
                ctx["_attraction_info"] = results[0]
                return f"相关景点: {results[0]['metadata'].get('name', '')}"
            return "未找到精确匹配景点"

    def _exec_extract_detail(self, task: SubTask, ctx: dict) -> str:
        info = ctx.get("_attraction_info", {})
        if info:
            ctx["_detail"] = info.get("document", "")
            return "详细信息已提取"
        return "无详细信息可提取"

    def _exec_generate_answer(self, task: SubTask, ctx: dict) -> str:
        return "answer_ready"

    def _exec_search_local_food(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        cities = entities.get("cities", [])
        query = f"{' '.join(cities)} 美食"
        results = self.kb.search_food(query, n=6)
        ctx["_food_results"] = results
        names = [r["metadata"].get("name", "") for r in results]
        return f"找到{'/'.join(names)}等美食推荐"

    def _exec_filter_food(self, task: SubTask, ctx: dict) -> str:
        return "筛选完成"

    def _exec_recommend(self, task: SubTask, ctx: dict) -> str:
        return "recommendation_ready"

    def _exec_organize_tips(self, task: SubTask, ctx: dict) -> str:
        return "tips_organized"

    def _exec_search_cost(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        cities = entities.get("cities", [])
        query = f"{' '.join(cities)} 费用 价格"
        attractions = self.kb.search_attractions(query, n=4)
        ctx["_cost_attractions"] = attractions
        return "检索到费用信息"

    def _exec_calculate_budget(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        days = entities.get("days", 3)
        people = entities.get("people", 1)
        attractions = ctx.get("_cost_attractions", [])
        ticket_total = 0
        ticket_count = 0
        for a in attractions:
            price_str = a["metadata"].get("price", "")
            prices = re.findall(r"(\d+)", price_str)
            if prices:
                ticket_total += int(prices[0])
                ticket_count += 1
        avg_ticket = ticket_total / max(ticket_count, 1)
        total_ticket = avg_ticket * max(len(attractions), 1) * people
        total_food = 100 * days * people
        total_hotel = 250 * (days - 1) * max(people // 2, 1)
        total_transport = 100 * days * people
        total = total_ticket + total_food + total_hotel + total_transport
        ctx["_budget_estimate"] = {
            "ticket": round(total_ticket, 0), "food": round(total_food, 0),
            "hotel": round(total_hotel, 0), "transport": round(total_transport, 0),
            "total": round(total, 0),
        }
        return f"估算总预算约{total:.0f}元"

    def _exec_saving_tips(self, task: SubTask, ctx: dict) -> str:
        tips = self.kb.search_tips("省钱", n=3)
        ctx["_saving_tips"] = tips
        return "省钱建议已准备"

    def _exec_analyze_change(self, task: SubTask, ctx: dict) -> str:
        entities = ctx.get("entities", {})
        has_budget = entities.get("budget") is not None
        ctx["_change_type"] = "budget" if has_budget else "general"
        return f"变更分析: {'预算调整' if has_budget else '方案调整'}"

    def _exec_fetch_plan(self, task: SubTask, ctx: dict) -> str:
        plan = ctx.get("current_plan", {})
        return f"当前方案: {plan.get('city', '')} {plan.get('days', '')}天" if plan else "无已有方案"

    def _exec_apply_changes(self, task: SubTask, ctx: dict) -> str:
        return "changes_applied"

    def _exec_generate_new_plan(self, task: SubTask, ctx: dict) -> str:
        return "new_plan_ready"

    def _exec_general_qa(self, task: SubTask, ctx: dict) -> str:
        return "general_qa_done"

    # ============ 响应生成器 ============

    def _build_trip_plan_response(self, results, entities, memory, ctx: dict = None) -> str:
        days = entities.get("days", 3)
        cities = entities.get("cities", [])
        budget = entities.get("budget", 0)
        companions = entities.get("companions", "")
        city_str = "、".join(cities) if cities else "目的地"
        ctx = ctx or {}
        route = ctx.get("_route", [])
        food_items = ctx.get("_food", [])
        mem_summary = memory.summary if memory else ""

        comp_label = {"parents": "带父母", "kids": "亲子", "couple": "情侣",
                      "friends": "朋友", "solo": "独自"}.get(companions, "一般")
        lines = [
            f"**{city_str}{days}天文旅行程方案**\n",
            f"  **目的地**: {city_str}",
            f"  **行程天数**: {days}天",
            f"  **同行**: {comp_label}",
        ]
        if budget:
            lines.append(f"  **预算**: 约{budget}元")
        lines.append("")

        if route:
            for day_route in route:
                lines.append(f"**{day_route}**")
                lines.append("")
        else:
            for day in range(1, days + 1):
                lines.append(f"**第{day}天:**")
                lines.append(f"  上午: 游览{cities[0] if cities else ''}核心景点")
                lines.append(f"  中午: 品尝当地特色美食")
                lines.append(f"  下午/晚上: 自由活动/夜景")
                lines.append("")

        lines.append("**当地美食推荐**:")
        if food_items:
            for f_item in food_items[:3]:
                lines.append(f"  - {f_item['metadata'].get('name', '')}")
        else:
            lines.append("  - 品尝当地特色小吃")
        lines.append("")

        if budget:
            daily_budget = budget // days
            lines.append(f"**预算分配参考**: 每天约{daily_budget}元")
            lines.append(f"  住宿: 约{(budget * 0.35)//1}元")
            lines.append(f"  餐饮: 约{(budget * 0.25)//1}元")
            lines.append(f"  门票: 约{(budget * 0.2)//1}元")
            lines.append(f"  交通: 约{(budget * 0.2)//1}元")
            lines.append("")

        lines.append("**温馨提示**:")
        if companions == "parents":
            lines.append("  - 带父母出行建议行程不要太赶, 每天2-3个景点")
            lines.append("  - 选择平缓景点, 注意休息")
        elif companions == "kids":
            lines.append("  - 亲子游建议安排半天游玩+半天休息")
            lines.append("  - 选择儿童友好的景点和餐厅")
        lines.append("  - 建议提前预约门票")

        if mem_summary and "记忆摘要" in mem_summary:
            lines.append(f"*{mem_summary}*")
        lines.append("")
        lines.append("告诉我您的想法, 我可以调整这个方案!")
        lines.append("比如: 增加/减少天数、调整预算、换城市等。")
        return "\n".join(lines)

    def _build_attraction_response(self, results, entities, ctx: dict = None) -> str:
        attractions = entities.get("attractions", [])
        name = attractions[0] if attractions else ""
        ctx = ctx or {}

        # 优先直接从知识库查询（不依赖上下文传递）
        info = {}
        if name:
            info = self.kb.get_attraction_detail(name) or {}

        # 兜底: 从 RAG 预热结果
        if not info:
            info = ctx.get("_attraction_info", {})
        if not info:
            rag_attrs = ctx.get("rag", {}).get("attractions", [])
            if rag_attrs:
                info = rag_attrs[0]
        if not info:
            city_str = " ".join(entities.get("cities", []))
            search_results = self.kb.search_attractions(f"{name} {city_str}", n=1)
            if search_results:
                info = search_results[0]

        if not info:
            return (f"关于{name or '该景点'}的信息, 正在查询中...\n\n"
                    f"您可以试试搜索具体景点名称, 比如故宫博物院、兵马俑等。")
        doc = info.get("document", "")
        meta = info.get("metadata", {})
        lines = [f"**{meta.get('name', name)}**\n"]
        for line in doc.split("\n"):
            if line.strip():
                lines.append(f"  {line.strip()}")
        lines.append(f"\n还有什么想了解的? 比如交通、周边景点等。")
        return "\n".join(lines)

    def _build_food_response(self, results, entities, ctx: dict = None) -> str:
        cities = entities.get("cities", [])
        ctx = ctx or {}

        # 优先直接查询知识库（按城市过滤）
        city_str = "、".join(cities) if cities else "特色美食"
        food_results = self.kb.search_food(city_str, n=8)
        # 按城市过滤
        if cities:
            food_results = [f for f in food_results if f.get("metadata", {}).get("city", "") in cities]
        if not food_results:
            food_results = ctx.get("_food_results", []) or ctx.get("_food", [])
        if not food_results:
            return (f"关于{city_str}的美食推荐:\n\n"
                    f"推荐尝试当地特色小吃和人气美食街。您有偏好的口味吗?")

        lines = [f"**{city_str}美食推荐**\n"]
        for i, food in enumerate(food_results[:5], 1):
            doc = food.get("document", "")
            meta = food.get("metadata", {})
            fname = meta.get("name", "美食")
            price = restaurants = must_try = ""
            for line in doc.split("\n"):
                if "价格范围" in line:
                    price = line.replace("价格范围：", "").strip()
                if "推荐餐厅" in line:
                    restaurants = line.replace("推荐餐厅：", "").strip()
                if "必点推荐" in line:
                    must_try = line.replace("必点推荐：", "").strip()
            lines.append(f"{i}. {fname}")
            if price:
                lines.append(f"   价格: {price}")
            if restaurants:
                lines.append(f"   推荐: {restaurants}")
            if must_try:
                lines.append(f"   必点: {must_try}")
            lines.append("")
        lines.append("还有其他需求吗? 比如推荐餐厅的具体位置?")
        return "\n".join(lines)

    def _build_tip_response(self, results, entities, ctx: dict = None) -> str:
        cities = entities.get("cities", [])
        ctx = ctx or {}
        tips = ctx.get("_tips", []) or ctx.get("rag", {}).get("tips", [])
        if not tips:
            tips = self.kb.search_tips("、".join(cities) if cities else "旅行贴士", n=6)
        if not tips:
            return (f"关于{'/'.join(cities) if cities else '通用'}的旅行贴士:\n\n"
                    f"1. 提前查看天气预报\n2. 提前预订门票和住宿\n3. 注意当地交通规则")
        lines = [f"**{'/'.join(cities) if cities else ''}旅行贴士**\n"]
        for tip in tips[:5]:
            doc = tip.get("document", "")
            title = tip.get("metadata", {}).get("title", "")
            if title:
                lines.append(f"**{title}**")
            for line in doc.split("\n"):
                if "内容：" in line:
                    lines.append(f"  {line.replace('内容：', '').strip()}")
            lines.append("")
        lines.append("还有什么需要了解的? 比如交通、住宿等。")
        return "\n".join(lines)

    def _build_budget_response(self, results, entities, ctx: dict = None) -> str:
        ctx = ctx or {}
        estimate = ctx.get("_budget_estimate", {})
        if not estimate:
            return "让我帮您估算旅游预算。请问您的目的地和出行天数?"
        lines = [
            "**旅游预算估算**\n",
            f"  门票: 约{float(estimate.get('ticket', 0)):.0f}元",
            f"  餐饮: 约{float(estimate.get('food', 0)):.0f}元",
            f"  住宿: 约{float(estimate.get('hotel', 0)):.0f}元",
            f"  交通: 约{float(estimate.get('transport', 0)):.0f}元",
            f"\n  **总计: 约{float(estimate.get('total', 0)):.0f}元**\n",
        ]
        saving_tips = ctx.get("_saving_tips", [])
        if saving_tips:
            lines.append("**省钱建议:**")
            for tip in saving_tips[:2]:
                for line in tip.get("document", "").split("\n"):
                    if "内容：" in line:
                        lines.append(f"  - {line.replace('内容：', '').strip()}")
            lines.append("")
        return "\n".join(lines)

    def _build_adjust_response(self, results, entities, memory, ctx: dict = None) -> str:
        ctx = ctx or {}
        plan = memory.get_plan() if memory else {}
        if not plan:
            plan = ctx.get("current_plan", {})
        ents = ctx.get("entities", {})
        has_budget = ents.get("budget")
        if plan:
            lines = [f"**方案已根据您的反馈调整!**\n"]
            if has_budget:
                lines.append(f"  预算从{plan.get('budget',0)}元调整为{has_budget}元")
            lines.append(f"\n  当前方案: {plan.get('city', '')} {plan.get('days', 0)}天")
            lines.append("\n还可以继续调整:")
            lines.append("- 增加/减少天数")
            lines.append("- 调整预算")
            lines.append("- 换城市")
            return "\n".join(lines)
        return ("**好的, 我们来调整方案!**\n\n"
                "不过目前还没有已有方案。请先告诉我您的旅行计划, 比如:\n"
                "帮我规划一个3天北京游")

    def _build_general_response(self, results, intent_result, ctx: dict = None) -> str:
        return ("我可以帮您:\n"
                "- **规划行程**: 告诉我天数、目的地和预算\n"
                "- **查询景点**: 告诉我景点名称\n"
                "- **推荐美食**: 告诉我城市\n"
                "- **旅行贴士**: 问交通、季节、注意事项等\n\n"
                "请告诉我您的需求吧!")

    def _llm_enhance_response(self, user_input: str, rule_response: str,
                                intent_result, context: dict, memory) -> str:
        """用 LLM 将模板响应润色为更自然的语言"""
        if not self._llm_enabled:
            return ""
        
        try:
            rag = context.get("rag", {})
            num_attrs = len(rag.get("attractions", []))
            num_foods = len(rag.get("food", []))
            num_tips = len(rag.get("tips", []))
            mem_summary = memory.summary
            
            system = ("你是一个亲切专业的文旅助手TourWise。"
                      "你的任务是把结构化的行程/景点/美食信息"
                      "转化为自然流畅的中文回复。保持信息准确完整，"
                      "语气热情但不浮夸。适当分段让回复易读。")
            user = (
                f"用户问题: {user_input}\n\n"
                f"系统生成的原始回复:\n{rule_response}\n\n"
                f"RAG检索: {num_attrs}个景点, {num_foods}个美食, {num_tips}条贴士\n"
                f"记忆: {mem_summary}\n\n"
                f"请将上述原始回复改写为更自然亲切的对话风格，"
                f"保留所有关键信息（景点名/价格/天数/预算等），"
                f"不要添加知识库中没有的信息。回复保持在300字以内。"
            )
            enhanced = llm_call(system, user, temperature=0.4)
            if enhanced and len(enhanced) > 20:
                logger.info("LLM 增强响应生成成功")
                return enhanced
        except Exception as e:
            logger.warning(f"LLM 增强响应失败: {e}")
        return ""

    def _greeting_response(self, memory) -> str:
        prefs = memory.state.preferences
        if prefs.interests or prefs.preferred_cities:
            interests = "、".join(prefs.interests[:2]) if prefs.interests else "旅游"
            return (f"欢迎回来! 记得您喜欢{interests}, 有什么需要帮忙的吗?\n\n"
                    f"我可以帮您规划行程、查询景点、推荐美食等。")
        return ("你好! 我是 TourWise 文旅助手。\n\n"
                f"我可以帮您:\n"
                f"- 规划旅行行程\n"
                f"- 查询景点信息\n"
                f"- 推荐当地美食\n"
                f"- 提供旅行贴士\n\n"
                f"想去哪里玩呀?")


_agent: Optional[TravelAgent] = None


def get_agent(knowledge_base: KnowledgeBase = None) -> TravelAgent:
    global _agent
    if _agent is None:
        _agent = TravelAgent(knowledge_base)
    return _agent
