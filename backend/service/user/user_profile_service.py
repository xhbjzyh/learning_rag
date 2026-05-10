"""
用户画像与行为收集服务（合并版）
整合：行为收集 + 答题画像 + 行为画像 + 用户画像引擎
一个文件搞定所有用户画像相关功能
"""
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.db_models import (
    UserProfile, UserKnowledgeMastery, KnowledgePoint,
    UserExerciseRecord, WrongQuestion, KnowledgeTag, KnowledgePointTagRel,
    UserCourseBehavior, UserLearningRecord, UserResourceProgress,
    UserInterestTag, UserLearningPreference, CourseTag, CourseTagRel,
    CourseResource, Exercise
)
from utils.logger import logger
from db.sqlite_conn import SessionLocal


# ==================== 用户画像引擎核心（后台异步更新） ====================
class UserProfileEngine:
    def __init__(self):
        self.update_queue = set()
        self.lock = threading.Lock()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def schedule_update(self, user_id: int):
        """调度用户画像更新（异步）"""
        with self.lock:
            self.update_queue.add(user_id)

    def _worker(self):
        """后台工作线程，处理用户画像更新"""
        while True:
            user_id = None
            with self.lock:
                if self.update_queue:
                    user_id = self.update_queue.pop()

            if user_id:
                try:
                    db = SessionLocal()
                    self._update_behavior_profile(db, user_id)
                    db.close()
                except Exception as e:
                    logger.error(f"更新用户行为画像失败: {e}")

            # 休眠1秒，避免CPU占用过高
            threading.Event().wait(1)

    def _update_behavior_profile(self, db: Session, user_id: int):
        """更新用户行为画像（兴趣标签 + 学习偏好）"""
        # 1. 更新兴趣标签
        self._update_interest_tags(db, user_id)

        # 2. 更新学习偏好
        self._update_learning_preference(db, user_id)

    def _update_interest_tags(self, db: Session, user_id: int):
        """更新用户兴趣标签权重"""
        # 1. 获取用户最近30天的课程行为
        thirty_days_ago = datetime.now() - timedelta(days=30)
        behaviors = db.query(UserCourseBehavior).filter(
            UserCourseBehavior.user_id == user_id,
            UserCourseBehavior.create_time >= thirty_days_ago
        ).all()

        # 2. 计算每个课程的行为权重
        course_weights = {}
        for behavior in behaviors:
            weight = {
                "view": 0.1,
                "collect": 0.3,
                "rate": 0.2 * (behavior.behavior_value or 3) / 5,
                "share": 0.4,
                "complete": 0.5
            }.get(behavior.behavior_type, 0.05)

            course_weights[behavior.course_id] = course_weights.get(behavior.course_id, 0) + weight

        # 3. 计算标签权重
        tag_weights = {}
        for course_id, course_weight in course_weights.items():
            # 获取课程标签
            tags = db.query(CourseTag).join(CourseTagRel).filter(
                CourseTagRel.course_id == course_id
            ).all()

            for tag in tags:
                tag_weights[tag.id] = tag_weights.get(tag.id, 0) + course_weight * tag.weight

        # 4. 归一化标签权重（0-1）
        if tag_weights:
            max_weight = max(tag_weights.values())
            for tag_id in tag_weights:
                tag_weights[tag_id] = tag_weights[tag_id] / max_weight

        # 5. 更新数据库
        for tag_id, weight in tag_weights.items():
            interest_tag = db.query(UserInterestTag).filter(
                UserInterestTag.user_id == user_id,
                UserInterestTag.tag_id == tag_id
            ).first()

            if not interest_tag:
                interest_tag = UserInterestTag(
                    user_id=user_id,
                    tag_id=tag_id
                )
                db.add(interest_tag)

            # 平滑更新：保留30%旧值，70%新值
            interest_tag.weight = interest_tag.weight * 0.3 + weight * 0.7
            interest_tag.last_updated = datetime.now()

        db.commit()
        logger.info(f"用户 {user_id} 兴趣标签已更新")

    def _update_learning_preference(self, db: Session, user_id: int):
        """更新用户学习偏好"""
        # 1. 查找或创建学习偏好记录
        preference = db.query(UserLearningPreference).filter(
            UserLearningPreference.user_id == user_id
        ).first()

        if not preference:
            preference = UserLearningPreference(user_id=user_id)
            db.add(preference)

        # 2. 计算学习时段偏好
        self._calculate_time_preference(db, user_id, preference)

        # 3. 计算资源类型偏好
        self._calculate_resource_preference(db, user_id, preference)

        # 4. 计算难度偏好
        self._calculate_difficulty_preference(db, user_id, preference)

        # 5. 计算平均学习时长
        self._calculate_average_session_duration(db, user_id, preference)

        db.commit()
        logger.info(f"用户 {user_id} 学习偏好已更新")

    def _calculate_time_preference(self, db: Session, user_id: int, preference):
        """计算学习时段偏好"""
        # 获取用户最近7天的学习记录
        seven_days_ago = datetime.now() - timedelta(days=7)
        records = db.query(UserLearningRecord).filter(
            UserLearningRecord.user_id == user_id,
            UserLearningRecord.create_time >= seven_days_ago
        ).all()

        time_counts = {
            "morning": 0,  # 6-12
            "afternoon": 0,  # 12-18
            "evening": 0,  # 18-24
            "night": 0  # 0-6
        }

        for record in records:
            hour = record.create_time.hour
            if 6 <= hour < 12:
                time_counts["morning"] += 1
            elif 12 <= hour < 18:
                time_counts["afternoon"] += 1
            elif 18 <= hour < 24:
                time_counts["evening"] += 1
            else:
                time_counts["night"] += 1

        total = sum(time_counts.values()) or 1
        preference.preferred_time_morning = time_counts["morning"] / total
        preference.preferred_time_afternoon = time_counts["afternoon"] / total
        preference.preferred_time_evening = time_counts["evening"] / total
        preference.preferred_time_night = time_counts["night"] / total

    def _calculate_resource_preference(self, db: Session, user_id: int, preference):
        """计算资源类型偏好"""
        # 获取用户所有资源进度
        progresses = db.query(UserResourceProgress).join(CourseResource).filter(
            UserResourceProgress.user_id == user_id
        ).all()

        type_counts = {
            "video": 0,
            "book": 0,
            "exercise": 0
        }

        for progress in progresses:
            if progress.resource.type == "video":
                type_counts["video"] += progress.progress / 100
            elif progress.resource.type in ["book", "document"]:
                type_counts["book"] += progress.progress / 100

        # 习题偏好从答题记录计算
        exercise_count = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id
        ).count()
        type_counts["exercise"] = min(exercise_count / 100, 1.0)

        total = sum(type_counts.values()) or 1
        preference.preferred_type_video = type_counts["video"] / total
        preference.preferred_type_book = type_counts["book"] / total
        preference.preferred_type_exercise = type_counts["exercise"] / total

    def _calculate_difficulty_preference(self, db: Session, user_id: int, preference):
        """计算难度偏好"""
        # 从答题记录计算
        records = db.query(UserExerciseRecord).join(Exercise).filter(
            UserExerciseRecord.user_id == user_id
        ).all()

        difficulty_counts = {
            "easy": 0,
            "medium": 0,
            "hard": 0
        }

        for record in records:
            if record.exercise.difficulty == "简单":
                difficulty_counts["easy"] += 1 if record.is_correct else 0.5
            elif record.exercise.difficulty == "中等":
                difficulty_counts["medium"] += 1 if record.is_correct else 0.5
            elif record.exercise.difficulty == "困难":
                difficulty_counts["hard"] += 1 if record.is_correct else 0.5

        total = sum(difficulty_counts.values()) or 1
        preference.preferred_difficulty_easy = difficulty_counts["easy"] / total
        preference.preferred_difficulty_medium = difficulty_counts["medium"] / total
        preference.preferred_difficulty_hard = difficulty_counts["hard"] / total

    def _calculate_average_session_duration(self, db: Session, user_id: int, preference):
        """计算平均单次学习时长"""
        # 从学习记录计算
        records = db.query(UserLearningRecord).filter(
            UserLearningRecord.user_id == user_id,
            UserLearningRecord.learn_duration > 0
        ).limit(100).all()

        if records:
            total_duration = sum(r.learn_duration for r in records)
            preference.average_session_duration = total_duration // len(records)


# 全局单例
user_profile_engine = UserProfileEngine()


# ==================== 用户行为收集服务 ====================
class UserBehaviorService:
    @staticmethod
    def record_course_behavior(db: Session, user_id: int, course_id: int, behavior_type: str, behavior_value: float = None):
        """记录用户课程级行为"""
        # 1. 记录行为
        behavior = UserCourseBehavior(
            user_id=user_id,
            course_id=course_id,
            behavior_type=behavior_type,
            behavior_value=behavior_value
        )
        db.add(behavior)
        db.commit()

        # 2. 异步触发用户画像更新
        user_profile_engine.schedule_update(user_id)

        logger.info(f"用户 {user_id} 课程行为已记录: {behavior_type}")
        return behavior

    @staticmethod
    def record_knowledge_behavior(db: Session, user_id: int, point_id: int, behavior_type: str, behavior_value: float = None):
        """记录用户知识点级行为（复用现有UserLearningRecord）"""
        # 1. 复用现有UserLearningRecord表
        record = UserLearningRecord(
            user_id=user_id,
            point_id=point_id,
            learn_duration=behavior_value if behavior_type == "view" else 0,
            feedback_score=behavior_value if behavior_type == "rate" else None,
            is_collected=(behavior_type == "collect"),
            is_finished=(behavior_type == "complete")
        )
        db.add(record)
        db.commit()

        # 2. 异步触发用户画像更新
        user_profile_engine.schedule_update(user_id)

        logger.info(f"用户 {user_id} 知识点行为已记录: {behavior_type}")
        return record

    @staticmethod
    def record_resource_behavior(db: Session, user_id: int, resource_id: int, behavior_type: str, behavior_value: float = None):
        """记录用户资源级行为（复用现有UserResourceProgress）"""
        # 1. 查找或创建资源进度记录
        progress = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.resource_id == resource_id
        ).first()

        if not progress:
            progress = UserResourceProgress(
                user_id=user_id,
                resource_id=resource_id
            )
            db.add(progress)

        # 2. 更新进度
        if behavior_type == "view":
            progress.progress = behavior_value or 0
            progress.watch_duration += behavior_value or 0
        elif behavior_type == "complete":
            progress.progress = 100
            progress.is_finished = True

        progress.last_study_time = datetime.now()
        db.commit()

        # 3. 异步触发用户画像更新
        user_profile_engine.schedule_update(user_id)

        logger.info(f"用户 {user_id} 资源行为已记录: {behavior_type}")
        return progress

    @staticmethod
    def get_user_behavior_history(db: Session, user_id: int, limit: int = 100):
        """获取用户行为历史"""
        return db.query(UserCourseBehavior).filter(
            UserCourseBehavior.user_id == user_id
        ).order_by(UserCourseBehavior.create_time.desc()).limit(limit).all()


# ==================== 原有答题画像服务（保留并增强） ====================
class UserAnswerProfileService:
    def get_user_answer_profile(self, user_id: int, db: Session) -> Dict:
        """获取用户答题画像（原有功能，完全保留）"""
        # 1. 获取基础画像
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not profile:
            # 如果没有画像，创建一个
            profile = UserProfile(
                user_id=user_id,
                current_level="入门",
                preferred_difficulty="中等"
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        # 2. 动态计算统计数据
        stats = self._calculate_user_stats(user_id, db)

        # 3. 分析薄弱/优势知识点
        weak_tags, strong_tags = self._analyze_weak_strong_tags(user_id, db)

        # 4. 更新画像（如果有变化）
        self._update_profile_from_stats(profile, stats, weak_tags, strong_tags, db)

        return {
            "user_id": profile.user_id,
            "total_study_duration": profile.total_study_duration,
            "finished_points_count": profile.finished_points_count,
            "current_level": profile.current_level,
            "preferred_difficulty": profile.preferred_difficulty,
            "average_score": stats.get("average_score", 0.0),
            "total_questions": stats.get("total_questions", 0),
            "correct_rate": stats.get("correct_rate", 0.0),
            "weak_tags": weak_tags,
            "strong_tags": strong_tags,
            "create_time": profile.create_time,
            "update_time": profile.update_time
        }

    def _calculate_user_stats(self, user_id: int, db: Session) -> Dict:
        """计算用户答题统计数据"""
        # 1. 答题记录统计
        records = db.query(UserExerciseRecord).filter(UserExerciseRecord.user_id == user_id).all()

        total_questions = len(records)
        if total_questions == 0:
            return {
                "total_questions": 0,
                "correct_count": 0,
                "correct_rate": 0.0,
                "total_score": 0.0,
                "average_score": 0.0,
                "total_answer_time": 0
            }

        correct_count = sum(1 for r in records if r.is_correct)
        total_score = sum(r.score or 0 for r in records)
        total_answer_time = sum(r.answer_time or 0 for r in records)

        return {
            "total_questions": total_questions,
            "correct_count": correct_count,
            "correct_rate": round(correct_count / total_questions * 100, 2),
            "total_score": total_score,
            "average_score": round(total_score / total_questions, 2),
            "total_answer_time": total_answer_time
        }

    def _analyze_weak_strong_tags(self, user_id: int, db: Session) -> (List[Dict], List[Dict]):
        """分析用户的薄弱标签和优势标签"""
        # 1. 获取用户所有知识点掌握度
        masteries = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id
        ).all()

        if not masteries:
            return [], []

        # 2. 按标签分组统计
        tag_stats = {}

        for mastery in masteries:
            # 获取知识点的标签
            tags = db.query(KnowledgeTag).join(
                KnowledgePointTagRel,
                KnowledgeTag.id == KnowledgePointTagRel.tag_id
            ).filter(
                KnowledgePointTagRel.point_id == mastery.knowledge_point_id
            ).all()

            for tag in tags:
                if tag.id not in tag_stats:
                    tag_stats[tag.id] = {
                        "tag_id": tag.id,
                        "tag_name": tag.name,
                        "total_mastery": 0,
                        "count": 0
                    }
                tag_stats[tag.id]["total_mastery"] += mastery.mastery_score
                tag_stats[tag.id]["count"] += 1

        # 3. 计算平均掌握度
        for tag_id in tag_stats:
            tag_stats[tag_id]["avg_mastery"] = round(
                tag_stats[tag_id]["total_mastery"] / tag_stats[tag_id]["count"],
                2
            )

        # 4. 排序并分类
        sorted_tags = sorted(tag_stats.values(), key=lambda x: x["avg_mastery"])

        # 薄弱标签：掌握度最低的3个
        weak_tags = sorted_tags[:3]
        # 优势标签：掌握度最高的3个
        strong_tags = sorted_tags[-3:][::-1]

        return weak_tags, strong_tags

    def _update_profile_from_stats(
        self,
        profile: UserProfile,
        stats: Dict,
        weak_tags: List[Dict],
        strong_tags: List[Dict],
        db: Session
    ):
        """根据统计数据更新用户画像"""
        # 1. 更新学习等级
        correct_rate = stats.get("correct_rate", 0)
        if correct_rate >= 90:
            profile.current_level = "精通"
        elif correct_rate >= 70:
            profile.current_level = "熟练掌握"
        elif correct_rate >= 40:
            profile.current_level = "初步掌握"
        else:
            profile.current_level = "入门"

        # 2. 更新偏好难度
        avg_score = stats.get("average_score", 0)
        if avg_score >= 9:
            profile.preferred_difficulty = "困难"
        elif avg_score >= 6:
            profile.preferred_difficulty = "中等"
        else:
            profile.preferred_difficulty = "简单"

        # 3. 更新统计数据
        profile.total_study_duration = stats.get("total_answer_time", 0)
        profile.average_score = stats.get("average_score", 0.0)

        # 4. 更新薄弱/优势标签
        profile.weak_tags = json.dumps([t["tag_name"] for t in weak_tags], ensure_ascii=False)
        profile.strong_tags = json.dumps([t["tag_name"] for t in strong_tags], ensure_ascii=False)

        # 5. 计算已完成知识点数量
        finished_count = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == profile.user_id,
            UserKnowledgeMastery.level == "精通"
        ).count()
        profile.finished_points_count = finished_count

        db.commit()
        logger.info(f"用户 {profile.user_id} 答题画像已更新")

    def update_profile_after_answer(self, user_id: int, db: Session):
        """答题后更新用户画像（在答题记录服务中调用）"""
        # 简单调用 get_user_answer_profile 就会触发更新
        self.get_user_answer_profile(user_id, db)


# ==================== 合并后的完整用户画像服务 ====================
class UserProfileService:
    def __init__(self):
        self.answer_service = UserAnswerProfileService()
        self.behavior_service = UserBehaviorService()

    def get_complete_user_profile(self, db: Session, user_id: int) -> Dict:
        """获取完整用户画像（答题画像 + 行为画像）"""
        # 1. 获取答题画像（原有功能）
        answer_profile = self.answer_service.get_user_answer_profile(user_id, db)

        # 2. 获取行为画像（新增功能）
        behavior_profile = self._get_user_behavior_profile(db, user_id)

        # 3. 合并两个画像
        return {
            **answer_profile,
            "behavior_profile": behavior_profile
        }

    def _get_user_behavior_profile(self, db: Session, user_id: int) -> Dict:
        """获取用户行为画像"""
        # 1. 兴趣标签
        interest_tags = db.query(UserInterestTag, CourseTag).join(CourseTag).filter(
            UserInterestTag.user_id == user_id
        ).order_by(UserInterestTag.weight.desc()).limit(20).all()

        # 2. 学习偏好
        learning_preference = db.query(UserLearningPreference).filter(
            UserLearningPreference.user_id == user_id
        ).first()

        return {
            "interest_tags": [
                {
                    "id": tag.CourseTag.id,
                    "name": tag.CourseTag.name,
                    "weight": tag.UserInterestTag.weight
                } for tag in interest_tags
            ],
            "learning_preference": learning_preference
        }

    def force_update_all_profiles(self, db: Session, user_id: int):
        """强制更新所有画像"""
        # 1. 更新答题画像
        self.answer_service.update_profile_after_answer(user_id, db)

        # 2. 更新行为画像
        user_profile_engine.schedule_update(user_id)

        return True


# 导出单例实例（与你原有风格一致）
user_profile_service = UserProfileService()
user_behavior_service = UserBehaviorService()
# 在文件最后添加
def get_user_weak_tags(db: Session, user_id: int, limit: int = 10):
    """兼容方法：供推荐服务调用获取薄弱标签"""
    profile = user_profile_service.answer_service.get_user_answer_profile(user_id, db)
    return profile.get("weak_tags", [])[:limit]