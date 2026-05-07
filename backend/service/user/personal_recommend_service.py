"""
个性化推荐业务服务
功能：基于用户画像的个性化知识点推荐、学习路径生成
使用：与RAG问答一致的线上大模型 glm-4-flash
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from models.db_models import (
    KnowledgePoint, UserKnowledgeMastery, KnowledgeTag,
    KnowledgePointTagRel, UserProfile, UserExerciseRecord, WrongQuestion
)
from utils.logger import logger
import json

# 🔥 核心修改：直接导入RAG使用的线上大模型（和问答完全一致）
from core.llm import llm


class PersonalRecommendService:

    def __init__(self):
        # 🔥 直接使用线上大模型，无需本地加载！
        self._llm = llm
        logger.info("✅ 推荐服务已加载线上大模型(glm-4-flash)，与RAG问答共用")

    @property
    def llm(self):
        """直接返回线上大模型，无懒加载、无本地依赖"""
        return self._llm

    def get_personal_recommend(self, user_id: int, db: Session, top_k: int = 10) -> List[Dict]:
        """获取个性化推荐知识点（结合大模型）"""
        # 1. 获取基础数据
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        mastered_point_ids = db.query(UserKnowledgeMastery.knowledge_point_id).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.level.in_(["熟练掌握", "精通"])
        ).all()
        mastered_point_ids = [p[0] for p in mastered_point_ids]

        # 2. 先用规则获取候选集
        candidates = self._get_rule_based_candidates(profile, mastered_point_ids, db, top_k * 2)

        # 3. 线上大模型重排序
        if self.llm and candidates:
            try:
                candidates = self._rerank_with_llm(user_id, candidates, profile, db)
            except Exception as e:
                logger.warning(f"⚠️ 大模型重排序失败: {e}，使用规则推荐结果")

        # 4. 返回前top_k个
        result = candidates[:top_k]
        logger.info(f"为用户 {user_id} 生成了 {len(result)} 个个性化推荐")
        return result

    def generate_learning_path(self, user_id: int, db: Session, max_length: int = 10) -> List[Dict]:
        """生成个性化学习路径（结合大模型）"""
        # 1. 获取基础数据
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        masteries = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id
        ).all()
        mastery_dict = {m.knowledge_point_id: m for m in masteries}

        # 2. 先用规则生成基础路径
        learning_path = self._get_rule_based_learning_path(profile, mastery_dict, db, max_length)

        # 3. 线上大模型优化路径
        if self.llm and learning_path:
            try:
                learning_path = self._optimize_path_with_llm(user_id, learning_path, profile, db)
            except Exception as e:
                logger.warning(f"⚠️ 大模型路径优化失败: {e}，使用规则路径")

        logger.info(f"为用户 {user_id} 生成了长度为 {len(learning_path)} 的学习路径")
        return learning_path

    def _get_rule_based_candidates(
        self,
        profile: Optional[UserProfile],
        exclude_ids: List[int],
        db: Session,
        count: int
    ) -> List[Dict]:
        """规则推荐：获取候选知识点"""
        candidates = []
        weak_tags = self._parse_tags(profile.weak_tags) if profile else []
        strong_tags = self._parse_tags(profile.strong_tags) if profile else []

        # 优先推荐薄弱标签相关的知识点
        if weak_tags:
            weak_candidates = self._get_points_by_tags(weak_tags, exclude_ids, db)
            candidates.extend(weak_candidates[:count//2])

        # 补充推荐优势标签相关的进阶知识点
        if strong_tags:
            strong_candidates = self._get_points_by_tags(
                strong_tags,
                exclude_ids,
                db,
                difficulty="困难" if profile and profile.preferred_difficulty == "困难" else "中等"
            )
            candidates.extend(strong_candidates[:count//2])

        # 补充热门推荐
        if len(candidates) < count:
            hot_candidates = self._get_hot_recommendations(
                db,
                count - len(candidates),
                exclude_ids=[c["id"] for c in candidates] + exclude_ids
            )
            candidates.extend(hot_candidates)

        # 最后兜底：返回所有知识点
        if len(candidates) < count:
            all_candidates = self._get_hot_recommendations(
                db,
                count - len(candidates),
                exclude_ids=[]
            )
            candidates.extend(all_candidates)

        return candidates

    def _get_rule_based_learning_path(
        self,
        profile: Optional[UserProfile],
        mastery_dict: Dict,
        db: Session,
        max_length: int
    ) -> List[Dict]:
        """规则推荐：生成基础学习路径"""
        learning_path = []
        visited_ids = set()
        weak_tags = self._parse_tags(profile.weak_tags) if profile else []

        if weak_tags:
            # 从薄弱标签的基础知识点开始
            start_points = self._get_points_by_tags(
                weak_tags,
                [],
                db,
                difficulty="简单"
            )

            if start_points:
                current_point = start_points[0]
                current_point["order"] = 1
                current_point["reason"] = "从你的薄弱知识点开始"
                learning_path.append(current_point)
                visited_ids.add(current_point["id"])

                # 构建路径
                while len(learning_path) < max_length:
                    next_points = self._get_next_points(
                        current_point["id"],
                        visited_ids,
                        db,
                        profile.preferred_difficulty if profile else "中等"
                    )

                    if not next_points:
                        break

                    next_point = min(
                        next_points,
                        key=lambda p: mastery_dict.get(p["id"], None).mastery_score if mastery_dict.get(p["id"]) else 0
                    )

                    next_point["order"] = len(learning_path) + 1
                    next_point["reason"] = "基于前置知识推荐"
                    learning_path.append(next_point)
                    visited_ids.add(next_point["id"])
                    current_point = next_point

        # 补充热门知识点
        if len(learning_path) < max_length:
            hot_points = self._get_hot_recommendations(
                db,
                max_length - len(learning_path),
                exclude_ids=list(visited_ids)
            )

            for i, point in enumerate(hot_points):
                point["order"] = len(learning_path) + 1
                point["reason"] = "热门推荐"
                learning_path.append(point)

        # 最后兜底
        if len(learning_path) < max_length:
            all_points = self._get_hot_recommendations(
                db,
                max_length - len(learning_path),
                exclude_ids=[]
            )

            for i, point in enumerate(all_points):
                point["order"] = len(learning_path) + 1
                point["reason"] = "基础知识点"
                learning_path.append(point)

        return learning_path

    def _rerank_with_llm(
            self,
            user_id: int,
            candidates: List[Dict],
            profile: Optional[UserProfile],
            db: Session
    ) -> List[Dict]:
        """用线上大模型重排序候选知识点"""
        # 1. 获取用户学习数据
        recent_records = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id
        ).order_by(UserExerciseRecord.create_time.desc()).limit(5).all()

        wrong_questions = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == user_id
        ).limit(3).all()

        # 2. 构建提示词
        candidate_titles = [c["title"] for c in candidates]
        user_context = self._build_user_context(profile, recent_records, wrong_questions)

        prompt = f"""你是一个智能学习推荐助手。请根据用户的学习情况，从以下知识点中选择最合适的推荐顺序，并为每个知识点生成个性化的推荐理由。

    【用户学习情况】
    {user_context}

    【候选知识点】
    {candidate_titles}

    请按以下JSON格式返回（只返回JSON，不要其他文字）：
    {{
        "recommendations": [
            {{
                "title": "知识点标题",
                "reason": "为什么推荐给这个用户的个性化理由（50字以内）"
            }}
        ]
    }}"""

        # 3. 调用RAG同款线上大模型 ✅修复点
        logger.info(f"🤖 调用线上大模型(glm-4-flash)进行推荐重排序...")
        response = self.llm.chat(prompt)
        # 4. 解析大模型返回
        try:
            result_text = response.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].strip()

            result = json.loads(result_text)

            # 5. 匹配候选知识点并添加理由
            recommendations = result.get("recommendations", [])
            title_to_reason = {r["title"]: r["reason"] for r in recommendations}

            reranked = []
            for rec in recommendations:
                for candidate in candidates:
                    if candidate["title"] == rec["title"]:
                        candidate["reason"] = rec["reason"]
                        reranked.append(candidate)
                        break

            for candidate in candidates:
                if candidate not in reranked:
                    candidate["reason"] = "智能推荐"
                    reranked.append(candidate)

            logger.info("✅ 大模型重排序完成")
            return reranked

        except Exception as e:
            logger.warning(f"⚠️ 解析大模型返回失败: {e}")
            for candidate in candidates:
                candidate["reason"] = "智能推荐"
            return candidates

    def _optimize_path_with_llm(
            self,
            user_id: int,
            learning_path: List[Dict],
            profile: Optional[UserProfile],
            db: Session
    ) -> List[Dict]:
        """用线上大模型优化学习路径"""
        recent_records = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id
        ).order_by(UserExerciseRecord.create_time.desc()).limit(5).all()

        path_titles = [p["title"] for p in learning_path]
        user_context = self._build_user_context(profile, recent_records, [])

        prompt = f"""你是一个智能学习路径规划助手。请根据用户的学习情况，优化以下学习路径，并为每个知识点生成学习建议。

    【用户学习情况】
    {user_context}

    【当前学习路径】
    {path_titles}

    请按以下JSON格式返回（只返回JSON，不要其他文字）：
    {{
        "learning_path": [
            {{
                "title": "知识点标题",
                "order": 1,
                "reason": "为什么放在这里（30字以内）",
                "suggestion": "学习这个知识点的建议（50字以内）"
            }}
        ]
    }}"""

        # 调用线上大模型 ✅修复点
        logger.info(f"🤖 调用线上大模型(glm-4-flash)优化学习路径...")
        response = self.llm.chat(prompt)  # 这里改了！

        try:
            result_text = response.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].strip()

            result = json.loads(result_text)
            optimized_path = result.get("learning_path", [])
            title_to_info = {p["title"]: p for p in optimized_path}

            final_path = []
            for opt in optimized_path:
                for point in learning_path:
                    if point["title"] == opt["title"]:
                        point["order"] = opt["order"]
                        point["reason"] = opt.get("reason", point.get("reason", ""))
                        point["suggestion"] = opt.get("suggestion", "")
                        final_path.append(point)
                        break

            final_path.sort(key=lambda x: x["order"])
            logger.info("✅ 大模型学习路径优化完成")
            return final_path

        except Exception as e:
            logger.warning(f"⚠️ 解析大模型返回失败: {e}")
            return learning_path

    def _build_user_context(
        self,
        profile: Optional[UserProfile],
        recent_records: List,
        wrong_questions: List
    ) -> str:
        """构建用户上下文描述"""
        context_parts = []

        if profile:
            context_parts.append(f"学习等级：{profile.current_level}")
            context_parts.append(f"偏好难度：{profile.preferred_difficulty}")
            if profile.weak_tags:
                context_parts.append(f"薄弱标签：{profile.weak_tags}")
            if profile.strong_tags:
                context_parts.append(f"优势标签：{profile.strong_tags}")

        if recent_records:
            recent_titles = [f"习题：{r.exercise_id}（{'正确' if r.is_correct else '错误'}）" for r in recent_records]
            context_parts.append(f"最近答题：{', '.join(recent_titles)}")

        if wrong_questions:
            wrong_titles = [w.question[:20] + "..." for w in wrong_questions]
            context_parts.append(f"错题本：{', '.join(wrong_titles)}")

        return "\n".join(context_parts) if context_parts else "新用户，暂无学习数据"

    def _parse_tags(self, tags_json: Optional[str]) -> List[str]:
        """解析JSON格式的标签"""
        if not tags_json:
            return []
        try:
            return json.loads(tags_json)
        except:
            return []

    def _get_points_by_tags(
        self,
        tag_names: List[str],
        exclude_ids: List[int],
        db: Session,
        difficulty: Optional[str] = None
    ) -> List[Dict]:
        """根据标签获取知识点"""
        query = db.query(KnowledgePoint).join(
            KnowledgePointTagRel,
            KnowledgePoint.id == KnowledgePointTagRel.point_id
        ).join(
            KnowledgeTag,
            KnowledgePointTagRel.tag_id == KnowledgeTag.id
        ).filter(
            KnowledgeTag.name.in_(tag_names),
            KnowledgePoint.id.not_in(exclude_ids)
        )

        if difficulty:
            query = query.filter(KnowledgePoint.difficulty == difficulty)

        points = query.order_by(KnowledgePoint.difficulty).limit(20).all()

        return [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content[:100] + "..." if len(p.content) > 100 else p.content,
                "difficulty": p.difficulty,
                "key_points": p.key_points,
                "doc_id": p.doc_id
            }
            for p in points
        ]

    def _get_next_points(
        self,
        current_point_id: int,
        exclude_ids: List[int],
        db: Session,
        preferred_difficulty: str
    ) -> List[Dict]:
        """获取后续知识点（基于前置知识）"""
        current_tags = db.query(KnowledgeTag).join(
            KnowledgePointTagRel,
            KnowledgeTag.id == KnowledgePointTagRel.tag_id
        ).filter(
            KnowledgePointTagRel.point_id == current_point_id
        ).all()

        tag_names = [t.name for t in current_tags]

        return self._get_points_by_tags(tag_names, exclude_ids, db, preferred_difficulty)

    def _get_hot_recommendations(
        self,
        db: Session,
        top_k: int,
        exclude_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """获取热门推荐（当没有用户画像时使用）"""
        query = db.query(KnowledgePoint)

        if exclude_ids:
            query = query.filter(KnowledgePoint.id.not_in(exclude_ids))

        points = query.order_by(KnowledgePoint.create_time.desc()).limit(top_k).all()

        return [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content[:100] + "..." if len(p.content) > 100 else p.content,
                "difficulty": p.difficulty,
                "key_points": p.key_points,
                "doc_id": p.doc_id
            }
            for p in points
        ]


personal_recommend_service = PersonalRecommendService()