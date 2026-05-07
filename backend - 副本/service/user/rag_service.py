"""
用户-RAG问答业务逻辑
"""
from typing import List, Dict
from sqlalchemy.orm import Session

from models.db_models import KnowledgePoint
from utils.vector_store import vector_store
from utils.logger import logger


class RagService:
    """RAG服务类"""

    @staticmethod
    def sync_point_to_vector(db: Session, point_id: int):
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not point:
            logger.warning(f"知识点不存在，无法同步: {point_id}")
            return False

        try:
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
    def sync_all_points_to_vector(db: Session):
        points = db.query(KnowledgePoint).all()
        if not points:
            logger.info("没有知识点需要同步")
            return {"total": 0, "success": 0}

        success_count = 0
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

    @staticmethod
    def search_knowledge(query: str, top_k: int = 5) -> List[Dict]:
        try:
            results = vector_store.search(query, top_k)
            return results
        except Exception as e:
            logger.error(f"检索失败: {query}, 错误: {str(e)}")
            raise Exception("检索服务暂时不可用")


rag_service = RagService()