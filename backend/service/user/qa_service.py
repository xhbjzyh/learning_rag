from sqlalchemy.orm import Session
from models.db_models import KnowledgePoint, KnowledgeQaRecord, CourseResource
from models.schemas import KnowledgeQaCreate, KnowledgeQaFeedbackUpdate
from fastapi import HTTPException
from datetime import datetime
import json

# 导入你的大模型调用工具
from core.llm import llm


class UserQaService:
    """
    用户端知识点问答业务逻辑
    """

    async def ask_question(self, db: Session, user_id: int, knowledge_point_id: int, question: str):
        """
        用户提问，调用大模型回答并保存记录
        """
        # 校验知识点是否存在
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
        if not point:
            raise HTTPException(status_code=404, detail="知识点不存在")

        # 1. 构建系统提示词和用户提示词
        system_prompt = """
        你是一个专业的学习助手，请基于用户提供的知识点内容回答问题。
        要求：
        1. 回答必须严格基于提供的知识点内容
        2. 语言简洁明了，通俗易懂
        3. 如果问题超出知识点范围，请明确说明
        4. 回答长度控制在300字以内
        """

        user_prompt = f"""
        知识点标题：{point.title}
        知识点内容：{point.content}
        核心要点：{point.key_points if point.key_points else "无"}
        常见错误：{point.common_mistakes if point.common_mistakes else "无"}

        用户问题：{question}
        """

        # 2. 调用你现有的大模型引擎（带超时控制）
        try:
            # 🔥 修改：使用你现有的llm.chat方法
            answer = await llm.chat(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                timeout=30  # 问答接口设置30秒超时
            )
        except Exception as e:
            # 你的大模型引擎已经抛出了BusinessException，这里直接捕获并重新抛出
            raise HTTPException(status_code=500, detail=str(e))

        # 3. 查询关联的课程资源
        related_resources = db.query(CourseResource).filter(
            CourseResource.knowledge_points.any(id=knowledge_point_id),
            CourseResource.is_published == True
        ).limit(3).all()
        related_resource_ids = json.dumps([r.id for r in related_resources])

        # 4. 创建问答记录
        qa_data = KnowledgeQaCreate(
            knowledge_point_id=knowledge_point_id,
            query=question,
            answer=answer,
            related_resource_ids=related_resource_ids,
            difficulty=point.difficulty,
            is_solved=True,
            follow_up_count=0
        )

        # 调用管理员端服务保存记录并同步掌握度
        from backend.service.admin.course_service import admin_qa_service
        qa_record = admin_qa_service.create_qa_record(db, user_id, qa_data)

        return {
            "qa_record": qa_record,
            "related_resources": related_resources
        }

    def update_feedback(self, db: Session, user_id: int, qa_id: int, data: KnowledgeQaFeedbackUpdate):
        """
        用户对问答结果进行反馈
        """
        # 校验问答记录是否属于该用户
        qa_record = db.query(KnowledgeQaRecord).filter(
            KnowledgeQaRecord.id == qa_id,
            KnowledgeQaRecord.user_id == user_id
        ).first()

        if not qa_record:
            raise HTTPException(status_code=404, detail="问答记录不存在")

        # 调用管理员端服务更新反馈
        from backend.service.admin.course_service import admin_qa_service
        return admin_qa_service.update_qa_feedback(db, qa_id, data)

    def get_user_qa_history(self, db: Session, user_id: int, page: int = 1, size: int = 10):
        """
        获取用户问答历史记录
        """
        from backend.service.admin.course_service import admin_qa_service
        return admin_qa_service.get_user_qa_history(db, user_id, page, size)

    def get_qa_detail(self, db: Session, user_id: int, qa_id: int):
        """
        获取问答详情
        """
        qa_record = db.query(KnowledgeQaRecord).filter(
            KnowledgeQaRecord.id == qa_id,
            KnowledgeQaRecord.user_id == user_id
        ).first()

        if not qa_record:
            raise HTTPException(status_code=404, detail="问答记录不存在")

        # 解析关联资源
        related_resource_ids = []
        if qa_record.related_resource_ids:
            try:
                related_resource_ids = json.loads(qa_record.related_resource_ids)
            except:
                pass

        # 查询关联资源详情
        related_resources = db.query(CourseResource).filter(
            CourseResource.id.in_(related_resource_ids),
            CourseResource.is_published == True
        ).all()

        return {
            "qa_record": qa_record,
            "related_resources": related_resources
        }


# 全局单例
user_qa_service = UserQaService()