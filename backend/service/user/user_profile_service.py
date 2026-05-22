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
    CourseResource, Exercise, UserLearningHistory, UserFeedback, 
    RecommendationRecord
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
            "videos": 0,
            "book": 0,
            "exercise": 0
        }

        for progress in progresses:
            if progress.resource.type == "videos":
                type_counts["videos"] += progress.progress / 100
            elif progress.resource.type in ["book", "document"]:
                type_counts["book"] += progress.progress / 100

        # 习题偏好从答题记录计算
        exercise_count = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id
        ).count()
        type_counts["exercise"] = min(exercise_count / 100, 1.0)

        total = sum(type_counts.values()) or 1
        preference.preferred_type_video = type_counts["videos"] / total
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

        # 3. 🔥 核心修复：实时计算总学习时长，不依赖缓存
        total_study_duration = self._calculate_total_study_duration(user_id, db)
        
        logger.info(f"🔥 用户 {user_id} 学习时长调试 - 计算值: {total_study_duration}, 类型: {type(total_study_duration)}")
        logger.info(f"🔥 UserProfile表中的值: {profile.total_study_duration}")
        
        # 4. 分析薄弱/优势知识点
        weak_tags, strong_tags = self._analyze_weak_strong_tags(user_id, db)

        # 5. 更新画像（如果有变化）
        self._update_profile_from_stats(profile, stats, weak_tags, strong_tags, db, total_study_duration)

        result = {
            "user_id": profile.user_id,
            "total_study_duration": total_study_duration,
            "finished_points_count": profile.finished_points_count,
            "current_level": profile.current_level,
            "preferred_difficulty": profile.preferred_difficulty,
            "average_score": stats.get("average_score", 0.0),
            "total_questions": stats.get("total_questions", 0),
            "correct_rate": stats.get("correct_rate", 0.0),
            "weak_tags": weak_tags,
            "strong_tags": strong_tags,
            "create_time": profile.create_time.isoformat() if hasattr(profile.create_time, 'isoformat') else str(profile.create_time),
            "update_time": profile.update_time.isoformat() if hasattr(profile.update_time, 'isoformat') else str(profile.update_time)
        }
        
        logger.info(f"🔥 返回给前端的数据: {result}")
        
        return result

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

    def _calculate_total_study_duration(self, user_id: int, db: Session) -> int:
        """
        计算用户总学习时长（秒）
        🔥 修复：从多个数据源汇总学习时长
        - user_resource_progress: 视频/文档学习时长
        - learning_progress: 知识点学习时长  
        - user_learning_record: 学习记录时长
        """
        from models.db_models import UserResourceProgress, LearningProgress, UserLearningRecord
        
        # 1. 从 user_resource_progress 获取视频/文档学习时长
        resource_duration = db.query(func.sum(UserResourceProgress.total_study_duration)).filter(
            UserResourceProgress.user_id == user_id
        ).scalar() or 0
        
        # 2. 从 learning_progress 获取知识点学习时长
        learning_duration = db.query(func.sum(LearningProgress.study_duration)).filter(
            LearningProgress.user_id == user_id
        ).scalar() or 0
        
        # 3. 从 user_learning_record 获取学习记录时长
        record_duration = db.query(func.sum(UserLearningRecord.learn_duration)).filter(
            UserLearningRecord.user_id == user_id
        ).scalar() or 0
        
        # 返回最大值的作为总时长（避免重复计算）
        # 通常 resource_duration 是最准确的视频学习时长
        total_duration = max(resource_duration, learning_duration, record_duration)
        
        logger.info(f"用户 {user_id} 学习时长统计 - 资源: {resource_duration}s, 知识点: {learning_duration}s, 记录: {record_duration}s, 总计: {total_duration}s")
        
        return total_duration

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
        db: Session,
        total_study_duration: int = None
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

        # 3. 🔥 核心修复：使用传入的学习时长或重新计算
        if total_study_duration is None:
            total_study_duration = self._calculate_total_study_duration(profile.user_id, db)
        
        profile.total_study_duration = total_study_duration
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
        logger.info(f"用户 {profile.user_id} 答题画像已更新，总学习时长: {total_study_duration}秒")

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
        # 🔥 论文第2.4.3节：先应用掌握度衰减
        self._apply_mastery_decay_to_all(db, user_id)
        
        # 1. 获取答题画像（原有功能）
        answer_profile = self.answer_service.get_user_answer_profile(user_id, db)

        # 2. 获取行为画像（新增功能）
        behavior_profile = self._get_user_behavior_profile(db, user_id)

        # 3. 合并两个画像
        return {
            **answer_profile,
            "behavior_profile": behavior_profile
        }

    def _apply_mastery_decay_to_all(self, db: Session, user_id: int):
        """
        对用户的所有掌握度应用衰减（论文第2.4.3节）
        
        公式：S_t = S_0 * e^(λt)
        其中 λ = -0.05/天（衰减系数）
        
        实际实现：mastery_score * 0.95 ** days
        （数学上等价于 e^(-0.0513 * days) ≈ 0.95^days）
        """
        import math
        from datetime import datetime
        
        masteries = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.mastery_score > 0  # 只对已有掌握度的应用衰减
        ).all()
        
        decay_rate = -0.05  # 每天衰减5%
        updated_count = 0
        
        for mastery in masteries:
            if not mastery.update_time:
                continue
            
            # 计算距离上次更新的天数
            last_update = mastery.update_time
            if isinstance(last_update, datetime):
                days_since_update = (datetime.now() - last_update).days
            else:
                try:
                    last_update_dt = datetime.strptime(str(last_update), "%Y-%m-%d %H:%M:%S")
                    days_since_update = (datetime.now() - last_update_dt).days
                except:
                    continue
            
            if days_since_update <= 0:
                continue
            
            # 应用衰减公式：S_t = S_0 * e^(λt)
            old_score = mastery.mastery_score
            decay_factor = math.exp(decay_rate * days_since_update)
            
            # 或者使用简化版本：S_t = S_0 * 0.95^days
            # decay_factor = 0.95 ** days_since_update
            
            new_score = old_score * decay_factor
            
            # 确保不低于0
            mastery.mastery_score = max(0, new_score)
            
            # 更新等级
            if mastery.mastery_score < 40:
                mastery.level = "未掌握"
            elif mastery.mastery_score < 70:
                mastery.level = "基本掌握"
            else:
                mastery.level = "已掌握"
            
            updated_count += 1
            
            logger.debug(f"📉 掌握度衰减: 知识点{mastery.knowledge_point_id}, "
                        f"{days_since_update}天, {old_score:.1f} → {new_score:.1f}")
        
        if updated_count > 0:
            db.commit()
            logger.info(f"✅ 已对用户 {user_id} 的 {updated_count} 个知识点应用掌握度衰减")

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


# ==================== 增强行为服务（第一阶段优化）====================
class EnhancedBehaviorService:
    """增强行为服务（第一阶段优化）"""
    
    def __init__(self):
        self.behavior_service = UserBehaviorService()
    
    # 🔥 新增：掌握度衰减计算（论文第2.4.3节）
    def _apply_mastery_decay(self, db: Session, user_id: int, mastery: UserKnowledgeMastery):
        """
        应用掌握度衰减公式（论文第2.4.3节）
        
        公式：S_t = S_0 * e^(λt)
        
        其中：
        - S_t: t时刻的掌握度
        - S_0: 初始掌握度（上次学习时的掌握度）
        - λ: 衰减系数（负数），默认为-0.05/天
        - t: 距离上次学习的天数
        
        实际实现：mastery_score * 0.95 ** days
        （数学上等价于 e^(-0.0513 * days) ≈ 0.95^days）
        """
        import math
        from datetime import datetime
        
        # 获取衰减系数（默认-0.05/天）
        decay_rate = -0.05
        
        # 计算距离上次学习的时间（天数）
        if mastery.update_time:
            last_update = mastery.update_time
            if isinstance(last_update, datetime):
                days_since_update = (datetime.now() - last_update).days
            else:
                # 如果是字符串，需要转换
                last_update_dt = datetime.strptime(str(last_update), "%Y-%m-%d %H:%M:%S")
                days_since_update = (datetime.now() - last_update_dt).days
        else:
            # 如果没有更新时间，假设是昨天
            days_since_update = 1
        
        # 应用衰减公式：S_t = S_0 * e^(λt)
        decay_factor = math.exp(decay_rate * days_since_update)
        
        # 或者使用简化版本：S_t = S_0 * 0.95^days
        # decay_factor = 0.95 ** days_since_update
        
        # 更新掌握度
        old_score = mastery.mastery_score
        new_score = old_score * decay_factor
        
        # 确保不低于0
        mastery.mastery_score = max(0, new_score)
        
        # 更新等级
        if mastery.mastery_score < 40:
            mastery.level = "未掌握"
        elif mastery.mastery_score < 70:
            mastery.level = "基本掌握"
        else:
            mastery.level = "已掌握"
        
        logger.info(f"📉 掌握度衰减: 用户{user_id}, 知识点{mastery.knowledge_point_id}, "
                   f"{days_since_update}天, {old_score:.1f} → {new_score:.1f} "
                   f"(衰减系数: {decay_factor:.3f})")
    
    def apply_decay_to_all_mastery(self, db: Session, user_id: int):
        """
        对用户的所有掌握度应用衰减
        
        建议在每次查询用户画像时调用此方法，确保掌握度反映最新状态
        """
        masteries = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.mastery_score > 0  # 只对已有掌握度的应用衰减
        ).all()
        
        for mastery in masteries:
            self._apply_mastery_decay(db, user_id, mastery)
        
        db.commit()
        logger.info(f"✅ 已对用户 {user_id} 的 {len(masteries)} 个知识点应用掌握度衰减")

    def record_learning_session(self, db: Session, user_id: int, session_data: dict):
        """
        记录学习会话
        同时记录到 user_learning_history 和 user_learning_record
        """
        from models.db_models import UserLearningHistory, UserLearningRecord
        
        point_id = session_data.get('point_id')
        duration = session_data.get('duration', 0)
        is_mastered = session_data.get('is_mastered', False)
        session_type = session_data.get('session_type', 'study')
        notes = session_data.get('notes')
        
        # 1. 记录到 user_learning_history
        history = UserLearningHistory(
            user_id=user_id,
            point_id=point_id,
            study_duration=duration,
            is_mastered=1 if is_mastered else 0,
            session_type=session_type
        )
        db.add(history)
        
        # 2. 更新或创建 user_learning_record
        if point_id:
            record = db.query(UserLearningRecord).filter(
                UserLearningRecord.user_id == user_id,
                UserLearningRecord.point_id == point_id
            ).first()
            
            if record:
                # 累加学习时长
                record.learn_duration = (record.learn_duration or 0) + duration
                record.update_time = datetime.now()
            else:
                record = UserLearningRecord(
                    user_id=user_id,
                    point_id=point_id,
                    learn_duration=duration,
                    is_finished=is_mastered
                )
                db.add(record)
        
        db.commit()
        db.refresh(history)
        
        logger.info(f"用户 {user_id} 学习会话已记录: point_id={point_id}, duration={duration}s")
        return history
    
    def get_smart_recommendations(self, db: Session, user_id: int, limit: int = 5) -> list:
        """
        🔥 第五步核心功能：智能推荐（混合策略 - 论文第4.3节实现）
        
        统一使用HybridRecommender，实现：
        - 协同过滤（User-CF）
        - 内容推荐（Content-Based）
        - 用户画像推荐
        - 动态权重调整
        
        替代旧的简单规则推荐（薄弱知识点、兴趣标签等）
        """
        from core.hybrid_recommender import HybridRecommender
        
        try:
            recommender = HybridRecommender(db)
            recommendations = recommender.get_personalized_recommendations(
                user_id=user_id,
                limit=limit
            )
            
            logger.info(f"✅ 为用户 {user_id} 生成 {len(recommendations)} 个混合推荐")
            return recommendations
        except Exception as e:
            logger.error(f"❌ 智能推荐失败: {str(e)}")
            return []
    
    def get_user_behavior_analysis(self, db: Session, user_id: int) -> dict:
        """
        🔥 第四步核心功能：获取用户行为分析
        包含：学习习惯、薄弱标签、连续学习天数、学习效果预测
        """
        from models.db_models import UserLearningHistory, UserKnowledgeMastery, KnowledgeTag
        
        # 1. 学习时段分析
        time_preference = self._analyze_learning_time(db, user_id)
        
        # 2. 资源类型偏好
        resource_preference = self._analyze_resource_preference(db, user_id)
        
        # 3. 薄弱知识点标签
        weak_tags = self._identify_weak_tags(db, user_id)
        
        # 4. 连续学习天数
        consecutive_days = self._calculate_consecutive_days(db, user_id)
        
        # 5. 学习效果预测
        learning_prediction = self._predict_learning_outcome(db, user_id)
        
        return {
            "time_preference": time_preference,
            "resource_preference": resource_preference,
            "weak_tags": weak_tags,
            "consecutive_days": consecutive_days,
            "learning_prediction": learning_prediction
        }
    
    def _analyze_learning_time(self, db: Session, user_id: int) -> dict:
        """分析用户学习时段偏好"""
        recent_records = db.query(UserLearningHistory).filter(
            UserLearningHistory.user_id == user_id,
            UserLearningHistory.create_time >= datetime.now() - timedelta(days=30)
        ).all()
        
        time_slots = {
            "morning": {"count": 0, "duration": 0},  # 6-12点
            "afternoon": {"count": 0, "duration": 0},  # 12-18点
            "evening": {"count": 0, "duration": 0},  # 18-24点
            "night": {"count": 0, "duration": 0}  # 0-6点
        }
        
        for record in recent_records:
            hour = record.create_time.hour
            duration = record.study_duration or 0
            
            if 6 <= hour < 12:
                time_slots["morning"]["count"] += 1
                time_slots["morning"]["duration"] += duration
            elif 12 <= hour < 18:
                time_slots["afternoon"]["count"] += 1
                time_slots["afternoon"]["duration"] += duration
            elif 18 <= hour < 24:
                time_slots["evening"]["count"] += 1
                time_slots["evening"]["duration"] += duration
            else:
                time_slots["night"]["count"] += 1
                time_slots["night"]["duration"] += duration
        
        # 找出最佳学习时段
        best_slot = max(time_slots.items(), key=lambda x: x[1]["duration"])
        
        return {
            "distribution": time_slots,
            "best_time": best_slot[0],
            "total_sessions": sum(v["count"] for v in time_slots.values())
        }
    
    def _analyze_resource_preference(self, db: Session, user_id: int) -> dict:
        """分析用户资源类型偏好"""
        from models.db_models import UserResourceProgress, CourseResource
        
        progresses = db.query(UserResourceProgress).join(CourseResource).filter(
            UserResourceProgress.user_id == user_id
        ).all()
        
        type_stats = {
            "video": {"count": 0, "total_duration": 0, "avg_completion": 0},
            "document": {"count": 0, "total_duration": 0, "avg_completion": 0},
            "exercise": {"count": 0, "total_duration": 0, "avg_completion": 0}
        }
        
        for progress in progresses:
            resource_type = progress.resource.type
            
            if resource_type == "videos":
                type_key = "video"
            elif resource_type in ["book", "document"]:
                type_key = "document"
            else:
                continue
            
            type_stats[type_key]["count"] += 1
            type_stats[type_key]["total_duration"] += progress.total_study_duration or 0
            type_stats[type_key]["avg_completion"] += progress.progress or 0
        
        # 计算平均值
        for type_key in type_stats:
            count = type_stats[type_key]["count"]
            if count > 0:
                type_stats[type_key]["avg_completion"] /= count
        
        # 找出偏好类型
        preferred_type = max(type_stats.items(), key=lambda x: x[1]["count"])
        
        return {
            "statistics": type_stats,
            "preferred_type": preferred_type[0],
            "total_resources": sum(v["count"] for v in type_stats.values())
        }
    
    def _identify_weak_tags(self, db: Session, user_id: int, limit: int = 5) -> list:
        """识别薄弱知识点标签"""
        # 获取用户掌握度较低的知识点
        weak_points = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.mastery_score < 60
        ).order_by(UserKnowledgeMastery.mastery_score.asc()).limit(20).all()
        
        if not weak_points:
            return []
        
        # 统计薄弱知识点的标签
        tag_scores = {}
        
        for mastery in weak_points:
            # 获取知识点关联的标签
            tags = db.query(KnowledgeTag).join(
                KnowledgePointTagRel,
                KnowledgeTag.id == KnowledgePointTagRel.tag_id
            ).filter(
                KnowledgePointTagRel.point_id == mastery.knowledge_point_id
            ).all()
            
            for tag in tags:
                if tag.id not in tag_scores:
                    tag_scores[tag.id] = {
                        "tag_id": tag.id,
                        "tag_name": tag.name,
                        "category": tag.category,
                        "weak_count": 0,
                        "avg_mastery": 0,
                        "total_mastery": 0
                    }
                
                tag_scores[tag.id]["weak_count"] += 1
                tag_scores[tag.id]["total_mastery"] += mastery.mastery_score
        
        # 计算平均掌握度
        for tag_id in tag_scores:
            tag_scores[tag_id]["avg_mastery"] = round(
                tag_scores[tag_id]["total_mastery"] / tag_scores[tag_id]["weak_count"],
                2
            )
        
        # 按薄弱程度排序（薄弱数量多且掌握度低的优先）
        sorted_tags = sorted(
            tag_scores.values(),
            key=lambda x: (x["weak_count"], -x["avg_mastery"]),
            reverse=True
        )
        
        return sorted_tags[:limit]
    
    def _calculate_consecutive_days(self, db: Session, user_id: int) -> int:
        """计算连续学习天数"""
        recent_records = db.query(UserLearningHistory).filter(
            UserLearningHistory.user_id == user_id
        ).order_by(UserLearningHistory.create_time.desc()).all()
        
        if not recent_records:
            return 0
        
        consecutive_days = 0
        last_date = recent_records[0].create_time.date()
        today = datetime.now().date()
        
        # 检查是否从今天或昨天开始
        if (today - last_date).days > 1:
            return 0
        
        consecutive_days = 1
        
        for record in recent_records[1:]:
            current_date = record.create_time.date()
            
            if (last_date - current_date).days == 1:
                consecutive_days += 1
                last_date = current_date
            elif (last_date - current_date).days == 0:
                # 同一天，跳过
                continue
            else:
                # 中断
                break
        
        return consecutive_days
    
    def _predict_learning_outcome(self, db: Session, user_id: int) -> dict:
        """预测学习效果"""
        from models.db_models import UserKnowledgeMastery
        
        # 获取所有知识点的掌握情况
        masteries = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id
        ).all()
        
        if not masteries:
            return {
                "current_level": "入门",
                "predicted_level": "初步掌握",
                "estimated_days": 30,
                "confidence": 0.5
            }
        
        # 计算当前整体水平
        total_mastery = sum(m.mastery_score for m in masteries)
        avg_mastery = total_mastery / len(masteries)
        
        # 确定当前等级
        if avg_mastery >= 90:
            current_level = "精通"
        elif avg_mastery >= 70:
            current_level = "熟练"
        elif avg_mastery >= 50:
            current_level = "进阶"
        elif avg_mastery >= 30:
            current_level = "基础"
        else:
            current_level = "入门"
        
        # 预测下一等级所需时间（基于历史数据简化估算）
        next_level_thresholds = {
            "入门": 30,
            "基础": 50,
            "进阶": 70,
            "熟练": 90,
            "精通": 100
        }
        
        next_level = {
            "入门": "基础",
            "基础": "进阶",
            "进阶": "熟练",
            "熟练": "精通",
            "精通": "大师"
        }.get(current_level, "大师")
        
        target_mastery = next_level_thresholds.get(next_level, 100)
        remaining_mastery = target_mastery - avg_mastery
        
        # 假设每天提升1-2分（简化估算）
        estimated_days = max(7, int(remaining_mastery / 1.5))
        
        # 置信度（基于学习记录数量）
        confidence = min(0.9, 0.5 + len(masteries) * 0.02)
        
        return {
            "current_level": current_level,
            "predicted_level": next_level,
            "estimated_days": estimated_days,
            "confidence": round(confidence, 2),
            "current_avg_mastery": round(avg_mastery, 2)
        }
    
    def submit_user_feedback(self, db: Session, user_id: int, feedback_data: dict):
        """提交用户反馈"""
        from models.db_models import UserFeedback
        
        feedback = UserFeedback(
            user_id=user_id,
            point_id=feedback_data.get('point_id'),
            course_id=feedback_data.get('course_id'),
            feedback_type=feedback_data.get('feedback_type', 'rating'),
            feedback_content=feedback_data.get('feedback_content'),
            rating=feedback_data.get('rating')
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"用户 {user_id} 反馈已提交")
        return feedback
    
    def submit_recommendation_feedback(self, db: Session, user_id: int, feedback_data: dict):
        """提交推荐反馈"""
        recommendation_id = feedback_data.get('recommendation_id')
        is_clicked = feedback_data.get('is_clicked', False)
        is_completed = feedback_data.get('is_completed', False)
        rating = feedback_data.get('rating')
        
        record = db.query(RecommendationRecord).filter(
            RecommendationRecord.id == recommendation_id,
            RecommendationRecord.user_id == user_id
        ).first()
        
        if not record:
            return None
        
        record.is_clicked = is_clicked
        record.is_completed = is_completed
        record.rating = rating
        record.feedback_time = datetime.now()
        
        db.commit()
        
        logger.info(f"用户 {user_id} 推荐反馈已提交: recommendation_id={recommendation_id}")
        return True
    
    def get_user_behavior_stats(self, db: Session, user_id: int) -> dict:
        """获取用户行为统计"""
        from models.db_models import UserLearningHistory
        
        total_sessions = db.query(UserLearningHistory).filter(
            UserLearningHistory.user_id == user_id
        ).count()
        
        total_duration = db.query(func.sum(UserLearningHistory.study_duration)).filter(
            UserLearningHistory.user_id == user_id
        ).scalar() or 0
        
        mastered_points = db.query(UserLearningHistory).filter(
            UserLearningHistory.user_id == user_id,
            UserLearningHistory.is_mastered == 1
        ).count()
        
        consecutive_days = self._calculate_consecutive_days(db, user_id)
        
        return {
            "total_sessions": total_sessions,
            "total_duration": total_duration,
            "mastered_points": mastered_points,
            "consecutive_days": consecutive_days
        }


# 导出增强行为服务单例
enhanced_behavior_service = EnhancedBehaviorService()


# 在文件最后添加
def get_user_weak_tags(db: Session, user_id: int, limit: int = 10):
    """兼容方法：供推荐服务调用获取薄弱标签"""
    profile = user_profile_service.answer_service.get_user_answer_profile(user_id, db)
    return profile.get("weak_tags", [])[:limit]