"""
个性化推荐引擎
核心实现：基于用户画像标签权重个性化知识点推荐
设计原则：
1. 冷启动友好：新用户无学习记录时返回默认推荐
2. 动态权重更新：基于用户学习行为实时调整标签权重
3. 基于内容推荐：通过知识点标签匹配，逻辑清晰，适合答辩讲解
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.db_models import KnowledgePoint, UserProfile, UserLearningRecord, KnowledgePointTagRel
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException


class Recommender:
    """个性化推荐引擎类"""

    @staticmethod
    def _update_user_profile(user_id: int, db: Session):
        """
        内部方法：基于用户学习行为，动态更新用户画像标签权重
        权重计算规则（答辩重点讲解）：
        1. 完成学习：+0.2权重
        2. 收藏知识点：+0.3权重
        3. 5分好评：+0.4权重
        4. 1分差评：-0.5权重
        5. 权重归一化到0-1之间
        """
        logger.info(f"开始更新用户{user_id}的画像权重")

        # 1. 查询用户所有学习记录
        learn_records = db.query(UserLearningRecord).filter(
            UserLearningRecord.user_id == user_id
        ).all()
        if not learn_records:
            logger.warning(f"用户{user_id}暂无学习记录，无法更新画像")
            return

        # 2. 统计每个标签的累计权重
        tag_score_map = {}
        for record in learn_records:
            # 查询该知识点的所有标签
            tag_rels = db.query(KnowledgePointTagRel).filter(
                KnowledgePointTagRel.point_id == record.point_id
            ).all()
            if not tag_rels:
                continue

            # 计算单条学习记录的权重增量
            weight_delta = 0.0
            if record.is_finished:
                weight_delta += 0.2
            if record.is_collected:
                weight_delta += 0.3
            if record.feedback_score:
                # 评分1-5分，映射为-0.5到+0.4
                weight_delta += (record.feedback_score - 3) * 0.2

            # 累加到对应标签
            for rel in tag_rels:
                tag_id = str(rel.tag_id)
                if tag_id not in tag_score_map:
                    tag_score_map[tag_id] = 0.0
                tag_score_map[tag_id] += weight_delta

        # 3. 权重归一化到0-1之间
        max_score = max(tag_score_map.values()) if tag_score_map else 1.0
        normalized_weight = {
            tag_id: max(0.0, min(1.0, score / max_score))
            for tag_id, score in tag_score_map.items()
        }

        # 4. 更新/创建用户画像
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if user_profile:
            user_profile.tag_weight = str(normalized_weight)  # 转换为字符串存储
        else:
            user_profile = UserProfile(
                user_id=user_id,
                tag_weight=str(normalized_weight)
            )
            db.add(user_profile)
        db.commit()
        logger.info(f"用户{user_id}画像更新完成，标签数量：{len(normalized_weight)}")

    @staticmethod
    def get_recommend_points(
        user_id: int,
        db: Session,
        top_k: int = 10,
        exclude_learned: bool = True
    ) -> List[KnowledgePoint]:
        """
        核心推荐方法：获取用户的个性化推荐知识点列表
        :param user_id: 用户ID
        :param db: 数据库会话
        :param top_k: 推荐的知识点数量
        :param exclude_learned: 是否排除用户已经学过的知识点
        :return: 推荐的知识点列表
        """
        # 1. 先更新用户画像
        Recommender._update_user_profile(user_id, db)

        # 2. 获取用户画像
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile or not user_profile.tag_weight or user_profile.tag_weight == "{}":
            # 冷启动：用户无画像，返回最新的知识点
            logger.warning(f"用户{user_id}无有效画像，返回默认推荐（最新知识点）")
            base_query = db.query(KnowledgePoint)
            if exclude_learned:
                # 排除已学知识点
                learned_point_ids = db.query(UserLearningRecord.point_id).filter(
                    UserLearningRecord.user_id == user_id
                ).all()
                learned_ids = [item[0] for item in learned_point_ids]
                base_query = base_query.filter(KnowledgePoint.id.not_in(learned_ids))
            return base_query.order_by(KnowledgePoint.create_time.desc()).limit(top_k).all()

        # 3. 解析标签权重字典
        import json
        try:
            tag_weight_dict = json.loads(user_profile.tag_weight)
        except Exception:
            tag_weight_dict = {}

        # 4. 按标签权重排序，获取高权重标签的知识点
        # 标签按权重降序排序
        sorted_tags = sorted(
            tag_weight_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )
        # 取权重>=0.3的高权重标签，或前3个标签
        high_weight_tag_ids = [int(tag_id) for tag_id, weight in sorted_tags if weight >= 0.3]
        if not high_weight_tag_ids:
            high_weight_tag_ids = [int(tag_id) for tag_id, _ in sorted_tags[:3]] if sorted_tags else []

        # 5. 查询高权重标签对应的知识点
        if high_weight_tag_ids:
            # 先获取高权重标签关联的知识点ID，按匹配标签数量排序
            recommend_point_ids = db.query(
                KnowledgePointTagRel.point_id,
                func.count(KnowledgePointTagRel.tag_id).label("tag_match_count")
            ).filter(
                KnowledgePointTagRel.tag_id.in_(high_weight_tag_ids)
            ).group_by(KnowledgePointTagRel.point_id).order_by(func.count(KnowledgePointTagRel.tag_id).desc()).all()

            point_ids = [item[0] for item in recommend_point_ids]
        else:
            point_ids = []

        # 6. 构建查询条件
        base_query = db.query(KnowledgePoint)
        if point_ids:
            base_query = base_query.filter(KnowledgePoint.id.in_(point_ids))
        # 排除已学知识点
        if exclude_learned:
            learned_point_ids = db.query(UserLearningRecord.point_id).filter(
                UserLearningRecord.user_id == user_id
            ).all()
            learned_ids = [item[0] for item in learned_point_ids]
            base_query = base_query.filter(KnowledgePoint.id.not_in(learned_ids))

        # 7. 返回推荐结果
        recommend_points = base_query.limit(top_k).all()
        logger.info(f"为用户{user_id}生成推荐知识点{len(recommend_points)}个")
        return recommend_points


# 全局单例
recommender = Recommender()