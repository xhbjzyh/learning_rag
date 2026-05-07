"""
向量数据库工具
基于FAISS实现向量存储和相似度检索
支持按用户隔离的向量库（实现真正的私有知识库）
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import json
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
from utils.logger import logger
from config import settings

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("FAISS未安装，向量检索功能不可用")
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers未安装，向量化功能不可用")
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class VectorStoreManager:
    """向量存储管理器（按用户隔离）"""

    def __init__(self, user_id: int):
        """
        初始化用户专属的向量存储
        :param user_id: 用户ID，实现向量库隔离
        """
        self.user_id = user_id

        # 用户专属的向量库路径
        self.user_faiss_dir = settings.FAISS_DIR / f"user_{user_id}"
        os.makedirs(self.user_faiss_dir, exist_ok=True)

        self.index_path = self.user_faiss_dir / "rag_index.faiss"
        self.doc_map_path = self.user_faiss_dir / "doc_id_map.json"

        # 初始化索引和映射
        self.index = None
        self.doc_map = {}  # {vector_id: {"point_id": int, "content": str, "title": str}}
        self.next_id = 0

        # 加载已有数据
        self._load_index()
        self._load_doc_map()

        # 初始化嵌入模型（懒加载）
        self._model = None

    @property
    def model(self):
        """懒加载嵌入模型（全局共享，避免重复加载）"""
        if not hasattr(VectorStoreManager, '_global_model'):
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info(f"正在加载嵌入模型: {settings.EMBEDDING_MODEL_NAME}")
                VectorStoreManager._global_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info("嵌入模型加载完成")
            else:
                VectorStoreManager._global_model = None
        return VectorStoreManager._global_model

    def _load_index(self):
        """加载FAISS索引"""
        if not FAISS_AVAILABLE:
            return

        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(str(self.index_path))
                self.next_id = self.index.ntotal
                logger.info(f"用户 {self.user_id} FAISS索引加载成功，共 {self.next_id} 个向量")
            except Exception as e:
                logger.error(f"用户 {self.user_id} FAISS索引加载失败: {str(e)}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """创建新的FAISS索引"""
        if not FAISS_AVAILABLE:
            return

        dimension = settings.EMBEDDING_DIM
        self.index = faiss.IndexFlatL2(dimension)
        self.next_id = 0
        logger.info(f"用户 {self.user_id} 创建新的FAISS索引，维度: {dimension}")

    def _save_index(self):
        """保存FAISS索引到磁盘"""
        if not FAISS_AVAILABLE or self.index is None:
            return

        try:
            faiss.write_index(self.index, str(self.index_path))
            logger.info(f"用户 {self.user_id} FAISS索引保存成功，共 {self.index.ntotal} 个向量")
        except Exception as e:
            logger.error(f"用户 {self.user_id} FAISS索引保存失败: {str(e)}")

    def _load_doc_map(self):
        """加载文档ID映射"""
        if os.path.exists(self.doc_map_path):
            try:
                with open(self.doc_map_path, "r", encoding="utf-8") as f:
                    self.doc_map = json.load(f)
                # 转换key为int
                self.doc_map = {int(k): v for k, v in self.doc_map.items()}
                logger.info(f"用户 {self.user_id} 文档映射加载成功，共 {len(self.doc_map)} 条记录")
            except Exception as e:
                logger.error(f"用户 {self.user_id} 文档映射加载失败: {str(e)}")
                self.doc_map = {}

    def _save_doc_map(self):
        """保存文档ID映射到磁盘"""
        try:
            # 转换key为str以便JSON序列化
            str_key_map = {str(k): v for k, v in self.doc_map.items()}
            with open(self.doc_map_path, "w", encoding="utf-8") as f:
                json.dump(str_key_map, f, ensure_ascii=False, indent=2)
            logger.info(f"用户 {self.user_id} 文档映射保存成功，共 {len(self.doc_map)} 条记录")
        except Exception as e:
            logger.error(f"用户 {self.user_id} 文档映射保存失败: {str(e)}")

    def get_embedding(self, text: str) -> np.ndarray:
        """
        获取文本的向量嵌入
        :param text: 输入文本
        :return: 向量数组
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
            raise Exception("sentence-transformers未安装，无法生成向量")

        # 生成向量
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.reshape(1, -1)

    def add_knowledge_points(self, knowledge_points: List[Dict]):
        """
        批量添加知识点到向量库
        :param knowledge_points: 知识点列表，每个元素包含 id, title, content, difficulty
        """
        if not FAISS_AVAILABLE:
            raise Exception("FAISS未安装，无法添加向量")

        added_count = 0
        for kp in knowledge_points:
            point_id = kp["id"]

            # 防重复：检查是否已存在
            exists = False
            for info in self.doc_map.values():
                if info["point_id"] == point_id:
                    exists = True
                    break
            if exists:
                continue

            # 构建向量化文本
            full_text = f"{kp['title']}\n\n{kp['content']}"

            # 生成向量
            embedding = self.get_embedding(full_text)

            # 添加到索引
            vector_id = self.next_id
            self.index.add(embedding)
            self.next_id += 1

            # 更新映射
            self.doc_map[vector_id] = {
                "point_id": point_id,
                "title": kp["title"],
                "content": kp["content"],
                "difficulty": kp.get("difficulty", "中等")
            }
            added_count += 1

        # 批量保存
        if added_count > 0:
            self._save_index()
            self._save_doc_map()
            logger.info(f"用户 {self.user_id} 批量添加 {added_count} 个知识点到向量库")

    def hybrid_search(self, query: str, top_k: int = 5, difficulty: str = None) -> List[Dict]:
        """
        混合检索：语义检索 + 难度过滤
        :param query: 查询文本
        :param top_k: 返回数量
        :param difficulty: 难度过滤（简单/中等/困难）
        :return: 检索结果列表
        """
        if not FAISS_AVAILABLE or self.index is None or self.index.ntotal == 0:
            logger.warning(f"用户 {self.user_id} 向量库为空或未初始化")
            return []

        # 生成查询向量
        query_embedding = self.get_embedding(query)

        # 检索（多返回一些，用于过滤）
        distances, indices = self.index.search(query_embedding, top_k * 2)

        # 整理结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx not in self.doc_map:
                continue

            doc_info = self.doc_map[idx]

            # 难度过滤
            if difficulty and doc_info.get("difficulty") != difficulty:
                continue

            results.append({
                "point_id": doc_info["point_id"],
                "title": doc_info["title"],
                "content": doc_info["content"],
                "difficulty": doc_info.get("difficulty", "中等"),
                "distance": float(distances[0][i]),
                "similarity": float(1.0 / (1.0 + distances[0][i]))
            })

        # 按相似度排序，取前top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:top_k]

        logger.info(f"用户 {self.user_id} 检索完成，查询: {query[:50]}..., 返回 {len(results)} 个结果")
        return results

    def delete_by_point_id(self, point_id: int):
        """
        根据知识点ID删除向量
        :param point_id: 知识点ID
        """
        # 找到对应的vector_id
        to_delete = [vid for vid, info in self.doc_map.items() if info["point_id"] == point_id]

        for vid in to_delete:
            if vid in self.doc_map:
                del self.doc_map[vid]

        self._save_doc_map()
        logger.info(f"用户 {self.user_id} 已从映射中删除知识点，point_id: {point_id}")


# ==================== 向后兼容：保留旧的全局单例接口 ====================
# 为了不修改现有代码，这里创建一个默认的全局实例
# 注意：新代码应该使用 VectorStoreManager(user_id) 来实现用户隔离
_global_vector_store = None

def get_global_vector_store():
    """获取全局向量存储实例（向后兼容）"""
    global _global_vector_store
    if _global_vector_store is None:
        # 默认使用用户ID 0 作为全局实例
        _global_vector_store = VectorStoreManager(user_id=0)
    return _global_vector_store

# 保留旧的导入名称
vector_store = get_global_vector_store()