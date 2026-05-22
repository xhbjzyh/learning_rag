"""
RAG 核心引擎（支持公共/私有知识库切换 + 对话历史 + 动态配置 + 统一知识库）
对接 VectorStoreManager 实现用户隔离
"""
from typing import List, Dict
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException
from utils.vector_store import VectorStoreManager, get_global_vector_store
from core.llm import llm
from core.embedder import embeder
import numpy as np


class RAGEngine:
    def __init__(self):
        # 🔥 关键修改：不在 __init__ 中初始化，改为懒加载
        self._public_vector_store = None
        self._private_vector_store = None
        self.current_user_id = None
        
        # 🔥 RAG配置缓存（默认值）
        self._config_cache = {
            "top_k": 5,
            "similarity_threshold": 0.7,
            "max_context_length": 4000,
            "batch_size": 32,
            "include_course_knowledge": True,  # 🔥 新增：是否包含课程知识点
            # 🔥 Prompt模板配置（从数据库动态加载）
            "prompt_system_with_history": (
                "你是专业学习助手，基于知识点和对话历史回答问题，不编造。\n"
                "参考知识点：\n{context_text}\n\n"
                "规则：\n"
                "1. 参考之前的对话历史，保持对话连贯性\n"
                "2. 如果有知识点，基于知识点回答；如果没有，直接回答\n"
                "3. 分点作答、专业清晰"
            ),
            "prompt_system_without_history": (
                "你是专业学习助手，基于知识点回答问题，不编造。\n"
                "参考知识点：\n{context_text}\n"
                "规则：分点作答、专业清晰"
            ),
            "prompt_fallback": "你是专业学习助手，直接回答用户问题"
        }
        
        logger.info("✅ RAG引擎初始化完成（向量库将在首次使用时加载）")

    def _load_config_from_db(self):
        """🔥 从数据库加载RAG配置（包括Prompt模板）"""
        try:
            from db.sqlite_conn import SessionLocal
            from service.admin.system_config_service import system_config_service
            
            db = SessionLocal()
            
            # 加载基础配置
            top_k = system_config_service.get_config_value(db, "rag.top_k", "5")
            threshold = system_config_service.get_config_value(db, "rag.similarity_threshold", "0.7")
            max_context = system_config_service.get_config_value(db, "rag.max_context_length", "4000")
            batch_size = system_config_service.get_config_value(db, "embedding.batch_size", "32")
            include_course = system_config_service.get_config_value(db, "rag.include_course_knowledge", "true")
            
            # 🔥 加载Prompt模板配置（论文4.2.2节）
            prompt_with_history = system_config_service.get_config_value(
                db, 
                "rag.prompt.system_with_history"
            )
            prompt_without_history = system_config_service.get_config_value(
                db, 
                "rag.prompt.system_without_history"
            )
            prompt_fallback = system_config_service.get_config_value(
                db, 
                "rag.prompt.fallback"
            )
            
            # 更新缓存
            self._config_cache["top_k"] = int(top_k) if top_k.isdigit() else 5
            self._config_cache["similarity_threshold"] = float(threshold) if threshold.replace('.', '').isdigit() else 0.7
            self._config_cache["max_context_length"] = int(max_context) if max_context.isdigit() else 4000
            self._config_cache["batch_size"] = int(batch_size) if batch_size.isdigit() else 32
            self._config_cache["include_course_knowledge"] = include_course.lower() == "true"
            
            # 🔥 更新Prompt模板（如果数据库中有配置）
            if prompt_with_history:
                self._config_cache["prompt_system_with_history"] = prompt_with_history
            if prompt_without_history:
                self._config_cache["prompt_system_without_history"] = prompt_without_history
            if prompt_fallback:
                self._config_cache["prompt_fallback"] = prompt_fallback
            
            logger.info(f"📦 RAG配置已加载: top_k={self._config_cache['top_k']}, threshold={self._config_cache['similarity_threshold']}, include_course={self._config_cache['include_course_knowledge']}")
            logger.info(f"📝 Prompt模板已加载: {len(prompt_with_history or '')}字符（有历史）, {len(prompt_without_history or '')}字符（无历史）")
            db.close()
        except Exception as e:
            logger.warning(f"⚠️ 从数据库加载RAG配置失败，使用默认值: {str(e)}")

    @property
    def public_vector_store(self):
        """懒加载公共知识库"""
        if self._public_vector_store is None:
            logger.info("🔄 首次使用公共知识库，正在初始化...")
            self._public_vector_store = get_global_vector_store()
        return self._public_vector_store

    def init_user_store(self, user_id: int):
        """初始化用户私有向量库"""
        if self.current_user_id != user_id:
            logger.info(f"🔄 首次为用户 {user_id} 初始化私有知识库...")
            self._private_vector_store = VectorStoreManager(user_id)
            self.current_user_id = user_id

    def get_vector_store(self, user_id: int, kb_type: str = "private"):
        """获取对应向量库：public=公共(user_0) / private=私有"""
        if kb_type == "public":
            return self.public_vector_store
        self.init_user_store(user_id)
        return self._private_vector_store

    def add_document(self, doc_id: int, title: str, content: str, user_id: int = 0, kb_type: str = "public"):
        """
        添加单个文档到向量库
        :param doc_id: 文档ID（来自数据库）
        :param title: 标题
        :param content: 文本内容
        :param user_id: 用户ID，默认为0（公共知识库）
        :param kb_type: 知识库类型，默认为"public"
        """
        try:
            vs = self.get_vector_store(user_id, kb_type)
            
            # 构建知识点数据
            knowledge_point = {
                "id": doc_id,
                "title": title,
                "content": content,
                "difficulty": "中等"  # 默认难度
            }
            
            # 添加到向量库
            vs.add_knowledge_points([knowledge_point])
            logger.info(f"✅ 文档 {doc_id} 已添加到{kb_type}知识库")
            
        except Exception as e:
            logger.error(f"❌ 文档向量化失败：{str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.VECTOR_SEARCH_ERROR,
                msg="文档向量化失败"
            )

    def search(self, query: str, user_id: int, kb_type: str = "private", top_k: int = None, include_course: bool = None) -> List[dict]:
        """检索：支持缓存优化"""
        # 🔥 生成缓存key
        cache_key = f"rag:search:{user_id}:{kb_type}:{query[:50]}:{top_k}"
        
        # 尝试从缓存获取
        from utils.cache import cache_service
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"✅ 缓存命中: {cache_key}")
            return cached_result
        
        # 🔥 如果没有指定top_k，使用配置中的值
        if top_k is None:
            self._load_config_from_db()
            top_k = self._config_cache["top_k"]
        
        # 🔥 确定是否包含课程知识点
        if include_course is None:
            include_course = self._config_cache.get("include_course_knowledge", True)
        
        vs = self.get_vector_store(user_id, kb_type)
        
        # 🔥 执行搜索
        if kb_type == "public":
            # 🔥 关键修复：公共知识库也使用FAISS向量库
            results = vs.hybrid_search(query, top_k=top_k)
            
            # 如果向量库为空，降级到数据库混合搜索
            if not results and vs.index.ntotal == 0:
                logger.warning("⚠️ 公共向量库为空，降级到数据库混合搜索")
                results = self._hybrid_public_search(query, top_k, include_course)
        else:
            results = vs.hybrid_search(query, top_k=top_k)
        
        # 🔥 应用相似度阈值过滤
        threshold = self._config_cache["similarity_threshold"]
        filtered_results = [r for r in results if r.get('score', 0) >= threshold]
        
        # 🔥 写入缓存（5分钟）
        cache_service.set(cache_key, filtered_results, ttl=300)
        
        logger.info(f"🔍 检索结果: 原始{len(results)}条, 过滤后{len(filtered_results)}条")
        return filtered_results
    
    def _hybrid_public_search(self, query: str, top_k: int, include_course: bool) -> List[dict]:
        """
        🔥 混合搜索公共知识库（公共 + 课程知识点）- 降级方案
        仅在向量库为空时使用
        """
        from db.sqlite_conn import SessionLocal
        from models.db_models import KnowledgePoint
        from sklearn.metrics.pairwise import cosine_similarity
        
        db = SessionLocal()
        
        try:
            # 1. 生成查询向量
            query_embedding = embeder.encode_query(query)
            
            # 2. 构建查询条件
            filters = [KnowledgePoint.is_published == True]
            
            if not include_course:
                # 仅搜索公共知识点
                filters.append(KnowledgePoint.source_type == "public")
            # 如果 include_course=True，则搜索所有知识点（公共 + 课程）
            
            # 3. 从数据库获取候选知识点
            candidate_points = db.query(KnowledgePoint).filter(*filters).all()
            
            if not candidate_points:
                logger.warning("⚠️ 未找到任何知识点")
                return []
            
            # 4. 计算相似度并排序
            results = []
            for point in candidate_points:
                # 获取知识点的向量（假设已存储在向量库中）
                # 这里简化处理，实际应该从向量库中检索
                point_embedding = embeder.encode_query(point.content[:500])  # 取前500字符
                
                # 计算余弦相似度
                similarity = cosine_similarity(
                    [query_embedding],
                    [point_embedding]
                )[0][0]
                
                results.append({
                    "id": point.id,
                    "title": point.title,
                    "content": point.content,
                    "source_type": point.source_type,
                    "course_id": point.course_id,
                    "score": float(similarity)
                })
            
            # 5. 按相似度排序，返回top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        finally:
            db.close()

    # 🔥 核心修改：添加 history 参数
    async def answer(self, query: str, user_id: int, kb_type: str = "private", history: list = None, include_course: bool = None) -> str:
        """
        RAG问答：支持公共/私有切换 + 空库兜底 + 对话历史 + 动态配置 + 统一知识库
        
        🔥 论文4.2.2节实现：Prompt模板从system_config表动态读取
        
        :param query: 用户问题
        :param user_id: 用户ID
        :param kb_type: 知识库类型
        :param history: 对话历史（新增），格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        :param include_course: 是否包含课程知识点（None时使用配置）
        :return: 回答
        """
        # 🔥 加载配置（包括Prompt模板）
        self._load_config_from_db()
        top_k = self._config_cache["top_k"]
        max_context = self._config_cache["max_context_length"]
        
        # 🔥 获取Prompt模板
        prompt_with_history = self._config_cache["prompt_system_with_history"]
        prompt_without_history = self._config_cache["prompt_system_without_history"]
        prompt_fallback = self._config_cache["prompt_fallback"]
        
        # 1. 检索
        docs = self.search(query, user_id, kb_type, top_k=top_k, include_course=include_course)

        # 2. 拼接上下文（限制长度）
        context_text = "\n".join([f"- {item['content']}" for item in docs]) if docs else ""
        
        # 🔥 截断过长的上下文
        if len(context_text) > max_context:
            context_text = context_text[:max_context] + "...\n(内容过长，已截断)"

        # 3. 🔥 构建包含历史对话的提示词（使用动态模板）
        if history and len(history) > 0:
            # 有历史对话的情况
            system_prompt = prompt_with_history.format(context_text=context_text if context_text else "（无相关知识点）")
            
            # 🔥 将历史对话转换为字符串格式
            history_text = "\n".join([
                f"{'用户' if item['role'] == 'user' else '助手'}：{item['content']}"
                for item in history
            ])

            # 构建完整的 user_prompt
            full_user_prompt = f"""
对话历史：
{history_text}

当前问题：{query}
"""
        else:
            # 没有历史对话的情况（保持原有逻辑）
            if not docs:
                logger.warning(f"{kb_type}知识库为空，使用纯大模型兜底")
                return await llm.chat(
                    user_prompt=query,
                    system_prompt=prompt_fallback
                )

            system_prompt = prompt_without_history.format(context_text=context_text)
            full_user_prompt = query

        # 4. 生成回答
        return await llm.chat(user_prompt=full_user_prompt, system_prompt=system_prompt)

    def reload_config(self):
        """🔥 重新加载配置（管理员修改配置后调用）"""
        self._load_config_from_db()
        logger.info("🔄 RAG配置已重新加载")


# 🔥 关键修改：只创建轻量级实例，不立即加载向量库
rag_engine = RAGEngine()
