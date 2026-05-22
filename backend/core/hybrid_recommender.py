
"""
混合推荐引擎
综合协同过滤、内容推荐、基于知识的推荐等多种策略

🔥 论文第4.3节实现：
- 动态权重调整策略：基于用户交互数据量自动调整推荐权重
- 混合推荐公式：Score_final = α·Score_CF + β·Score_CB + γ·Score_Profile
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

    def _calculate_dynamic_weights(self, user_id: int) -> Dict[str, float]:
        """
        🔥 计算动态权重（论文第4.3节核心算法）
        
        动态权重调整策略：
        - 用户交互记录 < 10条：α=0.2（侧重内容推荐，冷启动友好）
        - 用户交互记录 10-50条：α线性增长（0.2 → 0.8）
        - 用户交互记录 > 50条：α=0.8（侧重协同过滤，数据充分）
        
        🔥 改进：综合统计所有学习相关表的交互记录
        包括：user_course_behavior + user_learning_history + user_course_knowledge_mastery
        
        权重分配：
        - α（协同过滤）：动态调整
        - β（内容推荐）：(1-α) × 0.6
        - γ（用户画像）：(1-α) × 0.4
        
        Returns:
            {'cf_weight': float, 'cb_weight': float, 'profile_weight': float}
        """
        from models.db_models import (
            UserCourseBehavior, 
            UserLearningHistory,
            UserCourseKnowledgeMastery
        )
        
        # 🔥 综合统计用户交互记录数
        # 1. 课程行为记录（view, collect, complete等）
        behavior_count = self.db.query(UserCourseBehavior).filter(
            UserCourseBehavior.user_id == user_id
        ).count()
        
        # 2. 学习历史记录（RAG问答、知识点学习）
        history_count = self.db.query(UserLearningHistory).filter(
            UserLearningHistory.user_id == user_id
        ).count()
        
        # 3. 课程知识点掌握度记录（视频学习、习题练习）
        mastery_count = self.db.query(UserCourseKnowledgeMastery).filter(
            UserCourseKnowledgeMastery.user_id == user_id
        ).count()
        
        # 总交互记录数（去重后的近似值）
        interaction_count = behavior_count + history_count + mastery_count
        
        # 动态计算α值（协同过滤权重）
        if interaction_count < 10:
            alpha = 0.2  # 冷启动：侧重内容推荐
            strategy = "冷启动策略"
        elif interaction_count > 50:
            alpha = 0.8  # 充分数据：侧重协同过滤
            strategy = "成熟用户策略"
        else:
            # 线性插值：10-50条之间
            alpha = 0.2 + (interaction_count - 10) * (0.6 / 40)
            strategy = f"过渡期策略（{interaction_count}条记录）"
        
        # 计算其他权重
        cf_weight = alpha
        cb_weight = (1 - alpha) * 0.6  # 内容推荐占剩余权重的60%
        profile_weight = (1 - alpha) * 0.4  # 用户画像占剩余权重的40%
        
        logger.info(f"📊 用户 {user_id} 权重计算 - "
                   f"行为:{behavior_count}, 历史:{history_count}, 掌握度:{mastery_count}, "
                   f"总计:{interaction_count}条, "
                   f"策略: {strategy}, "
                   f"α(CF)={cf_weight:.2f}, β(CB)={cb_weight:.2f}, γ(Profile)={profile_weight:.2f}")
        
        return {
            'cf_weight': cf_weight,
            'cb_weight': cb_weight,
            'profile_weight': profile_weight,
            'interaction_count': interaction_count
        }

    def get_personalized_recommendations(
            self,
            user_id: int,
            query: str = None,
            limit: int = 10
    ) -> List[Dict]:
        """
        🔥 获取个性化推荐（混合策略 - 论文第4.3节实现）
        
        混合推荐公式：
        Score_final = α·Score_CF + β·Score_CB + γ·Score_Profile
        
        动态权重调整：
        - 交互记录 < 10条：α=0.2（内容推荐为主）
        - 交互记录 10-50条：α线性增长
        - 交互记录 > 50条：α=0.8（协同过滤为主）
        """
        # 1. 计算动态权重
        weights = self._calculate_dynamic_weights(user_id)
        cf_weight = weights['cf_weight']
        cb_weight = weights['cb_weight']
        profile_weight = weights['profile_weight']
        
        all_recommendations = []

        # 2. 协同过滤推荐（动态权重 α）
        try:
            cf_recs = self.cf_recommender.recommend_by_collaborative_filtering(
                user_id,
                limit=limit
            )
            for rec in cf_recs:
                rec['weight'] = cf_weight
                rec['final_score'] = rec['score'] * cf_weight
                rec['strategy'] = 'collaborative_filtering'
            all_recommendations.extend(cf_recs)
            logger.info(f"✅ 协同过滤推荐: {len(cf_recs)} 个课程（权重: {cf_weight:.2f}）")
        except Exception as e:
            logger.error(f" 协同过滤推荐失败: {e}")

        # 3. 内容相似度推荐（动态权重 β）
        try:
            # 获取用户最近学习的课程
            recent_course = self._get_user_recent_course(user_id)
            if recent_course:
                cb_recs = self.cb_recommender.recommend_similar_courses(
                    recent_course,
                    user_id,
                    limit=limit
                )
                for rec in cb_recs:
                    rec['weight'] = cb_weight
                    rec['final_score'] = rec.get('similarity', 0.5) * cb_weight
                    rec['strategy'] = 'content_based'
                all_recommendations.extend(cb_recs)
                logger.info(f"✅ 内容相似度推荐: {len(cb_recs)} 个课程（权重: {cb_weight:.2f}）")
        except Exception as e:
            logger.error(f"❌ 内容相似度推荐失败: {e}")

        # 4. 基于用户画像推荐（动态权重 γ）
        try:
            profile_recs = self.cb_recommender.recommend_by_user_profile(
                user_id,
                limit=limit
            )
            for rec in profile_recs:
                rec['weight'] = profile_weight
                rec['final_score'] = rec['score'] * profile_weight
                rec['strategy'] = 'profile_based'
            all_recommendations.extend(profile_recs)
            logger.info(f"✅ 用户画像推荐: {len(profile_recs)} 个课程（权重: {profile_weight:.2f}）")
        except Exception as e:
            logger.error(f"❌ 用户画像推荐失败: {e}")

        # 5. 如果有搜索查询，添加基于查询的推荐
        if query:
            try:
                query_recs = self._recommend_by_query(query, user_id, limit)
                for rec in query_recs:
                    rec['weight'] = 0.5  # 查询推荐使用固定权重
                    rec['final_score'] = rec['score'] * 0.5
                    rec['strategy'] = 'query_based'
                all_recommendations.extend(query_recs)
                logger.info(f"✅ 查询推荐: {len(query_recs)} 个课程")
            except Exception as e:
                logger.error(f"❌ 查询推荐失败: {e}")

        # 6. 合并、去重、排序
        final_recommendations = self._merge_and_rank(
            all_recommendations,
            limit
        )

        logger.info(f"🎯 混合推荐完成，最终推荐 {len(final_recommendations)} 个课程")
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
