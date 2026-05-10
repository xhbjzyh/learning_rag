"""
用户-个性化推荐接口（异步优化版）
新增：学习路径生成
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from utils.response import success_response
# 🔥 修正：导入正确的服务单例
from service.user.recommendation_service import user_recommendation_service

router = APIRouter(
    prefix="/recommendation",
    tags=["用户-个性化推荐"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "/personal",
    summary="获取个性化推荐知识点",
    description="基于用户画像标签权重，优先推荐薄弱知识点"
)
def get_personal_recommend(
    top_k: int = Query(10, description="推荐的知识点数量", ge=1, le=20),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 🔥 修正：去掉await，服务方法是同步的
    recommend_list = user_recommendation_service.get_personalized_recommendations(
        db=db,
        user_id=current_user.id,
        limit=top_k
    )
    return success_response(data=recommend_list, msg="个性化推荐生成成功")


@router.get(
    "/learning-path",
    summary="生成个性化学习路径",
    description="基于用户学习进度和薄弱点，生成循序渐进的学习顺序"
)
def generate_learning_path(
    target_point_id: int = Query(..., description="目标知识点ID"),
    max_length: int = Query(10, description="学习路径最大长度", ge=1, le=20),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 🔥 修正：去掉await，服务方法是同步的
    learning_path = user_recommendation_service.get_learning_path(
        db=db,
        user_id=current_user.id,
        target_point_id=target_point_id
    )
    return success_response(data=learning_path, msg="学习路径生成成功")


@router.get(
    "/weak-points",
    summary="获取薄弱点专项推荐",
    description="基于三源融合掌握度的精准薄弱点推荐"
)
def get_weak_points_recommendation(
    limit: int = Query(5, description="推荐数量", ge=1, le=10),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    weak_points = user_recommendation_service.get_weak_points_recommendation(
        db=db,
        user_id=current_user.id,
        limit=limit
    )
    return success_response(data=weak_points, msg="薄弱点推荐生成成功")