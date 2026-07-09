"""
意图识别模块 — 能力1：用户意图自主识别
混合策略：关键词规则 + 语义匹配，准确识别文旅相关需求
"""

import re
import logging
from typing import Optional

from app.models.schemas import IntentType, IntentResult

logger = logging.getLogger(__name__)

# ─── 意图关键词规则表 ───────────────────────────────────────

_INTENT_PATTERNS: dict[IntentType, list[str]] = {
    IntentType.PLAN_TRIP: [
        r"规划", r"行程", r"旅游计划", r"路线", r"安排.*(天|日|晚)",
        r"攻略", r"怎么玩", r"怎么去", r"推荐.*行程", r"想去.*玩",
        r"帮我.*(规划|安排|设计)", r"(几天|几日).*(游|玩|行程)",
        r"自由行", r"出游", r"旅行计划",
    ],
    IntentType.QUERY_ATTRACTION: [
        r"(门票|开放|时间|地址|介绍|怎么样|好玩吗|值得)",
        r"(门票|开放|介绍|怎么样).*(景|点|区|园|馆|寺|山|湖|城|塔)",
        r"(景|点|区|园|馆|寺).*(门票|开放|好玩|介绍|历史)",
        r"什么.*(值得|好玩|推荐).*(景|点|区)",
    ],
    IntentType.RECOMMEND_FOOD: [
        r"美食", r"好吃", r"吃什", r"餐厅", r"饭馆", r"小吃", r"特色菜",
        r"有什么.*(吃|美食|推荐)", r"(吃|美食).*(推荐|攻略)",
        r"美食街", r"特产", r"必吃", r"老字号",
    ],
    IntentType.TRAVEL_TIP: [
        r"注意什么", r"注意事项", r"贴士", r"建议", r"避坑", r"避雷",
        r"交通", r"住宿", r"天气", r"穿搭", r"穿衣", r"季节",
        r"什么.*(季节|时候|月份).*(去|玩|旅游)",
        r"怎么.*(去|到|坐车|交通)",
    ],
    IntentType.ADJUST_PLAN: [
        r"调整|修改|换|改.*(方案|计划|行程|路线)",
        r"预算.*(不够|多了|调整|改)",
        r"时间.*(不够|不够用|调整)",
        r"加点|减点|去掉|增加.*(景点|天)",
        r"换.*(地方|景点|城市)",
        r"重新.*(规划|安排|设计)",
    ],
    IntentType.BUDGET_QUERY: [
        r"预算", r"花费", r"多少钱.*(够|行)", r"费用", r"开销",
        r"省钱", r"经济.*(游|方案)", r"穷游",
        r"大概.*(多少|花费|钱)",
    ],
    IntentType.WEATHER_QUERY: [
        r"天气", r"气温", r"温度", r"下雨", r"冷不冷", r"热不热",
        r"什么.*(天气|温度|气候)",
    ],
    IntentType.GREETING: [
        r"^(你好|嗨|哈[喽罗]|hi|hello|hey|早上好|晚上好|下午好|你好呀)",
        r"^(在吗|在不在|请问)",
    ],
}

# 城市/景点名称实体提取模式
_CITY_PATTERN = re.compile(
    r"(北京|上海|广州|深圳|杭州|成都|西安|重庆|南京|苏州|厦门|昆明|"
    r"丽江|大理|桂林|阳朔|青岛|长沙|武汉|哈尔滨|拉萨|兰州|"
    r"贵阳|珠海|三亚|海口|宁波|无锡|天津|沈阳|大连|郑州|"
    r"九寨沟|黄山|张家界|鼓浪屿|青海湖)"
)

_ATTRACTION_PATTERN = re.compile(
    r"(故宫|长城|兵马俑|西湖|颐和园|天坛|大雁塔|城墙|外滩|东方明珠|"
    r"迪士尼|熊猫|都江堰|灵隐寺|黄山|漓江|鼓浪屿|拙政园|"
    r"洱海|丽江古城|洪崖洞|布达拉宫|宋城|夫子庙|"
    r"大运河|栈桥|九寨沟|张家界|青海湖)"
)

_NUMBER_PATTERN = re.compile(r"(\d+)\s*(天|日|晚|人|元|块)")

_BUDGET_PATTERN = re.compile(r"(预算|花|控制|限于)\s*(?:在)?\s*(\d+)")


def _match_patterns(text: str, patterns: list[str]) -> bool:
    """检查文本是否匹配模式列表中的任意一项"""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _extract_entities(text: str) -> dict:
    """从文本中提取实体：城市、景点、天数、人数、预算"""
    entities = {}

    # 城市
    cities = _CITY_PATTERN.findall(text)
    if cities:
        entities["cities"] = list(set(cities))

    # 景点
    attractions = _ATTRACTION_PATTERN.findall(text)
    if attractions:
        entities["attractions"] = list(set(attractions))

    # 天数和人数
    numbers = _NUMBER_PATTERN.findall(text)
    for num, unit in numbers:
        n = int(num)
        if unit in ("天", "日"):
            entities["days"] = n
        elif unit == "人":
            entities["people"] = n
        elif unit in ("元", "块"):
            entities["budget"] = n

    # 预算金额
    budget_match = _BUDGET_PATTERN.search(text)
    if budget_match:
        entities["budget"] = int(budget_match.group(2))

    # 同行人
    if re.search(r"(父母|爸妈|老人|长辈)", text):
        entities["companions"] = "parents"
    elif re.search(r"(孩子|小孩|亲子)", text):
        entities["companions"] = "kids"
    elif re.search(r"(情侣|对象|女朋友|男朋友|女友|男友)", text):
        entities["companions"] = "couple"
    elif re.search(r"(朋友|同学|同事)", text):
        entities["companions"] = "friends"
    elif re.search(r"(一?个人|独自|自己)", text):
        entities["companions"] = "solo"

    # 季节
    if re.search(r"(春|春天)", text):
        entities["season"] = "spring"
    elif re.search(r"(夏|夏天|避暑)", text):
        entities["season"] = "summer"
    elif re.search(r"(秋|秋天|枫叶)", text):
        entities["season"] = "autumn"
    elif re.search(r"(冬|冬天|雪|滑雪)", text):
        entities["season"] = "winter"

    return entities


class IntentRecognizer:
    """
    意图识别器
    混合策略：关键词规则快速匹配 + 错误修正
    """

    def __init__(self):
        self._patterns = _INTENT_PATTERNS

    def recognize(self, text: str) -> IntentResult:
        """
        识别用户意图

        Args:
            text: 用户输入文本

        Returns:
            IntentResult: 意图识别结果
        """
        text = text.strip()
        entities = _extract_entities(text)

        # 计算每个意图的匹配得分
        scores = {}
        for intent, patterns in self._patterns.items():
            score = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
            if score > 0:
                scores[intent] = score

        logger.debug(f"意图匹配得分: {scores}")

        # 选择得分最高的意图
        if scores:
            best_intent = max(scores, key=scores.get)
            max_score = scores[best_intent]
            # 如果有并列且包含 PLAN_TRIP -> PLAN_TRIP 优先（更复杂的需求）
            if best_intent in (IntentType.QUERY_ATTRACTION, IntentType.TRAVEL_TIP):
                # 如果提到了天数，可能其实是行程规划
                if entities.get("days"):
                    best_intent = IntentType.PLAN_TRIP
                    max_score += 1

            # 计算置信度
            # 如果有天数或预算跨度的匹配，置信度高
            confidence = min(0.5 + max_score * 0.15, 0.95)
            if entities.get("cities"):
                confidence = min(confidence + 0.1, 0.98)
        else:
            best_intent = IntentType.GENERAL_QA
            confidence = 0.3

        # 如果同时匹配了多个，且没有明确意图 -> fallback to 一般问答
        if best_intent == IntentType.GENERAL_QA and not entities:
            confidence = 0.2

        logger.info(
            f"意图识别: [{best_intent.value}] ({confidence:.2f}) "
            f"实体: {entities}"
        )

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
            raw_text=text,
        )

    def recognize_with_llm(self, text: str, llm_fn) -> IntentResult:
        """
        使用 LLM 辅助意图识别（可选增强）
        当规则匹配置信度低时使用

        Args:
            text: 用户输入
            llm_fn: LLM 调用函数

        Returns:
            IntentResult
        """
        # 先用规则识别
        result = self.recognize(text)

        # 如果置信度足够高，直接返回
        if result.confidence >= 0.6:
            return result

        # 否则尝试 LLM 辅助
        try:
            prompt = f"""你是一个文旅助手，请识别以下用户提问的意图。

可选意图：
- plan_trip: 行程规划（要求规划多天行程、旅游路线）
- query_attraction: 景点咨询（询问景点详情、门票、开放时间）
- recommend_food: 美食推荐（想找好吃的、特色菜）
- travel_tip: 旅行贴士（交通、住宿、季节、注意事项）
- adjust_plan: 调整方案（修改已有行程计划）
- budget_query: 预算查询（问花费、省钱）
- weather_query: 天气查询
- greeting: 打招呼
- general_qa: 一般问答

用户输入: "{text}"

请只输出意图名称（如 plan_trip），不要输出其他内容。"""

            llm_response = llm_fn(prompt)
            llm_intent = llm_response.strip().lower().replace('"', "").replace("'", "")

            # 验证意图是否合法
            for intent in IntentType:
                if intent.value == llm_intent:
                    # 用 LLM 结果覆盖
                    result.intent = intent
                    result.confidence = min(result.confidence + 0.3, 0.95)
                    logger.info(f"LLM 辅助修正意图: {intent.value}")
                    break

        except Exception as e:
            logger.warning(f"LLM 意图识别失败: {e}")

        return result


# 全局单例
_intent_recognizer: Optional[IntentRecognizer] = None


def get_intent_recognizer() -> IntentRecognizer:
    global _intent_recognizer
    if _intent_recognizer is None:
        _intent_recognizer = IntentRecognizer()
    return _intent_recognizer
