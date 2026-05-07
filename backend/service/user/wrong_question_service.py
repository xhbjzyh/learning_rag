"""
错题本业务服务
功能：错题列表、移除错题、标记已掌握、更新复习记录
"""
from datetime import datetime
from sqlalchemy.orm import Session

from models.db_models import WrongQuestion
from utils.logger import logger
from utils.response import BusinessException, BusinessErrorCode


class WrongQuestionService:

    def get_wrong_questions(self, db: Session, user_id: int, page: int = 1, size: int = 10):
        """获取用户错题本列表"""
        query = db.query(WrongQuestion).filter(WrongQuestion.user_id == user_id)
        total = query.count()
        questions = query.order_by(WrongQuestion.next_review_time.asc()).offset((page-1)*size).limit(size).all()
        return {"total": total, "list": questions, "page": page, "size": size}

    def mark_mastered(self, db: Session, user_id: int, wrong_id: int):
        """标记错题已掌握"""
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_id,
            WrongQuestion.user_id == user_id
        ).first()

        if not wrong:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "错题不存在")

        wrong.master_level = 2
        wrong.next_review_time = None
        db.commit()
        logger.info(f"用户 {user_id} 标记错题 {wrong_id} 已掌握")
        return {"msg": "标记成功"}

    def remove_wrong_question(self, db: Session, user_id: int, wrong_id: int):
        """从错题本移除"""
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_id,
            WrongQuestion.user_id == user_id
        ).first()

        if not wrong:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "错题不存在")

        db.delete(wrong)
        db.commit()
        logger.info(f"用户 {user_id} 移除错题 {wrong_id}")
        return {"msg": "移除成功"}


wrong_question_service = WrongQuestionService()