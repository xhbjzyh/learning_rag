
"""
用户个人仪表盘服务
整合用户学习统计数据，提供仪表盘展示所需的核心指标
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, List

from models.db_models import (
    UserResourceProgress, LearningProgress, UserLearningRecord,
    UserExerciseRecord, WrongQuestion, UserKnowledgeMastery,
    UserProfile, Course, CourseResource, KnowledgePoint
)
from utils.logger import logger


class PersonalDashboardService:
    """个人仪表盘服务"""

    def get_dashboard_data(self, db: Session, user_id: int) -> Dict:
        """
        获取仪表盘完整数据
        包含：学习概览、最近活动、学习趋势、知识掌握情况等
        """
        # 1. 学习概览统计
        overview = self._get_learning_overview(db, user_id)

        # 2. 最近学习活动
        recent_activities = self._get_recent_activities(db, user_id, limit=5)

        # 3. 学习趋势（近7天）
        learning_trend = self._get_learning_trend(db, user_id, days=7)

        # 4. 知识掌握情况
        knowledge_mastery = self._get_knowledge_mastery_stats(db, user_id)

        # 5. 课程进度
        course_progress = self._get_course_progress_stats(db, user_id)

        return {
            "overview": overview,
            "recent_activities": recent_activities,
            "learning_trend": learning_trend,
            "knowledge_mastery": knowledge_mastery,
            "course_progress": course_progress
        }

    def _get_learning_overview(self, db: Session, user_id: int) -> Dict:
        """获取学习概览统计"""
        # 总学习时长（秒）
        total_duration = db.query(func.sum(UserResourceProgress.total_study_duration)).filter(
            UserResourceProgress.user_id == user_id
        ).scalar() or 0

        # 已完成资源数
        completed_resources = db.query(func.count(UserResourceProgress.id)).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.is_finished == True
        ).scalar() or 0

        # 总答题数
        total_exercises = db.query(func.count(UserExerciseRecord.id)).filter(
            UserExerciseRecord.user_id == user_id
        ).scalar() or 0

        # 正确答题数
        correct_exercises = db.query(func.count(UserExerciseRecord.id)).filter(
            UserExerciseRecord.user_id == user_id,
            UserExerciseRecord.is_correct == True
        ).scalar() or 0

        # 正确率
        accuracy_rate = round((correct_exercises / total_exercises * 100), 2) if total_exercises > 0 else 0

        # 错题数量
        wrong_count = db.query(func.count(WrongQuestion.id)).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.master_level < 2
        ).scalar() or 0

        # 已掌握知识点数
        mastered_points = db.query(func.count(UserKnowledgeMastery.id)).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.mastery_score >= 80
        ).scalar() or 0

        # 总知识点数（用户学习过的）
        total_points = db.query(func.count(UserKnowledgeMastery.id)).filter(
            UserKnowledgeMastery.user_id == user_id
        ).scalar() or 0

        return {
            "total_study_duration": total_duration,
            "completed_resources": completed_resources,
            "total_exercises": total_exercises,
            "accuracy_rate": accuracy_rate,
            "wrong_count": wrong_count,
            "mastered_points": mastered_points,
            "total_points": total_points
        }

    def _get_recent_activities(self, db: Session, user_id: int, limit: int = 5) -> List[Dict]:
        """获取最近学习活动"""
        activities = []

        # 1. 最近的资源学习记录
        resource_records = db.query(UserResourceProgress, CourseResource).join(
            CourseResource, UserResourceProgress.resource_id == CourseResource.id
        ).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.last_study_time.isnot(None)
        ).order_by(
            UserResourceProgress.last_study_time.desc()
        ).limit(limit).all()

        for progress, resource in resource_records:
            activities.append({
                "type": "resource",
                "title": resource.title,
                "resource_type": resource.type,
                "progress": progress.progress,
                "is_finished": progress.is_finished,
                "time": progress.last_study_time.isoformat() if progress.last_study_time else None,
                "description": f"学习了{resource.type}：{resource.title}"
            })

        # 2. 最近的答题记录
        exercise_records = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id
        ).order_by(
            UserExerciseRecord.create_time.desc()
        ).limit(limit).all()

        for record in exercise_records:
            activities.append({
                "type": "exercise",
                "title": f"练习题 #{record.exercise_id}",
                "is_correct": record.is_correct,
                "score": record.score,
                "time": record.create_time.isoformat() if record.create_time else None,
                "description": f"完成了一道{'正确' if record.is_correct else '错误'}的练习题"
            })

        # 按时间排序并取前limit条
        activities.sort(key=lambda x: x.get("time", ""), reverse=True)
        return activities[:limit]

    def _get_learning_trend(self, db: Session, user_id: int, days: int = 7) -> List[Dict]:
        """获取学习趋势（近N天）"""
        trend_data = []
        today = datetime.now().date()

        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())

            # 当天的学习时长
            duration = db.query(func.sum(UserResourceProgress.total_study_duration)).filter(
                UserResourceProgress.user_id == user_id,
                UserResourceProgress.last_study_time >= start_datetime,
                UserResourceProgress.last_study_time <= end_datetime
            ).scalar() or 0

            # 当天的答题数
            exercises = db.query(func.count(UserExerciseRecord.id)).filter(
                UserExerciseRecord.user_id == user_id,
                UserExerciseRecord.create_time >= start_datetime,
                UserExerciseRecord.create_time <= end_datetime
            ).scalar() or 0

            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "duration": duration,
                "exercises": exercises
            })

        return trend_data

    def _get_knowledge_mastery_stats(self, db: Session, user_id: int) -> Dict:
        """获取知识掌握情况统计"""
        masteries = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id
        ).all()

        if not masteries:
            return {
                "total": 0,
                "mastered": 0,
                "learning": 0,
                "not_started": 0,
                "distribution": []
            }

        # 统计各掌握程度的知识点数量
        mastered = sum(1 for m in masteries if m.mastery_score >= 80)
        learning = sum(1 for m in masteries if 40 <= m.mastery_score < 80)
        not_started = sum(1 for m in masteries if m.mastery_score < 40)

        # 掌握度分布（用于图表）
        distribution = [
            {"level": "未掌握", "count": not_started, "range": "0-40"},
            {"level": "学习中", "count": learning, "range": "40-80"},
            {"level": "已掌握", "count": mastered, "range": "80-100"}
        ]

        return {
            "total": len(masteries),
            "mastered": mastered,
            "learning": learning,
            "not_started": not_started,
            "distribution": distribution
        }

    def _get_course_progress_stats(self, db: Session, user_id: int) -> List[Dict]:
        """获取课程进度统计"""
        from models.db_models import UserCourseProgress

        courses = db.query(Course).filter(
            Course.is_published == True
        ).order_by(
            Course.view_count.desc()
        ).limit(10).all()

        course_stats = []
        for course in courses:
            progress = db.query(UserCourseProgress).filter(
                UserCourseProgress.user_id == user_id,
                UserCourseProgress.course_id == course.id
            ).first()

            course_stats.append({
                "course_id": course.id,
                "course_title": course.title,
                "cover_url": course.cover_url,
                "progress": progress.progress if progress else 0,
                "is_finished": progress.is_finished if progress else False,
                "last_study_time": progress.last_study_time.isoformat() if progress and progress.last_study_time else None
            })

        return course_stats


# 导出单例
personal_dashboard_service = PersonalDashboardService()
