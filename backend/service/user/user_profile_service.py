"""
用户画像业务服务
功能：获取用户画像、更新用户画像（基于答题情况）
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.db_models import (
    UserProfile, UserKnowledgeMastery, KnowledgePoint,
    UserExerciseRecord, WrongQuestion, KnowledgeTag, KnowledgePointTagRel
)
from utils.logger import logger
import json


class UserProfileService:

    def get_user_profile(self, user_id: int, db: Session) -> Dict:
        """获取用户画像（包含动态计算的统计数据）"""
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
        logger.info(f"用户 {profile.user_id} 画像已更新")

    def update_profile_after_answer(self, user_id: int, db: Session):
        """答题后更新用户画像（在答题记录服务中调用）"""
        # 简单调用 get_user_profile 就会触发更新
        self.get_user_profile(user_id, db)


user_profile_service = UserProfileService()