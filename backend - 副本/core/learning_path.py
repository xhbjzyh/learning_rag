"""
学习路径生成引擎
基于用户画像和学习进度，生成个性化学习路径
"""
from typing import List, Dict
from sqlalchemy.orm import Session

from models.db_models import KnowledgePoint, LearningProgress, UserProfile
from utils.logger import logger


class LearningPathGenerator:
    """学习路径生成器"""

    @staticmethod
    def generate_learning_path(
            user_id: int,
            db: Session,
            max_length: int = 10
    ) -> List[Dict]:
        """
        生成个性化学习路径
        算法逻辑：
        1. 获取用户已完成的知识点
        2. 获取用户未完成的知识点
        3. 根据用户薄弱标签和知识点难度排序
        4. 生成推荐的学习顺序
        """
        logger.info(f"为用户{user_id}生成学习路径")

        # 1. 获取用户已完成的知识点
        finished_points = db.query(LearningProgress.point_id).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.is_finished == True
        ).all()
        finished_point_ids = [p[0] for p in finished_points]

        # 2. 获取用户未完成的知识点
        unfinished_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.id.notin_(finished_point_ids)
        ).all()

        if not unfinished_points:
            logger.info(f"用户{user_id}已完成所有知识点")
            return []

        # 3. 获取用户画像
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        weak_tags = []
        if user_profile and user_profile.weak_tags:
            import json
            try:
                weak_tags = json.loads(user_profile.weak_tags)
            except:
                weak_tags = []

        # 4. 对未完成知识点进行排序
        # 排序规则：
        # - 包含薄弱标签的知识点优先
        # - 难度低的知识点优先
        # - 创建时间早的知识点优先
        def sort_key(point):
            # 计算优先级分数，分数越低越优先
            score = 0

            # 薄弱标签加分
            for tag in weak_tags:
                if tag in point.title or tag in point.content:
                    score -= 10

            # 难度加分
            difficulty_map = {"简单": 0, "中等": 1, "困难": 2}
            score += difficulty_map.get(point.difficulty, 1)

            # 创建时间加分
            if point.create_time:
                score += point.create_time.timestamp() / 1e10

            return score

        # 排序
        sorted_points = sorted(unfinished_points, key=sort_key)

        # 5. 生成学习路径
        learning_path = []
        for i, point in enumerate(sorted_points[:max_length]):
            learning_path.append({
                "order": i + 1,
                "point_id": point.id,
                "title": point.title,
                "difficulty": point.difficulty,
                "estimated_duration": len(point.content) // 100 + 1,  # 预估学习时长，单位：分钟
                "reason": "薄弱知识点优先" if any(
                    tag in point.title or tag in point.content for tag in weak_tags) else "按难度顺序"
            })

        logger.info(f"为用户{user_id}生成了{len(learning_path)}个知识点的学习路径")
        return learning_path


# 全局单例
learning_path_generator = LearningPathGenerator()