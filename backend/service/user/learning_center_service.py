"""
用户-学习中心业务逻辑
新增：错题本管理、学习进度统计
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from models.db_models import (
    UserLearningRecord, KnowledgePoint, WrongQuestion, LearningProgress, UserProfile
)
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class LearningCenterService:
    """学习中心服务类"""

    # ... 保留原有 add_learning_record 和 get_user_learn_history 方法 ...

    # ==================== 错题本管理 ====================
    @staticmethod
    def add_wrong_question(
        db: Session,
        user_id: int,
        point_id: int,
        question: str,
        user_answer: str,
        correct_answer: str,
        error_reason: Optional[str] = None
    ):
        """
        添加错题记录
        """
        # 1. 校验知识点
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not point:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="知识点不存在"
            )

        # 2. 检查是否已有该错题
        exist_wrong = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.point_id == point_id
        ).first()

        if exist_wrong:
            # 更新错误次数和掌握程度
            exist_wrong.wrong_count += 1
            exist_wrong.master_level = 0
            exist_wrong.user_answer = user_answer
            exist_wrong.error_reason = error_reason
            exist_wrong.last_review_time = func.now()
            # 下次复习时间：1天后（艾宾浩斯遗忘曲线）
            exist_wrong.next_review_time = func.now() + timedelta(days=1)
            db.commit()
            logger.info(f"用户{user_id}错题记录更新，知识点ID: {point_id}")
            return exist_wrong
        else:
            # 创建新错题记录
            new_wrong = WrongQuestion(
                user_id=user_id,
                point_id=point_id,
                question=question,
                user_answer=user_answer,
                correct_answer=correct_answer,
                error_reason=error_reason,
                next_review_time=func.now() + timedelta(days=1)
            )
            db.add(new_wrong)
            db.commit()
            db.refresh(new_wrong)
            logger.info(f"用户{user_id}添加错题记录，知识点ID: {point_id}")
            return new_wrong

    @staticmethod
    def get_wrong_question_list(
        db: Session,
        user_id: int,
        master_level: Optional[int] = None,
        page: int = 1,
        size: int = 10
    ):
        """
        获取错题列表
        """
        query = db.query(WrongQuestion).filter(WrongQuestion.user_id == user_id)

        if master_level is not None:
            query = query.filter(WrongQuestion.master_level == master_level)

        total = query.count()
        wrong_questions = query.order_by(WrongQuestion.next_review_time.asc()).offset((page-1)*size).limit(size).all()

        result = []
        for wq in wrong_questions:
            point = db.query(KnowledgePoint).filter(KnowledgePoint.id == wq.point_id).first()
            result.append({
                "id": wq.id,
                "point_id": wq.point_id,
                "point_title": point.title if point else "知识点已删除",
                "question": wq.question,
                "user_answer": wq.user_answer,
                "correct_answer": wq.correct_answer,
                "error_reason": wq.error_reason,
                "master_level": wq.master_level,
                "wrong_count": wq.wrong_count,
                "next_review_time": wq.next_review_time.strftime("%Y-%m-%d %H:%M:%S") if wq.next_review_time else ""
            })

        return {"total": total, "items": result, "page": page, "size": size}

    @staticmethod
    def update_wrong_question_mastery(
        db: Session,
        user_id: int,
        wrong_id: int,
        master_level: int
    ):
        """
        更新错题掌握程度
        master_level: 0=未掌握，1=部分掌握，2=已掌握
        """
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_id,
            WrongQuestion.user_id == user_id
        ).first()

        if not wrong:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="错题记录不存在"
            )

        wrong.master_level = master_level
        wrong.last_review_time = func.now()

        # 根据掌握程度设置下次复习时间
        if master_level == 0:
            wrong.next_review_time = func.now() + timedelta(days=1)
        elif master_level == 1:
            wrong.next_review_time = func.now() + timedelta(days=3)
        else:
            wrong.next_review_time = None  # 已掌握，不需要复习

        db.commit()
        logger.info(f"用户{user_id}更新错题掌握程度，错题ID: {wrong_id}, 掌握程度: {master_level}")
        return wrong

    # ==================== 学习进度管理 ====================
    @staticmethod
    def update_learning_progress(
        db: Session,
        user_id: int,
        point_id: int,
        progress: float,
        study_duration: int
    ):
        """
        更新学习进度
        """
        # 1. 校验知识点
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not point:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="知识点不存在"
            )

        # 2. 检查是否已有进度记录
        progress_record = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.point_id == point_id
        ).first()

        if progress_record:
            # 更新进度
            progress_record.progress = min(progress, 100.0)
            progress_record.study_duration += study_duration
            progress_record.last_study_time = func.now()
            progress_record.is_finished = progress >= 100.0
        else:
            # 创建新进度记录
            progress_record = LearningProgress(
                user_id=user_id,
                point_id=point_id,
                progress=min(progress, 100.0),
                study_duration=study_duration,
                is_finished=progress >= 100.0
            )
            db.add(progress_record)

        # 3. 更新用户画像总学习时长
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if user_profile:
            user_profile.total_study_duration += study_duration
            if progress >= 100.0 and not progress_record.is_finished:
                user_profile.finished_points_count += 1

        db.commit()
        logger.info(f"用户{user_id}更新学习进度，知识点ID: {point_id}, 进度: {progress}%")
        return progress_record

    @staticmethod
    def get_user_learning_stats(db: Session, user_id: int):
        """
        获取用户学习统计数据
        🔥 修复：从 user_resource_progress 表读取视频/文档学习时长
        """
        from models.db_models import UserResourceProgress, CourseResource
        
        # 🔥 核心修复：从 user_resource_progress 读取总学习时长
        total_duration = db.query(func.sum(UserResourceProgress.total_study_duration)).filter(
            UserResourceProgress.user_id == user_id
        ).scalar() or 0

        # 🔥 计算已完成的学习项数量（视频+文档）
        finished_count = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.is_finished == True
        ).count()

        # 🔥 总学习资源数量（视频+文档）
        total_resources = db.query(CourseResource).filter(
            CourseResource.type.in_(['video', 'document'])
        ).count()

        # 🔥 今日学习时长
        today = datetime.now().date()
        today_duration = db.query(func.sum(UserResourceProgress.total_study_duration)).filter(
            UserResourceProgress.user_id == user_id,
            func.date(UserResourceProgress.last_study_time) == today
        ).scalar() or 0

        # 错题数量
        wrong_count = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.master_level < 2
        ).count()

        return {
            "total_study_duration": total_duration,
            "total_study_duration_hours": round(total_duration / 3600, 1),
            "finished_points_count": finished_count,
            "total_points_count": total_resources,
            "completion_rate": round(finished_count / total_resources * 100, 1) if total_resources > 0 else 0,
            "wrong_question_count": wrong_count,
            "today_study_duration": today_duration,
            "today_study_duration_minutes": round(today_duration / 60, 1)
        }


learning_center_service = LearningCenterService()