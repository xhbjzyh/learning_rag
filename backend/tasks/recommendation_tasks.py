"""
D:\projects\learning_rag\backend\tasks\recommendation_tasks.py
异步推荐任务
"""
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from utils.logger import logger


async def update_user_recommendations_async(
        db: Session,
        user_id: int,
        background_tasks: BackgroundTasks
):
    """异步更新用户推荐（不阻塞主流程）"""

    def _do_update():
        try:
            from service.user.user_profile_service import enhanced_behavior_service

            # 预计算推荐结果并缓存
            recommendations = enhanced_behavior_service.get_smart_recommendations(
                db=db,
                user_id=user_id,
                limit=10
            )

            # 缓存推荐结果
            from utils.cache import cache_service
            cache_key = f"user:recommendations:{user_id}"
            cache_service.set(cache_key, recommendations, ttl=600)  # 10分钟

            logger.info(f"✅ 用户 {user_id} 推荐已异步更新")
        except Exception as e:
            logger.error(f"❌ 异步更新推荐失败: {e}")

    # 添加到后台任务
    background_tasks.add_task(_do_update)
