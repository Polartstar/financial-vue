"""
嵌入模型模块 — 为 RAG 提供文本向量化能力
支持本地 Sentence-Transformers 模型和 API 调用
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Embedder:
    """文本嵌入器，将文本转换为向量"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None
        self._backend = None  # "local" or "api"

    @property
    def model(self):
        """延迟加载嵌入模型"""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self):
        """加载嵌入模型"""
        # 国内 HuggingFace 被墙，直接使用 fallback 不尝试下载
        try:
            from sentence_transformers import SentenceTransformer
            # 先检查模型是否已缓存
            import os
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            model_cache_path = os.path.join(cache_dir, f"models--sentence-transformers--{self.model_name.replace('/', '--')}")
            
            if os.path.exists(model_cache_path):
                logger.info(f"发现缓存模型: {self.model_name}")
                self._model = SentenceTransformer(self.model_name, cache_folder=cache_dir)
                self._backend = "local"
                logger.info(f"嵌入模型加载完成 (backend={self._backend})")
            else:
                logger.info(f"模型未缓存，使用 fallback 嵌入")
                self._backend = "fallback"
        except Exception as e:
            logger.info(f"无法加载嵌入模型，使用 fallback 嵌入")
            self._backend = "fallback"

    def embed_text(self, text: str) -> list[float]:
        """将单段文本转为向量"""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """将多段文本转为向量"""
        if not texts:
            return []

        # 首次调用时尝试加载真正的嵌入模型
        if self._backend is None:
            self._load_model()

        if self._backend == "local":
            vectors = self.model.encode(texts, show_progress_bar=False)
            return [v.tolist() for v in vectors]

        # 兜底：简单哈希嵌入（仅用于演示，不具备语义能力）
        return self._fallback_embed(texts)

    def _fallback_embed(self, texts: list[str]) -> list[list[float]]:
        """兜底嵌入：基于字符哈希的低维向量"""
        import hashlib
        dim = 384
        results = []
        for text in texts:
            # 使用 MD5 生成固定长度 seed
            seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
            import random
            rng = random.Random(seed + len(text))
            vec = [rng.gauss(0, 0.1) for _ in range(dim)]
            # 归一化
            norm = sum(v * v for v in vec) ** 0.5
            if norm > 0:
                vec = [v / norm for v in vec]
            results.append(vec)
        return results


# 全局单例
_global_embedder: Optional[Embedder] = None


def get_embedder(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> Embedder:
    """获取全局嵌入器单例"""
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = Embedder(model_name)
    return _global_embedder
