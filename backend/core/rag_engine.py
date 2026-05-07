"""
RAG 核心引擎（支持公共/私有知识库切换 + 对话历史）
对接 VectorStoreManager 实现用户隔离
"""
from typing import List
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException
from utils.vector_store import VectorStoreManager, get_global_vector_store
from core.llm import llm

class RAGEngine:
    def __init__(self):
        # 公共知识库固定 user_0
        self.public_vector_store = get_global_vector_store()
        # 当前用户私有库
        self.private_vector_store = None
        self.current_user_id = None

    def init_user_store(self, user_id: int):
        """初始化用户私有向量库"""
        if self.current_user_id != user_id:
            self.private_vector_store = VectorStoreManager(user_id)
            self.current_user_id = user_id

    def get_vector_store(self, user_id: int, kb_type: str = "private"):
        """获取对应向量库：public=公共(user_0) / private=私有"""
        if kb_type == "public":
            return self.public_vector_store
        self.init_user_store(user_id)
        return self.private_vector_store

    def search(self, query: str, user_id: int, kb_type: str = "private", top_k: int = 3) -> List[dict]:
        """检索：支持公共/私有切换"""
        vs = self.get_vector_store(user_id, kb_type)
        results = vs.hybrid_search(query, top_k=top_k)
        return results

    # 🔥 核心修改：添加 history 参数
    def answer(self, query: str, user_id: int, kb_type: str = "private", history: list = None) -> str:
        """
        RAG问答：支持公共/私有切换 + 空库兜底 + 对话历史
        :param query: 用户问题
        :param user_id: 用户ID
        :param kb_type: 知识库类型
        :param history: 对话历史（新增），格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        :return: 回答
        """
        # 1. 检索
        docs = self.search(query, user_id, kb_type, top_k=3)

        # 2. 拼接上下文
        context_text = "\n".join([f"- {item['content']}" for item in docs]) if docs else ""

        # 3. 🔥 构建包含历史对话的提示词
        if history and len(history) > 0:
            # 有历史对话的情况
            system_prompt = f"""
你是专业学习助手，基于知识点和对话历史回答问题，不编造。
参考知识点：
{context_text if context_text else '（无相关知识点）'}

规则：
1. 参考之前的对话历史，保持对话连贯性
2. 如果有知识点，基于知识点回答；如果没有，直接回答
3. 分点作答、专业清晰
"""
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
                return llm.chat(
                    user_prompt=query,
                    system_prompt="你是专业学习助手，直接回答用户问题"
                )

            system_prompt = f"""
你是专业学习助手，基于知识点回答问题，不编造。
参考知识点：
{context_text}
规则：分点作答、专业清晰
"""
            full_user_prompt = query

        # 4. 生成回答
        return llm.chat(user_prompt=full_user_prompt, system_prompt=system_prompt)

# 全局单例
rag_engine = RAGEngine()