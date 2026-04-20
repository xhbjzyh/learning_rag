"""
个性化推荐接口
提供学习行为采集、个性化推荐、学习历史查询、用户画像查询接口
设计原则：
1. 仅做参数接收、响应返回，不写业务逻辑
2. 统一使用依赖注入（当前用户、数据库会话）
3. 统一响应格式，使用success_response
4. 接口文档注释完整，适合/docs展示
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from service.recommend_service import recommend_service
from utils.response import success_response, ApiResponse

router = APIRouter()


@router.post(
    "/learn/record",
    summary="新增/更新学习记录",
    description="采集用户学习行为（学习时长、收藏、评分），用于更新用户画像",
    tags=["个性化推荐模块"],
    response_model=ApiResponse
)
async def add_learning_record(
    point_id: int = Query(..., description="知识点ID", ge=1),
    learn_duration: int = Query(0, description="本次学习时长，单位：秒", ge=0),
    is_collected: bool = Query(False, description="是否收藏该知识点"),
    feedback_score: int = Query(None, description="用户反馈评分，1-5分，5分最感兴趣", ge=1, le=5),
    is_finished: bool = Query(False, description="是否完成该知识点的学习"),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新增/更新学习记录接口
    前置条件：用户已登录
    """
    record_data = {
        "learn_duration": learn_duration,
        "is_collected": is_collected,
        "feedback_score": feedback_score,
        "is_finished": is_finished
    }
    record = recommend_service.add_learning_record(
        user_id=current_user.id,
        point_id=point_id,
        record_data=record_data,
        db=db
    )
    return success_response(data=record, msg="学习记录更新成功")


@router.get(
    "/personal",
    summary="获取个性化推荐知识点",
    description="基于用户画像标签权重，返回个性化推荐的学习知识点",
    tags=["个性化推荐模块"],
    response_model=ApiResponse
)
async def get_personal_recommend(
    top_k: int = Query(10, description="推荐的知识点数量", ge=1, le=20),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取个性化推荐接口
    前置条件：用户已登录
    冷启动处理：新用户无学习记录时，返回最新的知识点
    """
    recommend_list = recommend_service.get_personal_recommend(
        user_id=current_user.id,
        db=db,
        top_k=top_k
    )
    return success_response(
        data=recommend_list,
        msg="个性化推荐生成成功"
    )


@router.get(
    "/learn/history",
    summary="获取用户学习历史",
    description="查询当前用户的所有学习记录，按更新时间倒序排列",
    tags=["个性化推荐模块"],
    response_model=ApiResponse
)
async def get_learn_history(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取学习历史接口
    前置条件：用户已登录
    """
    history = recommend_service.get_user_learn_history(
        user_id=current_user.id,
        db=db
    )
    return success_response(data=history, msg="学习历史查询成功")


@router.get(
    "/profile",
    summary="获取用户画像",
    description="查询当前用户的画像信息，包括标签权重、学习进度等",
    tags=["个性化推荐模块"],
    response_model=ApiResponse
)
async def get_user_profile(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户画像接口
    前置条件：用户已登录
    """
    profile = recommend_service.get_user_profile(
        user_id=current_user.id,
        db=db
    )
    return success_response(data=profile, msg="用户画像查询成功")