
"""
混合推荐引擎
综合协同过滤、内容推荐、基于知识的推荐等多种策略
"""
from typing import List, Dict
from sqlalchemy.orm import Session

from core.collaborative_filtering import CollaborativeFilteringRecommender
from core.content_based_recommender import ContentBasedRecommender
from utils.logger import logger


class HybridRecommender:
    """混合推荐引擎"""

    def __init__(self, db: Session):
        self.db = db
        self.cf_recommender = CollaborativeFilteringRecommender(db)
        self.cb_recommender = ContentBasedRecommender(db)

    def get_personalized_recommendations(
            self,
            user_id: int,
            query: str = None,
            limit: int = 10
    ) -> List[Dict]:
        """
        获取个性化推荐（混合策略）

        推荐策略权重：
        - 协同过滤：40%
        - 内容相似度：35%
        - 基于用户画像：25%
        """
        all_recommendations = []

        # 1. 协同过滤推荐（权重 40%）
        try:
            cf_recs = self.cf_recommender.recommend_by_collaborative_filtering(
                user_id,
                limit=limit // 2
            )
            for rec in cf_recs:
                rec['weight'] = 0.4
                rec['final_score'] = rec['score'] * 0.4
            all_recommendations.extend(cf_recs)
            logger.info(f"协同过滤推荐: {len(cf_recs)} 个")
        except Exception as e:
            logger.error(f"协同过滤推荐失败: {e}")

        # 2. 内容相似度推荐（权重 35%）
        try:
            # 获取用户最近学习的课程
            recent_course = self._get_user_recent_course(user_id)
            if recent_course:
                cb_recs = self.cb_recommender.recommend_similar_courses(
                    recent_course,
                    user_id,
                    limit=limit // 2
                )
                for rec in cb_recs:
                    rec['weight'] = 0.35
                    rec['final_score'] = rec.get('similarity', 0.5) * 0.35
                all_recommendations.extend(cb_recs)
                logger.info(f"内容相似度推荐: {len(cb_recs)} 个")
        except Exception as e:
            logger.error(f"内容相似度推荐失败: {e}")

        # 3. 基于用户画像推荐（权重 25%）
        try:
            profile_recs = self.cb_recommender.recommend_by_user_profile(
                user_id,
                limit=limit // 2
            )
            for rec in profile_recs:
                rec['weight'] = 0.25
                rec['final_score'] = rec['score'] * 0.25
            all_recommendations.extend(profile_recs)
            logger.info(f"用户画像推荐: {len(profile_recs)} 个")
        except Exception as e:
            logger.error(f"用户画像推荐失败: {e}")

        # 4. 如果有搜索查询，添加基于内容的推荐
        if query:
            try:
                query_recs = self._recommend_by_query(query, user_id, limit // 2)
                for rec in query_recs:
                    rec['weight'] = 0.3
                    rec['final_score'] = rec['score'] * 0.3
                all_recommendations.extend(query_recs)
            except Exception as e:
                logger.error(f"查询推荐失败: {e}")

        # 5. 合并、去重、排序
        final_recommendations = self._merge_and_rank(
            all_recommendations,
            limit
        )

        logger.info(f"混合推荐完成，最终推荐 {len(final_recommendations)} 个课程")
        return final_recommendations

    def _get_user_recent_course(self, user_id: int) -> int:
        """获取用户最近学习的课程ID"""
        from models.db_models import UserCourseBehavior

        recent = self.db.query(UserCourseBehavior.course_id).filter(
            UserCourseBehavior.user_id == user_id
        ).order_by(
            UserCourseBehavior.create_time.desc()
        ).first()

        return recent[0] if recent else None

    def _recommend_by_query(
            self,
            query: str,
            user_id: int,
            limit: int
    ) -> List[Dict]:
        """基于查询关键词推荐"""
        from models.db_models import Course

        # 简单的关键词匹配
        courses = self.db.query(Course).filter(
            Course.is_published == True,
            (
                    Course.title.like(f'%{query}%') |
                    Course.description.like(f'%{query}%')
            )
        ).limit(limit).all()

        return [
            {
                'course_id': course.id,
                'course_title': course.title,
                'score': 0.8,
                'reason': f'与您的搜索 "{query}" 相关',
                'recommend_type': 'query_based'
            }
            for course in courses
        ]

    def _merge_and_rank(
            self,
            recommendations: List[Dict],
            limit: int
    ) -> List[Dict]:
        """合并并排名推荐结果"""
        if not recommendations:
            return []

        # 按 final_score 降序排序
        recommendations.sort(
            key=lambda x: x.get('final_score', 0),
            reverse=True
        )

        # 去重（基于 course_id）
        seen_course_ids = set()
        unique_recs = []

        for rec in recommendations:
            course_id = rec.get('course_id')
            if course_id and course_id not in seen_course_ids:
                seen_course_ids.add(course_id)
                unique_recs.append(rec)

            if len(unique_recs) >= limit:
                break

        return unique_recs[:limit]
