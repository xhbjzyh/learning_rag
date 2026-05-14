
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime

from core.hybrid_recommender import HybridRecommender
from core.collaborative_filtering import CollaborativeFilteringRecommender
from core.content_based_recommender import ContentBasedRecommender
from models.db_models import RecommendationRecord, Course
from utils.logger import logger


class RecommendationService:
    """推荐服务类"""

    def __init__(self):
        self._recommenders = {}  # 缓存推荐器实例

    def _get_hybrid_recommender(self, db: Session) -> HybridRecommender:
        """获取混合推荐器实例"""
        return HybridRecommender(db)

    def get_personalized_recommendations(
            self,
            db: Session,
            user_id: int,
            query: str = None,
            limit: int = 10
    ) -> List[Dict]:
        """获取个性化推荐"""
        recommender = self._get_hybrid_recommender(db)

        # 获取推荐结果
        recommendations = recommender.get_personalized_recommendations(
            user_id=user_id,
            query=query,
            limit=limit
        )

        # 保存推荐记录
        self._save_recommendation_records(db, user_id, recommendations)

        return recommendations

    def _save_recommendation_records(
            self,
            db: Session,
            user_id: int,
            recommendations: List[Dict]
    ):
        """保存推荐记录到数据库"""
        for rank, rec in enumerate(recommendations, 1):
            record = RecommendationRecord(
                user_id=user_id,
                target_id=rec['course_id'],
                recommend_type=rec.get('recommend_type', 'hybrid'),
                recommendation_reason=rec.get('reason', ''),
                score=rec.get('final_score', 0),
                rank=rank,
                is_clicked=False,
                create_time=datetime.now()
            )
            db.add(record)

        db.commit()
        logger.info(f"为用户 {user_id} 保存了 {len(recommendations)} 条推荐记录")

    def refresh_user_similarities(self, db: Session):
        """刷新用户相似度（定时任务调用）"""
        recommender = CollaborativeFilteringRecommender(db)
        recommender.calculate_all_user_similarities()

    def refresh_course_similarities(self, db: Session):
        """刷新课程相似度（定时任务调用）"""
        recommender = ContentBasedRecommender(db)
        recommender.calculate_all_course_similarities()


# 单例
recommendation_service = RecommendationService()
