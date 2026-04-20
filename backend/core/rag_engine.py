"""
RAG 核心引擎
实现：文档加载 → 文本分割 → 向量化存储 → 语义检索 → 大模型问答
对接 FAISS 向量库、嵌入模型、智谱大模型
"""
# ==================== 标准库导入 ====================
import os
from typing import List
from pathlib import Path

# ==================== 第三方库导入 ====================
import faiss
import json
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==================== 内部模块导入 ====================
from config.settings import settings
from core.embedder import embeder
from core.llm import llm
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException


class RAGEngine:
    """
    RAG 检索增强生成引擎
    完整流程：
    1. 文档分块 → 2. 向量化 → 3. 存入 FAISS → 4. 用户问题检索 → 5. 大模型生成答案
    """

    def __init__(self):
        """
        初始化 RAG 引擎
        1. 加载 FAISS 索引
        2. 加载文档ID映射表
        3. 自动创建目录
        """
        # 确保向量库目录存在
        os.makedirs(settings.FAISS_DIR, exist_ok=True)

        # 路径配置
        self.index_path = settings.FAISS_INDEX_PATH
        self.doc_map_path = settings.DOC_MAP_PATH

        # FAISS 索引与文档映射
        self.index = None
        self.doc_map = {}  # key: 向量ID, value: 知识点内容/标题等

        # 文本分块器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", " ", ""],
            length_function=len
        )

        # 加载索引
        self._load_index()

    def _load_index(self):
        """
        加载 FAISS 索引和文档映射表
        不存在则初始化空索引
        """
        try:
            # 加载索引
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"✅ 加载 FAISS 索引成功，向量数量：{self.index.ntotal}")
            else:
                self.index = faiss.IndexFlatL2(settings.EMBEDDING_DIM)
                logger.info("✅ 初始化空 FAISS 索引")

            # 加载文档映射
            if self.doc_map_path.exists():
                with open(self.doc_map_path, "r", encoding="utf-8") as f:
                    self.doc_map = json.load(f)
            else:
                self.doc_map = {}

        except Exception as e:
            logger.error(f"❌ 加载向量库失败：{str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.VECTOR_SEARCH_ERROR,
                msg="向量库加载失败"
            )

    def _save_index(self):
        """保存 FAISS 索引 + 文档映射表"""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.doc_map_path, "w", encoding="utf-8") as f:
            json.dump(self.doc_map, f, ensure_ascii=False, indent=2)

    def add_document(self, doc_id: int, title: str, content: str):
        """
        添加单个文档到向量库
        :param doc_id: 文档ID（来自数据库）
        :param title: 标题
        :param content: 文本内容
        """
        try:
            # 1. 文本分块
            chunks = self.text_splitter.split_text(content)
            if not chunks:
                return

            # 2. 向量化
            vectors = embeder.embed_texts(chunks)

            # 3. 添加到 FAISS
            self.index.add(vectors)

            # 4. 记录映射
            for i, chunk in enumerate(chunks):
                vec_id = len(self.doc_map)
                self.doc_map[str(vec_id)] = {
                    "doc_id": doc_id,
                    "title": title,
                    "content": chunk
                }

            # 5. 保存
            self._save_index()
            logger.info(f"✅ 文档 {doc_id} 向量化完成，共 {len(chunks)} 块")

        except Exception as e:
            logger.error(f"❌ 文档向量化失败：{str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.VECTOR_SEARCH_ERROR,
                msg="文档向量化失败"
            )

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """
        语义检索：根据用户问题检索相关知识点
        """
        if self.index.ntotal == 0:
            raise BusinessException(
                code=BusinessErrorCode.KNOWLEDGE_EMPTY,
                msg="知识库暂无内容，请先上传文档"
            )

        try:
            # 1. 问题向量化
            query_vec = embeder.embed_text(query)
            query_vec = np.expand_dims(query_vec, axis=0)

            # 2. FAISS 检索
            distances, indices = self.index.search(query_vec, top_k)

            # 3. 组装结果
            results = []
            for idx in indices[0]:
                if str(idx) in self.doc_map:
                    results.append(self.doc_map[str(idx)])

            return results

        except Exception as e:
            logger.error(f"❌ 向量检索失败：{str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.VECTOR_SEARCH_ERROR,
                msg="向量检索失败"
            )

    def answer(self, query: str) -> str:
        """
        RAG 问答主接口
        检索 + 提示词 + 大模型生成
        """
        # 1. 检索相关知识
        docs = self.search(query)
        if not docs:
            return "未找到相关知识，请尝试更换问题。"

        # 2. 拼接上下文
        context = "\n---\n".join([d["content"] for d in docs])

        # 3. 系统提示词
        system_prompt = f"""
你是一个专业的学习助手，请根据下面提供的知识库内容回答用户问题。
只使用提供的知识，不编造内容。

知识库内容：
{context}
"""

        # 4. 调用大模型
        return llm.chat(user_prompt=query, system_prompt=system_prompt)


# ==================== 全局单例 ====================
rag_engine = RAGEngine()