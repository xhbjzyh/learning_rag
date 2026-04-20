"""
推荐服务层
实现个性化推荐、学习行为采集、用户画像管理的业务逻辑
设计原则：
1. 仅处理业务逻辑，不直接暴露HTTP接口
2. 对接数据库和核心引擎，做数据校验和转换
3. 统一异常处理，抛出业务异常
"""
from typing import List
from sqlalchemy.orm import Session

from core.recommender import recommender
from models.db_models import UserLearningRecord, KnowledgePoint, UserProfile
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException


class RecommendService:
    @staticmethod
    def add_learning_record(user_id: int, point_id: int, record_data: dict, db: Session):
        """
        新增/更新用户学习记录
        :param user_id: 用户ID
        :param point_id: 知识点ID
        :param record_data: 学习记录数据（学习时长、收藏状态、评分等）
        :param db: 数据库会话
        :return: 更新后的学习记录
        """
        # 1. 检查知识点是否存在
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not point:
            logger.error(f"学习记录更新失败：知识点{point_id}不存在")
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="知识点不存在"
            )

        # 2. 查询是否已有记录
        record = db.query(UserLearningRecord).filter(
            UserLearningRecord.user_id == user_id,
            UserLearningRecord.point_id == point_id
        ).first()

        if record:
            # 3. 更新已有记录
            for key, value in record_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        else:
            # 4. 新增记录
            record = UserLearningRecord(
                user_id=user_id,
                point_id=point_id,
                **record_data
            )
            db.add(record)

        # 5. 提交事务
        db.commit()
        db.refresh(record)
        logger.info(f"用户{user_id}学习记录更新成功，知识点ID：{point_id}")
        return record

    @staticmethod
    def get_personal_recommend(user_id: int, db: Session, top_k: int = 10):
        """
        获取个性化推荐知识点列表
        :param user_id: 用户ID
        :param db: 数据库会话
        :param top_k: 推荐数量
        :return: 推荐的知识点列表
        """
        return recommender.get_recommend_points(
            user_id=user_id,
            db=db,
            top_k=top_k
        )

    @staticmethod
    def get_user_learn_history(user_id: int, db: Session):
        """
        获取用户学习历史记录
        :param user_id: 用户ID
        :param db: 数据库会话
        :return: 学习历史记录列表
        """
        records = db.query(UserLearningRecord).filter(
            UserLearningRecord.user_id == user_id
        ).order_by(UserLearningRecord.update_time.desc()).all()
        return records

    @staticmethod
    def get_user_profile(user_id: int, db: Session):
        """
        获取用户画像
        :param user_id: 用户ID
        :param db: 数据库会话
        :return: 用户画像对象
        """
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            # 如果没有画像，创建空画像
            profile = UserProfile(user_id=user_id, tag_weight="{}")
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile


# 全局单例
recommend_service = RecommendService()