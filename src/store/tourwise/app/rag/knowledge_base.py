"""
知识库管理模块 — 提供高层 API 封装 RAG 检索
含 JSON 数据文件直接查找兜底
"""

import json
import logging

from app.config import settings
from app.rag.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)


def _load_json_data(path: str) -> list[dict]:
    """加载 JSON 数据文件"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"JSON加载失败 {path}: {e}")
        return []


class KnowledgeBase:
    """知识库管理器，封装文旅数据检索接口"""

    def __init__(self, vector_store: VectorStore = None):
        self.vs = vector_store or get_vector_store()

    def initialize(self, force: bool = False):
        count = self.vs.count()
        if count == 0 or force:
            logger.info("正在构建知识库索引...")
            return self.vs.build_all_indexes()
        logger.info(f"知识库已就绪，现有 {count} 条数据")
        return count

    def _attraction_from_json(self, item: dict) -> dict:
        """将 JSON 景点数据转为与向量检索一致的格式"""
        lines = [f"{k}：{v}" for k, v in item.items() if v]
        return {
            "document": "\n".join(lines),
            "metadata": {
                "type": "attraction",
                "name": item["name"],
                "city": item["city"],
                "category": item.get("category", ""),
                "rating": item.get("rating", 0),
                "price": item.get("ticket_price", ""),
            },
        }

    def _cuisine_from_json(self, item: dict) -> dict:
        lines = [f"{k}：{v}" for k, v in item.items() if v]
        return {
            "document": "\n".join(lines),
            "metadata": {"type": "cuisine", "name": item["name"], "city": item.get("city", "")},
        }

    def _tip_from_json(self, item: dict) -> dict:
        lines = [f"{k}：{v}" for k, v in item.items() if v]
        return {
            "document": "\n".join(lines),
            "metadata": {"type": "tip", "title": item.get("title", ""), "category": item.get("category", ""), "city": item.get("city", "")},
        }

    def search_attractions(self, query: str, n: int = 5) -> list[dict]:
        results = self.vs.search(query, n_results=n, type_filter="attraction")
        # RAG 无结果时 JSON 兜底
        if not results:
            data = _load_json_data(settings.ATTRACTIONS_DATA)
            for item in data:
                text = item["name"] + item.get("city", "") + item.get("description", "") + item.get("tags", "")
                if any(kw in text for kw in query.split() if len(kw) >= 2):
                    results.append(self._attraction_from_json(item))
                    if len(results) >= n:
                        break
        names = [r["metadata"].get("name", "") for r in results]
        logger.info(f"景点检索: '{query}' -> {names}")
        return results

    def search_food(self, query: str, n: int = 5) -> list[dict]:
        results = self.vs.search(query, n_results=n, type_filter="cuisine")
        if not results:
            data = _load_json_data(settings.CUISINE_DATA)
            for item in data:
                text = item["name"] + item.get("city", "") + item.get("description", "") + "".join(item.get("tags", ""))
                if any(kw in text for kw in query.split() if len(kw) >= 2):
                    results.append(self._cuisine_from_json(item))
                    if len(results) >= n:
                        break
        names = [r["metadata"].get("name", "") for r in results]
        logger.info(f"美食检索: '{query}' -> {names}")
        return results

    def search_tips(self, query: str, n: int = 5) -> list[dict]:
        results = self.vs.search(query, n_results=n, type_filter="tip")
        if not results:
            data = _load_json_data(settings.TRAVEL_TIPS_DATA)
            for item in data:
                text = item.get("title", "") + item.get("content", "") + item.get("city", "")
                if any(kw in text for kw in query.split() if len(kw) >= 2):
                    results.append(self._tip_from_json(item))
                    if len(results) >= n:
                        break
        titles = [r["metadata"].get("title", "") for r in results]
        logger.info(f"贴士检索: '{query}' -> {titles}")
        return results

    def search_all(self, query: str, n: int = 8) -> dict[str, list[dict]]:
        return {
            "attractions": self.search_attractions(query, n),
            "food": self.search_food(query, n),
            "tips": self.search_tips(query, n),
        }

    def get_attraction_detail(self, name: str) -> dict | None:
        """按名称查找景点（精确匹配优先，支持别名）"""
        if not name:
            return None

        # 方案一：向量检索匹配
        all_attractions = self.vs.search(name, n_results=30, type_filter="attraction")
        for a in all_attractions:
            meta_name = a["metadata"].get("name", "")
            if name in meta_name and len(name) >= 2:
                return a

        # 方案二：JSON 直接查找
        try:
            with open(settings.ATTRACTIONS_DATA, "r", encoding="utf-8") as f:
                attractions_list = json.load(f)

            # 精确匹配
            for item in attractions_list:
                if name == item["name"] or name in item["name"]:
                    return self._attraction_from_json(item)

            # 模糊匹配（连续双字）
            if len(name) >= 2:
                for item in attractions_list:
                    item_name = item["name"]
                    for i in range(len(name) - 1):
                        if name[i:i+2] in item_name:
                            return self._attraction_from_json(item)
        except Exception as e:
            logger.warning(f"JSON直接查找失败: {e}")

        return None

    def get_cuisine_detail(self, name: str) -> dict | None:
        """按名称查找美食（含 JSON 兜底）"""
        results = self.vs.search(name, n_results=10, type_filter="cuisine")
        for r in results:
            if name in r["metadata"].get("name", ""):
                return r
        try:
            with open(settings.CUISINE_DATA, "r", encoding="utf-8") as f:
                cuisines = json.load(f)
            for item in cuisines:
                if name in item["name"] or item["name"] in name:
                    return self._cuisine_from_json(item)
        except:
            pass
        return None

    def get_cities_list(self) -> list[str]:
        """获取知识库中所有城市列表"""
        data = _load_json_data(settings.ATTRACTIONS_DATA)
        cities = set()
        for item in data:
            city = item.get("city", "")
            if city:
                cities.add(city)
        return sorted(c for c in cities if c)
