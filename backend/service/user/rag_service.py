"""
用户-RAG问答业务逻辑
支持按用户隔离的向量库（实现真正的私有知识库）
新增：对话上下文记忆 + 流式输出 + 自动记录学习行为
"""
from typing import List, Dict, AsyncGenerator
from sqlalchemy.orm import Session
from collections import defaultdict

from models.db_models import KnowledgePoint, UserLearningRecord
from utils.vector_store import VectorStoreManager, vector_store
from utils.logger import logger
from core.rag_engine import rag_engine

# ==============================================
# 对话记忆管理器
# ==============================================
class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.memory = defaultdict(list)

    def add_message(self, user_id: int, role: str, content: str):
        self.memory[user_id].append({"role": role, "content": content})
        if len(self.memory[user_id]) > self.max_history * 2:
            self.memory[user_id] = self.memory[user_id][-self.max_history * 2:]

    def get_history(self, user_id: int) -> List[Dict]:
        return self.memory[user_id]

    def clear_history(self, user_id: int):
        if user_id in self.memory:
            del self.memory[user_id]

conversation_memory = ConversationMemory(max_history=10)

# ==============================================
# RAG服务核心类
# ==============================================
class RagService:
    @staticmethod
    def sync_point_to_vector(db: Session, point_id: int, user_id: int = None):
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not point:
            logger.warning(f"知识点不存在，无法同步: {point_id}")
            return False

        try:
            if user_id:
                vs = VectorStoreManager(user_id)
                vs.add_knowledge_points([{
                    "id": point.id,
                    "title": point.title,
                    "content": point.content,
                    "difficulty": point.difficulty
                }])
            else:
                vector_store.add_point(
                    point_id=point.id,
                    content=point.content,
                    title=point.title
                )
            return True
        except Exception as e:
            logger.error(f"知识点同步到向量库失败: {point_id}, 错误: {str(e)}")
            return False

    @staticmethod
    def sync_all_points_to_vector(db: Session, user_id: int = None):
        if user_id:
            points = db.query(KnowledgePoint).filter(KnowledgePoint.user_id == user_id).all()
        else:
            points = db.query(KnowledgePoint).all()

        if not points:
            logger.info("没有知识点需要同步")
            return {"total": 0, "success": 0}

        success_count = 0
        if user_id:
            vs = VectorStoreManager(user_id)
            knowledge_points = [{
                "id": point.id,
                "title": point.title,
                "content": point.content,
                "difficulty": point.difficulty
            } for point in points]
            vs.add_knowledge_points(knowledge_points)
            success_count = len(knowledge_points)
        else:
            for point in points:
                try:
                    vector_store.add_point(
                        point_id=point.id,
                        content=point.content,
                        title=point.title
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"知识点同步失败: {point.id}, 错误: {str(e)}")
                    continue

        logger.info(f"全量同步完成，总计: {len(points)}, 成功: {success_count}")
        return {"total": len(points), "success": success_count}

    # ==============================================
    # 🔥 自动记录学习行为（核心方法）
    # ==============================================
    @staticmethod
    def _record_learning(db: Session, user_id: int, point_id: int):
        if not user_id or not point_id or not db:
            logger.warning(f"记录学习参数缺失：user_id={user_id}, point_id={point_id}, db={db}")
            return False

        try:
            # 查重：避免重复记录
            existing = db.query(UserLearningRecord).filter(
                UserLearningRecord.user_id == user_id,
                UserLearningRecord.point_id == point_id
            ).first()

            if existing:
                logger.info(f"用户{user_id} 已学习过知识点{point_id}，跳过记录")
                return False

            # 写入学习记录
            record = UserLearningRecord(
                user_id=user_id,
                point_id=point_id,
                learn_duration=15,
                is_finished=True,
                feedback_score=5,
                is_collected=False
            )
            db.add(record)
            db.commit()
            logger.info(f"✅ 学习记录已保存：用户{user_id} -> 知识点{point_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 学习记录保存失败：{str(e)}")
            db.rollback()
            return False

    # ==============================================
    # 🔥 异步流式问答（终极修复版）
    # ==============================================
    # ==============================================
    # 🔥 异步流式问答（最终最终版）
    # ==============================================
    @staticmethod
    async def chat_stream(
            query: str,
            user_id: int,
            db: Session = None,
            kb_type: str = "private",
            top_k: int = 5,
            clear_history: bool = False
    ) -> AsyncGenerator[str, None]:
        try:
            logger.info(f"🚀 开始流式问答：用户{user_id}，问题={query}")

            # 清除历史对话
            if clear_history:
                conversation_memory.clear_history(user_id)
                yield "✅ 对话历史已清除\n"

            # 1. 检索知识点
            search_results = rag_engine.search(query, user_id, kb_type, top_k)
            logger.info(f"📚 检索到 {len(search_results)} 个知识点")

            # 2. 🔥 调试：打印db状态
            logger.info(f"🔥 数据库会话状态：db={db}")

            # 3. 🔥 强制记录学习（兼容所有字段名，解决核心问题！）
            if search_results and len(search_results) > 0:
                top_point = search_results[0]
                logger.info(f"🔥 检索结果原始数据: {top_point}")  # 打印看字段名

                # 兼容所有可能的ID字段名（id / point_id / knowledge_point_id）
                point_id = (
                        top_point.get("id")
                        or top_point.get("point_id")
                        or top_point.get("knowledge_point_id")
                )
                logger.info(f"🔥 提取到的知识点ID: {point_id}")

                # 只要有ID就记录，没有就打印警告
                if point_id and db:
                    RagService._record_learning(db, user_id, point_id)
                else:
                    logger.warning(f"⚠️ 无法记录学习：ID={point_id}，DB={db}")

            # 4. 获取对话历史
            history = conversation_memory.get_history(user_id)
            conversation_memory.add_message(user_id, "user", query)

            # 5. 调用大模型生成回答
            full_answer = rag_engine.answer(
                query=query,
                user_id=user_id,
                kb_type=kb_type,
                history=history
            )

            # 6. 流式输出
            for char in full_answer:
                yield char

            # 7. 保存对话记忆
            conversation_memory.add_message(user_id, "assistant", full_answer)
            logger.info(f"✅ 用户{user_id} 流式问答完成")

        except Exception as e:
            logger.error(f"❌ 流式问答异常：{str(e)}")
            yield f"❌ 服务异常：{str(e)}"

# 全局单例
rag_service = RagService()