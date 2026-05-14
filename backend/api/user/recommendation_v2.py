
"""
推荐系统 API 路由（第二阶段）
提供个性化推荐、相似课程、推荐反馈等接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from models.schemas import (
    SuccessResponse,
    PersonalizedRecommendationRequest,
    PersonalizedRecommendationResponse,
    RecommendationItemResponse,
    SimilarCoursesRequest,
    RecommendationFeedbackCreate
)
from service.user.recommendation_service_v2 import recommendation_service
from utils.response import success_response, error_response
from utils.logger import logger

router = APIRouter(prefix="/recommendation", tags=["推荐系统"])


@router.get("/personalized", summary="获取个性化推荐")
def get_personalized_recommendations(
        query: Optional[str] = Query(None, description="搜索关键词"),
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    """
    获取个性化推荐课程

    - 混合推荐策略：协同过滤 + 内容相似度 + 用户画像
    - 自动保存推荐记录
    - 支持关键词搜索
    """
    try:
        recommendations = recommendation_service.get_personalized_recommendations(
            db=db,
            user_id=current_user.id,
            query=query,
            limit=limit
        )

        # 转换为响应格式
        items = [
            RecommendationItemResponse(
                course_id=rec['course_id'],
                course_title=rec['course_title'],
                score=rec.get('score', 0),
                final_score=rec.get('final_score', 0),
                reason=rec.get('reason', ''),
                recommend_type=rec.get('recommend_type', 'hybrid'),
                weight=rec.get('weight', 0)
            )
            for rec in recommendations
        ]

        response_data = PersonalizedRecommendationResponse(
            recommendations=items,
            total=len(items)
        )

        return success_response(data=response_data.model_dump(), msg="获取推荐成功")

    except Exception as e:
        logger.error(f"获取个性化推荐失败: {e}")
        return error_response(msg=f"获取推荐失败: {str(e)}")


@router.post("/feedback", summary="提交推荐反馈")
def submit_recommendation_feedback(
        feedback: RecommendationFeedbackCreate,
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    """
    提交推荐反馈

    - is_clicked: 是否点击了推荐
    - is_helpful: 推荐是否有用
    - feedback_score: 评分（1-5）
    """
    try:
        from models.db_models import RecommendationRecord

        # 验证推荐记录是否存在
        record = db.query(RecommendationRecord).filter(
            RecommendationRecord.id == feedback.recommendation_id,
            RecommendationRecord.user_id == current_user.id
        ).first()

        if not record:
            return error_response(msg="推荐记录不存在")

        # 更新反馈信息
        record.is_clicked = feedback.is_clicked
        if feedback.is_helpful is not None:
            record.is_helpful = feedback.is_helpful
        if feedback.feedback_score is not None:
            record.feedback_score = feedback.feedback_score

        db.commit()

        logger.info(f"用户 {current_user.id} 提交了推荐反馈: {feedback.recommendation_id}")

        return success_response(msg="反馈提交成功")

    except Exception as e:
        db.rollback()
        logger.error(f"提交推荐反馈失败: {e}")
        return error_response(msg=f"提交反馈失败: {str(e)}")


@router.get("/similar-courses/{course_id}", summary="获取相似课程")
def get_similar_courses(
        course_id: int,
        limit: int = Query(5, ge=1, le=20, description="返回数量"),
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    """
    获取与指定课程相似的课程

    - 基于内容相似度算法
    - 排除用户已学习的课程
    """
    try:
        from core.content_based_recommender import ContentBasedRecommender

        recommender = ContentBasedRecommender(db)
        recommendations = recommender.recommend_similar_courses(
            course_id=course_id,
            user_id=current_user.id,
            limit=limit
        )

        # 转换为响应格式
        items = [
            RecommendationItemResponse(
                course_id=rec['course_id'],
                course_title=rec['course_title'],
                score=rec.get('similarity', 0),
                final_score=rec.get('similarity', 0),
                reason=rec.get('reason', ''),
                recommend_type='content_based',
                weight=1.0
            )
            for rec in recommendations
        ]

        response_data = PersonalizedRecommendationResponse(
            recommendations=items,
            total=len(items)
        )

        return success_response(data=response_data.model_dump(), msg="获取相似课程成功")

    except Exception as e:
        logger.error(f"获取相似课程失败: {e}")
        return error_response(msg=f"获取相似课程失败: {str(e)}")


@router.post("/refresh-similarities", summary="刷新相似度矩阵（管理员）")
def refresh_similarities(
        similarity_type: str = Query("both", description="类型: user/course/both"),
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    """
    手动刷新相似度矩阵（需要管理员权限）

    - user: 刷新用户相似度
    - course: 刷新课程相似度
    - both: 两者都刷新
    """
    try:
        # TODO: 添加管理员权限检查
        # if current_user.role_id != 1:
        #     return error_response(msg="需要管理员权限")

        if similarity_type in ["user", "both"]:
            logger.info("开始刷新用户相似度...")
            recommendation_service.refresh_user_similarities(db)

        if similarity_type in ["course", "both"]:
            logger.info("开始刷新课程相似度...")
            recommendation_service.refresh_course_similarities(db)

        return success_response(msg="相似度刷新成功")

    except Exception as e:
        db.rollback()
        logger.error(f"刷新相似度失败: {e}")
        return error_response(msg=f"刷新失败: {str(e)}")


@router.get("/stats", summary="获取推荐统计信息")
def get_recommendation_stats(
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    """
    获取用户的推荐统计信息

    - 总推荐次数
    - 点击率
    - 有用率
    """
    try:
        from models.db_models import RecommendationRecord
        from sqlalchemy import func

        # 总推荐数
        total_recommendations = db.query(func.count(RecommendationRecord.id)).filter(
            RecommendationRecord.user_id == current_user.id
        ).scalar() or 0

        # 点击数
        clicked_count = db.query(func.count(RecommendationRecord.id)).filter(
            RecommendationRecord.user_id == current_user.id,
            RecommendationRecord.is_clicked == True
        ).scalar() or 0

        # 有用数
        helpful_count = db.query(func.count(RecommendationRecord.id)).filter(
            RecommendationRecord.user_id == current_user.id,
            RecommendationRecord.is_helpful == True
        ).scalar() or 0

        # 计算比率
        click_rate = (clicked_count / total_recommendations * 100) if total_recommendations > 0 else 0
        helpful_rate = (helpful_count / total_recommendations * 100) if total_recommendations > 0 else 0

        stats = {
            "total_recommendations": total_recommendations,
            "clicked_count": clicked_count,
            "helpful_count": helpful_count,
            "click_rate": round(click_rate, 2),
            "helpful_rate": round(helpful_rate, 2)
        }

        return success_response(data=stats, msg="获取统计信息成功")

    except Exception as e:
        logger.error(f"获取推荐统计失败: {e}")
        return error_response(msg=f"获取统计失败: {str(e)}")
