"""
用户画像API接口（合并版）
整合：画像查询 + 行为上报
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from service.user.user_profile_service import user_profile_service, user_behavior_service
from utils.response import success_response

router = APIRouter(
    prefix="/profile",
    tags=["用户-个人中心"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", summary="获取完整用户画像")
def get_complete_user_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取完整用户画像（答题画像 + 行为画像）"""
    profile = user_profile_service.get_complete_user_profile(
        db=db,
        user_id=current_user.id
    )
    return success_response(data=profile, msg="获取用户画像成功")


@router.post("/update", summary="强制更新所有画像")
def force_update_all_profiles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """强制更新所有画像"""
    user_profile_service.force_update_all_profiles(
        db=db,
        user_id=current_user.id
    )
    return success_response(msg="所有画像更新任务已提交")


@router.get("/weak-tags", summary="获取用户薄弱标签")
def get_user_weak_tags(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取用户薄弱标签"""
    profile = user_profile_service.answer_service.get_user_answer_profile(current_user.id, db)
    return success_response(data=profile.get("weak_tags", [])[:limit], msg="获取薄弱标签成功")


@router.get("/strong-tags", summary="获取用户优势标签")
def get_user_strong_tags(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取用户优势标签"""
    profile = user_profile_service.answer_service.get_user_answer_profile(current_user.id, db)
    return success_response(data=profile.get("strong_tags", [])[:limit], msg="获取优势标签成功")


@router.get("/interest-tags", summary="获取用户兴趣标签")
def get_user_interest_tags(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取用户兴趣标签"""
    # 🔥 修正：通过公共方法获取，不直接调用私有方法
    behavior_profile = user_profile_service.get_complete_user_profile(db, current_user.id).get("behavior_profile", {})
    return success_response(data=behavior_profile.get("interest_tags", [])[:limit], msg="获取兴趣标签成功")


# 行为上报API（合并到这里）
@router.post("/behavior/course/{course_id}/{behavior_type}", summary="记录课程行为")
def record_course_behavior(
    course_id: int,
    behavior_type: str,
    behavior_value: float = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """记录用户课程行为"""
    behavior = user_behavior_service.record_course_behavior(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        behavior_type=behavior_type,
        behavior_value=behavior_value
    )
    return success_response(data=behavior.id, msg="行为记录成功")


@router.post("/behavior/knowledge/{point_id}/{behavior_type}", summary="记录知识点行为")
def record_knowledge_behavior(
    point_id: int,
    behavior_type: str,
    behavior_value: float = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """记录用户知识点行为"""
    behavior = user_behavior_service.record_knowledge_behavior(
        db=db,
        user_id=current_user.id,
        point_id=point_id,
        behavior_type=behavior_type,
        behavior_value=behavior_value
    )
    return success_response(data=behavior.id, msg="行为记录成功")


@router.post("/behavior/resource/{resource_id}/{behavior_type}", summary="记录资源行为")
def record_resource_behavior(
    resource_id: int,
    behavior_type: str,
    behavior_value: float = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """记录用户资源行为"""
    behavior = user_behavior_service.record_resource_behavior(
        db=db,
        user_id=current_user.id,
        resource_id=resource_id,
        behavior_type=behavior_type,
        behavior_value=behavior_value
    )
    return success_response(data=behavior.id, msg="行为记录成功")