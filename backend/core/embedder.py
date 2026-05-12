"""
文本向量化引擎
基于 sentence-transformers 实现，提供统一的文本向量化接口
"""
# ==================== 标准库导入 ====================
from typing import List

# ==================== 第三方库导入 ====================
import numpy as np
from sentence_transformers import SentenceTransformer

# ==================== 内部模块导入 ====================
from config.settings import settings
from utils.logger import logger


class Embeder:
    """文本向量化引擎类（懒加载模式）"""

    def __init__(self):
        # 🔥 关键修改：不在 __init__ 中加载模型，改为懒加载
        self._model = None
        self._embedding_dim = None
        logger.info("✅ 向量化引擎初始化完成（模型将在首次使用时加载）")

    @property
    def model(self):
        """懒加载嵌入模型"""
        if self._model is None:
            logger.info(f"🔄 正在加载向量化模型: {settings.EMBEDDING_MODEL_NAME}...")
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_NAME,
                local_files_only=True,
                trust_remote_code=True
            )
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"✅ 向量化模型加载完成，向量维度: {self._embedding_dim}")
        return self._model

    @property
    def embedding_dim(self):
        """获取向量维度（懒加载）"""
        if self._embedding_dim is None:
            _ = self.model  # 触发模型加载
        return self._embedding_dim

    def embed_text(self, text: str) -> np.ndarray:
        """单文本向量化"""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """批量文本向量化"""
        return self.model.encode(texts, convert_to_numpy=True)


# 🔥 关键修改：只创建轻量级实例，不立即加载模型
embeder = Embeder()
