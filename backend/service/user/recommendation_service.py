from sqlalchemy.orm import Session
from models.db_models import (
    UserProfile, UserKnowledgeMastery, UserLearningPreference,
    Course, CourseResource, KnowledgePoint, KnowledgeQaRecord
)
from fastapi import HTTPException
from datetime import datetime, timedelta
import json

class UserRecommendationService:
    """
    用户端个性化推荐业务逻辑（三源融合版）
    """

    def get_personalized_recommendations(self, db: Session, user_id: int, limit: int = 10):
        """
        获取综合个性化推荐结果
        """
        # 1. 薄弱点推荐（权重最高）
        weak_point_recommendations = self.get_weak_points_recommendation(db, user_id, limit=4)

        # 2. 最近问答相关推荐
        recent_qa_recommendations = self.get_recent_qa_recommendation(db, user_id, limit=3)

        # 3. 热门课程推荐
        hot_course_recommendations = self.get_hot_course_recommendation(db, limit=3)

        # 合并并去重
        all_recommendations = []
        seen_ids = set()

        for rec in weak_point_recommendations + recent_qa_recommendations + hot_course_recommendations:
            if rec["id"] not in seen_ids:
                seen_ids.add(rec["id"])
                all_recommendations.append(rec)

        return all_recommendations[:limit]

    def get_weak_points_recommendation(self, db: Session, user_id: int, limit: int = 5):
        """
        基于三源融合掌握度的薄弱点推荐
        """
        # 查询用户所有未完全掌握的知识点，按综合得分升序排列
        weak_points = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.mastery_score < 70
        ).order_by(
            UserKnowledgeMastery.mastery_score.asc(),
            UserKnowledgeMastery.exercise_mastery.asc(),
            UserKnowledgeMastery.qa_mastery.asc()
        ).limit(limit).all()

        recommendations = []
        for mastery in weak_points:
            # 获取知识点详情
            point = db.query(KnowledgePoint).get(mastery.knowledge_point_id)
            if not point:
                continue

            # 选择最合适的资源类型
            preferred_type = self._get_preferred_resource_type(db, user_id, mastery)

            # 查询该知识点关联的对应类型资源
            resource = db.query(CourseResource).filter(
                CourseResource.knowledge_points.any(id=point.id),
                CourseResource.type == preferred_type,
                CourseResource.is_published == True
            ).first()

            recommendations.append({
                "id": point.id,
                "type": "knowledge_point",
                "title": point.title,
                "content": point.content[:100] + "..." if len(point.content) > 100 else point.content,
                "difficulty": point.difficulty,
                "mastery_score": round(mastery.mastery_score, 1),
                "weak_reason": self._generate_weak_reason(mastery),
                "recommended_resource": resource,
                "recommendation_reason": "基于你的薄弱点推荐"
            })

        return recommendations

    def get_recent_qa_recommendation(self, db: Session, user_id: int, limit: int = 3):
        """
        基于用户最近问答记录的推荐
        """
        # 查询用户最近7天的问答记录
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_qa = db.query(KnowledgeQaRecord).filter(
            KnowledgeQaRecord.user_id == user_id,
            KnowledgeQaRecord.create_time >= seven_days_ago
        ).order_by(KnowledgeQaRecord.create_time.desc()).limit(5).all()

        # 提取相关知识点并去重
        point_ids = list({qa.knowledge_point_id for qa in recent_qa})

        recommendations = []
        for point_id in point_ids:
            point = db.query(KnowledgePoint).get(point_id)
            if not point:
                continue

            # 查询该知识点的相关资源
            resources = db.query(CourseResource).filter(
                CourseResource.knowledge_points.any(id=point_id),
                CourseResource.is_published == True
            ).limit(2).all()

            recommendations.append({
                "id": point.id,
                "type": "knowledge_point",
                "title": point.title,
                "content": point.content[:100] + "..." if len(point.content) > 100 else point.content,
                "difficulty": point.difficulty,
                "related_resources": resources,
                "recommendation_reason": "基于你最近的提问推荐"
            })

        return recommendations[:limit]

    def get_hot_course_recommendation(self, db: Session, user_id: int, limit: int = 5):
        """
        基于用户能力水平的热门课程推荐
        """
        # 获取用户画像
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        # 确定推荐难度范围
        difficulty_range = ["中等"]
        if profile:
            if profile.comprehensive_ability < 40:
                difficulty_range = ["简单", "中等"]
            elif profile.comprehensive_ability < 70:
                difficulty_range = ["中等", "困难"]
            else:
                difficulty_range = ["困难"]

        # 查询热门课程
        hot_courses = db.query(Course).filter(
            Course.is_published == True,
            Course.is_public == True,
            Course.difficulty.in_(difficulty_range)
        ).order_by(Course.view_count.desc()).limit(limit).all()

        recommendations = []
        for course in hot_courses:
            recommendations.append({
                "id": course.id,
                "type": "course",
                "title": course.title,
                "description": course.description[:100] + "..." if course.description and len(course.description) > 100 else course.description,
                "cover_url": course.cover_url,
                "lecturer": course.lecturer,
                "difficulty": course.difficulty,
                "view_count": course.view_count,
                "recommendation_reason": "热门课程推荐"
            })

        return recommendations

    def get_learning_path(self, db: Session, user_id: int, target_point_id: int):
        """
        生成从当前水平到目标知识点的学习路径
        """
        # 获取目标知识点
        target_point = db.query(KnowledgePoint).get(target_point_id)
        if not target_point:
            raise HTTPException(status_code=404, detail="知识点不存在")

        # 解析前置知识
        pre_knowledge_ids = []
        if target_point.pre_knowledge:
            try:
                pre_knowledge_ids = json.loads(target_point.pre_knowledge)
            except:
                pass

        # 获取用户对前置知识的掌握情况
        learning_path = []
        for pre_id in pre_knowledge_ids:
            pre_point = db.query(KnowledgePoint).get(pre_id)
            if not pre_point:
                continue

            mastery = db.query(UserKnowledgeMastery).filter(
                UserKnowledgeMastery.user_id == user_id,
                UserKnowledgeMastery.knowledge_point_id == pre_id
            ).first()

            if not mastery or mastery.mastery_score < 70:
                # 推荐学习该前置知识
                learning_path.append({
                    "order": len(learning_path) + 1,
                    "knowledge_point": pre_point,
                    "mastery_score": mastery.mastery_score if mastery else 0,
                    "suggestion": "需要先学习该前置知识",
                    "recommended_resource": self._get_best_resource(db, pre_id)
                })

        # 添加目标知识点
        learning_path.append({
            "order": len(learning_path) + 1,
            "knowledge_point": target_point,
            "mastery_score": 0,
            "suggestion": "目标知识点",
            "recommended_resource": self._get_best_resource(db, target_point_id)
        })

        return learning_path

    def _get_preferred_resource_type(self, db: Session, user_id: int, mastery: UserKnowledgeMastery) -> str:
        """
        根据用户学习偏好和知识点掌握情况选择最合适的资源类型
        """
        # 获取用户学习偏好
        preference = db.query(UserLearningPreference).filter(
            UserLearningPreference.user_id == user_id
        ).first()

        if not preference:
            return "video"

        # 对于掌握度特别低的知识点，优先推荐视频
        if mastery.mastery_score < 30:
            return "video"

        # 对于掌握度中等的知识点，优先推荐习题
        if mastery.mastery_score < 60:
            return "exercise"

        # 对于掌握度较高的知识点，根据用户偏好推荐
        preferences = {
            "video": preference.preferred_type_video,
            "document": preference.preferred_type_book,
            "exercise": preference.preferred_type_exercise
        }

        return max(preferences, key=preferences.get)

    def _generate_weak_reason(self, mastery: UserKnowledgeMastery) -> str:
        """
        生成个性化的薄弱点原因说明
        """
        reasons = []
        if mastery.exercise_mastery < 50:
            reasons.append("习题正确率较低")
        if mastery.video_mastery < 60:
            reasons.append("视频学习不够完整")
        if mastery.qa_mastery < 50:
            reasons.append("相关问题较多")

        if not reasons:
            return "需要进一步巩固"
        return "、".join(reasons)

    def _get_best_resource(self, db: Session, point_id: int):
        """
        获取知识点的最佳学习资源
        """
        # 优先推荐视频资源
        resource = db.query(CourseResource).filter(
            CourseResource.knowledge_points.any(id=point_id),
            CourseResource.type == "video",
            CourseResource.is_published == True
        ).first()

        if not resource:
            # 没有视频则推荐文档
            resource = db.query(CourseResource).filter(
                CourseResource.knowledge_points.any(id=point_id),
                CourseResource.type == "document",
                CourseResource.is_published == True
            ).first()

        return resource


# 全局单例
user_recommendation_service = UserRecommendationService()