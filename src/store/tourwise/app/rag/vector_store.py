"""
向量存储模块 — 基于 ChromaDB 的 RAG 检索
负责文本的索引、存储和语义检索
使用自定义嵌入函数，避免 Chroma 默认 ONNX 模型下载
"""

import json
import logging
import os
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.config import settings as app_settings
from app.rag.embedder import get_embedder

logger = logging.getLogger(__name__)


class _ChromaEmbeddingFunction(EmbeddingFunction):
    """自定义 ChromaDB 嵌入函数，包装我们的 Embedder"""

    def __init__(self, embedder):
        self._embedder = embedder

    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input) if isinstance(input, list) else [input]
        return self._embedder.embed_texts(texts)


class VectorStore:
    """向量数据库封装，提供文旅知识库的语义检索能力"""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or app_settings.CHROMA_PERSIST_DIR
        self.embedder = get_embedder()
        self._ef = _ChromaEmbeddingFunction(self.embedder)
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None

    @property
    def client(self):
        if self._client is None:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_or_create_collection(self):
        """获取或创建集合，使用自定义嵌入函数"""
        return self.client.get_or_create_collection(
            name="tourwise_kb",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self._get_or_create_collection()
        return self._collection

    def index_attractions(self, data_path: str) -> int:
        """索引景点数据到向量库"""
        with open(data_path, "r", encoding="utf-8") as f:
            attractions = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for i, item in enumerate(attractions):
            doc_text = (
                f"景点名称：{item['name']}\n"
                f"所在城市：{item['city']}\n"
                f"类别：{item['category']}\n"
                f"描述：{item['description']}\n"
                f"开放时间：{item['opening_hours']}\n"
                f"门票价格：{item['ticket_price']}\n"
                f"最佳季节：{item['best_season']}\n"
                f"游玩贴士：{item['tips']}\n"
                f"建议时长：{item['duration']}\n"
                f"标签：{'、'.join(item['tags'])}"
            )
            documents.append(doc_text)
            metadatas.append({
                "type": "attraction",
                "name": item["name"],
                "city": item["city"],
                "category": item["category"],
                "rating": item["rating"],
                "price": item["ticket_price"],
            })
            ids.append(f"attraction_{i}")

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"已索引 {len(ids)} 条景点数据")
        return len(ids)

    def index_cuisine(self, data_path: str) -> int:
        """索引美食数据到向量库"""
        with open(data_path, "r", encoding="utf-8") as f:
            cuisines = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for i, item in enumerate(cuisines):
            doc_text = (
                f"美食名称：{item['name']}\n"
                f"所在城市：{item['city']}\n"
                f"类别：{item['category']}\n"
                f"描述：{item['description']}\n"
                f"推荐餐厅：{'；'.join(item['restaurant_recommendations'])}\n"
                f"价格范围：{item['price_range']}\n"
                f"必点推荐：{'、'.join(item['must_try'])}\n"
                f"标签：{'、'.join(item['tags'])}"
            )
            documents.append(doc_text)
            metadatas.append({
                "type": "cuisine",
                "name": item["name"],
                "city": item["city"],
                "category": item["category"],
            })
            ids.append(f"cuisine_{i}")

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"已索引 {len(ids)} 条美食数据")
        return len(ids)

    def index_travel_tips(self, data_path: str) -> int:
        """索引旅行贴士到向量库"""
        with open(data_path, "r", encoding="utf-8") as f:
            tips = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for i, item in enumerate(tips):
            doc_text = (
                f"标题：{item['title']}\n"
                f"类别：{item['category']}\n"
                f"相关城市：{item['city']}\n"
                f"内容：{item['content']}\n"
                f"标签：{'、'.join(item['tags'])}"
            )
            documents.append(doc_text)
            metadatas.append({
                "type": "tip",
                "title": item["title"],
                "category": item["category"],
                "city": item["city"],
            })
            ids.append(f"tip_{i}")

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"已索引 {len(ids)} 条旅行贴士")
        return len(ids)

    def build_all_indexes(self):
        """一键构建全量知识库索引"""
        self._collection = self._get_or_create_collection()
        # 清空重建
        try:
            existing = self.collection.get()
            if existing["ids"]:
                self.collection.delete(existing["ids"])
        except Exception:
            pass

        total = 0
        total += self.index_attractions(app_settings.ATTRACTIONS_DATA)
        total += self.index_cuisine(app_settings.CUISINE_DATA)
        total += self.index_travel_tips(app_settings.TRAVEL_TIPS_DATA)
        logger.info(f"知识库构建完成，共索引 {total} 条数据")
        return total

    def search(self, query: str, n_results: int = 5, type_filter: str = None) -> list[dict]:
        """语义检索知识库

        Args:
            query: 查询文本
            n_results: 返回结果数
            type_filter: 类型过滤 (attraction/cuisine/tip/None)

        Returns:
            检索结果列表，每项含 document, metadata, distance
        """
        where = None
        if type_filter:
            where = {"type": type_filter}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

        items = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                items.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })

        items.sort(key=lambda x: x["distance"])
        return items

    def count(self) -> int:
        """返回知识库文档总数"""
        try:
            return self.collection.count()
        except Exception:
            return 0


_global_vector_store: Optional[VectorStore] = None


def get_vector_store(persist_dir: str = None) -> VectorStore:
    """获取全局向量库单例"""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStore(persist_dir)
    return _global_vector_store
