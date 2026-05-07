"""
向量数据库工具
基于FAISS实现向量存储和相似度检索
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
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


class VectorStore:
    """向量存储管理器"""

    def __init__(self):
        """初始化向量存储"""
        # 确保目录存在
        self.faiss_dir = settings.FAISS_DIR
        os.makedirs(self.faiss_dir, exist_ok=True)

        self.index_path = settings.FAISS_INDEX_PATH
        self.doc_map_path = settings.DOC_MAP_PATH

        # 初始化索引和映射
        self.index = None
        self.doc_map = {}  # {vector_id: {"point_id": int, "content": str}}
        self.next_id = 0

        # 加载已有数据
        self._load_index()
        self._load_doc_map()

        # 初始化嵌入模型（懒加载）
        self._model = None

    @property
    def model(self):
        """懒加载嵌入模型"""
        if self._model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info(f"正在加载嵌入模型: {settings.EMBEDDING_MODEL_NAME}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("嵌入模型加载完成")
        return self._model

    def _load_index(self):
        """加载FAISS索引"""
        if not FAISS_AVAILABLE:
            return

        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(str(self.index_path))
                self.next_id = self.index.ntotal
                logger.info(f"FAISS索引加载成功，共 {self.next_id} 个向量")
            except Exception as e:
                logger.error(f"FAISS索引加载失败: {str(e)}")
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
        logger.info(f"创建新的FAISS索引，维度: {dimension}")

    def _save_index(self):
        """保存FAISS索引到磁盘"""
        if not FAISS_AVAILABLE or self.index is None:
            return

        try:
            faiss.write_index(self.index, str(self.index_path))
            logger.info(f"FAISS索引保存成功，共 {self.index.ntotal} 个向量")
        except Exception as e:
            logger.error(f"FAISS索引保存失败: {str(e)}")

    def _load_doc_map(self):
        """加载文档ID映射"""
        if os.path.exists(self.doc_map_path):
            try:
                with open(self.doc_map_path, "r", encoding="utf-8") as f:
                    self.doc_map = json.load(f)
                # 转换key为int
                self.doc_map = {int(k): v for k, v in self.doc_map.items()}
                logger.info(f"文档映射加载成功，共 {len(self.doc_map)} 条记录")
            except Exception as e:
                logger.error(f"文档映射加载失败: {str(e)}")
                self.doc_map = {}

    def _save_doc_map(self):
        """保存文档ID映射到磁盘"""
        try:
            # 转换key为str以便JSON序列化
            str_key_map = {str(k): v for k, v in self.doc_map.items()}
            with open(self.doc_map_path, "w", encoding="utf-8") as f:
                json.dump(str_key_map, f, ensure_ascii=False, indent=2)
            logger.info(f"文档映射保存成功，共 {len(self.doc_map)} 条记录")
        except Exception as e:
            logger.error(f"文档映射保存失败: {str(e)}")

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

    def add_point(self, point_id: int, content: str, title: Optional[str] = None) -> int:
        """
        添加知识点到向量库（防重复版）
        """
        # ===================== 防重复核心 =====================
        # 检查这个知识点是否已经在向量库里了
        for vid, info in self.doc_map.items():
            if info["point_id"] == point_id:
                logger.info(f"✅ 知识点已存在，跳过重复添加 | point_id={point_id}")
                return vid  # 直接返回已存在的ID
        # ======================================================

        if not FAISS_AVAILABLE:
            raise Exception("FAISS未安装，无法添加向量")

        full_text = f"{title}\n{content}" if title else content
        embedding = self.get_embedding(full_text)

        vector_id = self.next_id
        self.index.add(embedding)
        self.next_id += 1

        self.doc_map[vector_id] = {
            "point_id": point_id,
            "content": content,
            "title": title
        }

        self._save_index()
        self._save_doc_map()

        logger.info(f"✅ 知识点添加到向量库 | point_id={point_id}, vector_id={vector_id}")
        return vector_id

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        相似度检索
        :param query: 查询文本
        :param top_k: 返回最相似的top_k个结果
        :return: 检索结果列表，按相似度排序
        """
        if not FAISS_AVAILABLE or self.index is None or self.index.ntotal == 0:
            logger.warning("向量库为空或未初始化")
            return []

        # 生成查询向量
        query_embedding = self.get_embedding(query)

        # 检索
        distances, indices = self.index.search(query_embedding, top_k)

        # 整理结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx not in self.doc_map:
                continue

            doc_info = self.doc_map[idx]
            results.append({
                "point_id": doc_info["point_id"],
                "title": doc_info.get("title", ""),
                "content": doc_info["content"],
                "distance": float(distances[0][i]),
                "similarity": float(1.0 / (1.0 + distances[0][i]))  # 转换为相似度分数
            })

        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)

        logger.info(f"检索完成，查询: {query[:50]}..., 返回 {len(results)} 个结果")
        return results

    def delete_by_point_id(self, point_id: int):
        """
        根据知识点ID删除向量（FAISS不支持直接删除，这里只删除映射）
        :param point_id: 知识点ID
        """
        # 找到对应的vector_id
        to_delete = [vid for vid, info in self.doc_map.items() if info["point_id"] == point_id]

        for vid in to_delete:
            if vid in self.doc_map:
                del self.doc_map[vid]

        self._save_doc_map()
        logger.info(f"已从映射中删除知识点，point_id: {point_id}")


# 全局单例
vector_store = VectorStore()