import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

from models.db_models import (
    UserCourseBehavior, Course, SysUser,
    UserSimilarity, CourseSimilarity,
    UserKnowledgeMastery, KnowledgePoint
)
from utils.logger import logger


class CollaborativeFilteringRecommender:
    """协同过滤推荐引擎"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_user_similarities(self):
        """计算所有活跃用户的相似度矩阵"""
        logger.info("开始计算用户相似度...")

        # 获取所有有行为数据的用户
        active_users = self._get_active_users()

        if len(active_users) < 2:
            logger.warning("活跃用户数量不足，无法计算相似度")
            return

        # 构建用户-课程行为矩阵
        user_course_matrix, user_ids = self._build_user_course_matrix(active_users)

        # 计算余弦相似度
        similarity_matrix = cosine_similarity(user_course_matrix)

        # 保存相似度结果
        self._save_user_similarities(user_ids, similarity_matrix)

        logger.info(f"用户相似度计算完成，共 {len(user_ids)} 个用户")

    def _get_active_users(self) -> List[int]:
        """获取有行为数据的活跃用户ID列表"""
        # 至少有3次课程行为的用户
        behaviors = self.db.query(UserCourseBehavior.user_id).group_by(
            UserCourseBehavior.user_id
        ).having(
            self.db.func.count(UserCourseBehavior.id) >= 3
        ).all()

        return [user[0] for user in behaviors]

    def _build_user_course_matrix(self, user_ids: List[int]) -> Tuple[np.ndarray, List[int]]:
        """
        构建用户-课程行为矩阵
        返回: (矩阵, 用户ID列表)
        """
        # 获取所有课程ID
        all_courses = self.db.query(Course.id).filter(
            Course.is_published == True
        ).all()
        course_ids = [c[0] for c in all_courses]

        if not course_ids:
            return np.array([]), []

        # 初始化矩阵
        matrix = np.zeros((len(user_ids), len(course_ids)))

        # 填充矩阵
        for i, user_id in enumerate(user_ids):
            behaviors = self.db.query(UserCourseBehavior).filter(
                UserCourseBehavior.user_id == user_id,
                UserCourseBehavior.course_id.in_(course_ids)
            ).all()

            # 行为权重映射
            behavior_weights = {
                'view': 0.1,
                'collect': 0.3,
                'complete': 0.5,
                'rate': 0.4,
                'share': 0.4
            }

            for behavior in behaviors:
                if behavior.course_id in course_ids:
                    course_idx = course_ids.index(behavior.course_id)
                    weight = behavior_weights.get(behavior.behavior_type, 0.1)
                    value = behavior.behavior_value or 1.0
                    matrix[i][course_idx] += weight * value

        return matrix, user_ids

    def _save_user_similarities(self, user_ids: List[int], similarity_matrix: np.ndarray):
        """保存用户相似度到数据库"""
        from datetime import datetime

        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                user_id1 = user_ids[i]
                user_id2 = user_ids[j]
                similarity = float(similarity_matrix[i][j])

                # 只保存相似度 > 0.1 的用户对
                if similarity < 0.1:
                    continue

                # 检查是否已存在
                existing = self.db.query(UserSimilarity).filter(
                    ((UserSimilarity.user_id1 == user_id1) &
                     (UserSimilarity.user_id2 == user_id2)) |
                    ((UserSimilarity.user_id1 == user_id2) &
                     (UserSimilarity.user_id2 == user_id1))
                ).first()

                if existing:
                    existing.similarity = similarity
                    existing.update_time = datetime.now()
                else:
                    new_similarity = UserSimilarity(
                        user_id1=user_id1,
                        user_id2=user_id2,
                        similarity=similarity
                    )
                    self.db.add(new_similarity)

        self.db.commit()

    def get_similar_users(self, user_id: int, top_n: int = 10) -> List[Dict]:
        """获取与指定用户最相似的N个用户"""
        similarities = self.db.query(UserSimilarity).filter(
            (UserSimilarity.user_id1 == user_id) |
            (UserSimilarity.user_id2 == user_id)
        ).order_by(
            UserSimilarity.similarity.desc()
        ).limit(top_n).all()

        result = []
        for sim in similarities:
            other_user_id = sim.user_id2 if sim.user_id1 == user_id else sim.user_id1
            result.append({
                'user_id': other_user_id,
                'similarity': sim.similarity
            })

        return result

    def recommend_by_collaborative_filtering(
            self,
            user_id: int,
            limit: int = 10
    ) -> List[Dict]:
        """
        基于协同过滤的推荐
        找到相似用户喜欢的课程，推荐给当前用户
        """
        # 1. 获取相似用户
        similar_users = self.get_similar_users(user_id, top_n=20)

        if not similar_users:
            logger.info(f"用户 {user_id} 没有相似用户，使用默认推荐")
            return self._get_default_recommendations(limit)

        # 2. 获取当前用户已学习的课程
        user_courses = set(
            row[0] for row in self.db.query(UserCourseBehavior.course_id).filter(
                UserCourseBehavior.user_id == user_id
            ).all()
        )

        # 3. 收集相似用户的高评分课程
        course_scores = defaultdict(float)
        course_reasons = defaultdict(list)

        for sim_user in similar_users:
            other_user_id = sim_user['user_id']
            similarity = sim_user['similarity']

            # 获取该用户的行为数据
            behaviors = self.db.query(UserCourseBehavior).filter(
                UserCourseBehavior.user_id == other_user_id,
                UserCourseBehavior.behavior_type.in_(['complete', 'rate', 'collect'])
            ).all()

            for behavior in behaviors:
                if behavior.course_id not in user_courses:
                    # 根据行为类型计算分数
                    score_map = {
                        'complete': 0.8,
                        'rate': behavior.behavior_value or 0.5,
                        'collect': 0.6
                    }
                    score = score_map.get(behavior.behavior_type, 0.3)

                    # 加权分数 = 行为分数 * 用户相似度
                    weighted_score = score * similarity
                    course_scores[behavior.course_id] += weighted_score

                    # 记录推荐理由
                    course_reasons[behavior.course_id].append(
                        f"与您兴趣相似的用户也学习了这门课程"
                    )

        # 4. 排序并返回Top N
        sorted_courses = sorted(
            course_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        recommendations = []
        for course_id, score in sorted_courses:
            course = self.db.query(Course).filter(Course.id == course_id).first()
            if course:
                recommendations.append({
                    'course_id': course_id,
                    'course_title': course.title,
                    'cover_url': course.cover_url,
                    'difficulty': course.difficulty,
                    'score': round(score, 3),
                    'reason': course_reasons[course_id][0],
                    'recommend_type': 'collaborative_filtering'
                })

        logger.info(f"协同过滤推荐完成，为用户 {user_id} 推荐 {len(recommendations)} 个课程")
        return recommendations

    def _get_default_recommendations(self, limit: int) -> List[Dict]:
        """默认推荐（冷启动）：返回热门课程"""
        popular_courses = self.db.query(Course).filter(
            Course.is_published == True
        ).order_by(
            Course.view_count.desc()
        ).limit(limit).all()

        return [
            {
                'course_id': course.id,
                'course_title': course.title,
                'cover_url': course.cover_url,
                'difficulty': course.difficulty,
                'score': 0.5,
                'reason': '热门课程推荐',
                'recommend_type': 'popular'
            }
            for course in popular_courses
        ]
