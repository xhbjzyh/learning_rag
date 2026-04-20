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
    """文本向量化引擎类"""

    def __init__(self):
        logger.info(f"正在加载向量化模型: {settings.EMBEDDING_MODEL_NAME}...")
        # 核心修复：加local_files_only=True，强制只用本地缓存，不访问远程HF
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            local_files_only=True,  # 关键：禁用远程访问，只使用本地缓存
            trust_remote_code=True
        )
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"✅ 向量化模型加载完成，向量维度: {self.embedding_dim}")

    def embed_text(self, text: str) -> np.ndarray:
        """单文本向量化"""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """批量文本向量化"""
        return self.model.encode(texts, convert_to_numpy=True)


# 全局单例
try:
    embeder = Embeder()
except Exception as e:
    logger.error(f"❌ 向量化模型加载失败: {str(e)}")
    raise e