"""
用户-个性化推荐业务逻辑
新增：学习路径生成
"""
from sqlalchemy.orm import Session

from core.recommender import recommender
from core.learning_path import learning_path_generator


class PersonalRecommendService:
    """个性化推荐服务类"""

    @staticmethod
    def get_personal_recommend(user_id: int, db: Session, top_k: int = 10):
        return recommender.get_recommend_points(
            user_id=user_id,
            db=db,
            top_k=top_k
        )

    @staticmethod
    def generate_learning_path(user_id: int, db: Session, max_length: int = 10):
        """
        生成个性化学习路径
        """
        return learning_path_generator.generate_learning_path(
            user_id=user_id,
            db=db,
            max_length=max_length
        )


personal_recommend_service = PersonalRecommendService()