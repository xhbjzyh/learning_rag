"""
知识点同步服务
将课程知识点同步到公共知识库，实现统一管理
"""
from sqlalchemy.orm import Session
from typing import List
from models.db_models import CourseKnowledgePoint, KnowledgePoint, Course
from utils.logger import logger


class KnowledgeSyncService:
    """知识点同步服务"""

    def sync_course_to_public(self, db: Session, course_id: int) -> dict:
        """
        将课程的所有知识点同步到公共知识库并建立向量索引
        :param db: 数据库会话
        :param course_id: 课程ID
        :return: 同步结果统计
        """
        # 1. 获取课程的所有知识点（移除is_published过滤，同步所有知识点）
        course_kps = db.query(CourseKnowledgePoint).filter(
            CourseKnowledgePoint.course_id == course_id
        ).all()

        if not course_kps:
            logger.warning(f"课程 {course_id} 没有知识点需要同步")
            return {"synced": 0, "updated": 0, "failed": 0, "vector_synced": 0}

        synced_count = 0
        updated_count = 0
        failed_count = 0
        vector_synced_count = 0

        for course_kp in course_kps:
            try:
                # 2. 检查是否已同步（通过 source_id 关联）
                existing_kp = db.query(KnowledgePoint).filter(
                    KnowledgePoint.source_type == "course",
                    KnowledgePoint.source_id == course_kp.id
                ).first()

                synced_kp = None

                if existing_kp:
                    # 更新现有知识点
                    existing_kp.title = course_kp.title
                    existing_kp.content = course_kp.content
                    existing_kp.key_points = course_kp.key_points
                    existing_kp.difficulty = course_kp.difficulty
                    existing_kp.update_time = None  # 触发自动更新
                    synced_kp = existing_kp
                    updated_count += 1
                    logger.info(f"✅ 更新知识点: {course_kp.title}")
                else:
                    # 创建新知识点
                    new_kp = KnowledgePoint(
                        title=course_kp.title,
                        content=course_kp.content,
                        key_points=course_kp.key_points,
                        difficulty=course_kp.difficulty,
                        source_type="course",
                        source_id=course_kp.id,
                        course_id=course_id,
                        is_published=True
                    )
                    db.add(new_kp)
                    db.flush()  # 🔥 关键修复：立即flush获取ID
                    
                    synced_kp = new_kp
                    synced_count += 1
                    logger.info(f"✅ 同步知识点: {course_kp.title} (ID={new_kp.id})")

                # 🔥 关键修复：同步到向量库（此时synced_kp.id已经有值了）
                if synced_kp and synced_kp.id:
                    try:
                        from service.user.rag_service import rag_service
                        success = rag_service.sync_point_to_vector(db, synced_kp.id)
                        if success:
                            vector_synced_count += 1
                            logger.info(f"✅ 向量库同步成功: {synced_kp.title}")
                        else:
                            logger.warning(f"⚠️ 向量库同步失败: {synced_kp.title}")
                    except Exception as e:
                        logger.error(f"❌ 向量库同步异常: {synced_kp.title}, 错误: {e}")

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ 同步知识点失败: {course_kp.title}, 错误: {e}")
                import traceback
                traceback.print_exc()

        db.commit()

        result = {
            "synced": synced_count,
            "updated": updated_count,
            "failed": failed_count,
            "vector_synced": vector_synced_count,
            "total": len(course_kps)
        }

        logger.info(f"🎉 课程 {course_id} 知识点同步完成: {result}")
        return result

    def sync_all_courses(self, db: Session) -> dict:
        """同步所有课程的知识点"""
        courses = db.query(Course).filter(Course.is_published == True).all()

        total_result = {"synced": 0, "updated": 0, "failed": 0, "vector_synced": 0, "courses": 0}

        for course in courses:
            result = self.sync_course_to_public(db, course.id)
            total_result["synced"] += result["synced"]
            total_result["updated"] += result["updated"]
            total_result["failed"] += result["failed"]
            total_result["vector_synced"] += result.get("vector_synced", 0)
            total_result["courses"] += 1

        return total_result

    def unlink_course_from_public(self, db: Session, course_id: int) -> int:
        """
        取消课程与公共知识库的关联（不删除知识点，只移除关联）
        :return: 解除关联的知识点数量
        """
        kps = db.query(KnowledgePoint).filter(
            KnowledgePoint.source_type == "course",
            KnowledgePoint.course_id == course_id
        ).all()

        count = len(kps)

        for kp in kps:
            # 标记为未发布，但保留数据
            kp.is_published = False

        db.commit()
        logger.info(f"课程 {course_id} 已解除与公共知识库的关联，共 {count} 个知识点")
        return count


# 导出单例
knowledge_sync_service = KnowledgeSyncService()
