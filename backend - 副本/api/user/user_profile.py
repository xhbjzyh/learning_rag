"""
用户-用户画像接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from service.user.user_profile_service import user_profile_service
from utils.response import success_response, ApiResponse

router = APIRouter(
    prefix="/profile",
    tags=["用户-用户画像"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "",
    summary="获取用户画像",
    description="查询当前用户的画像信息",
    response_model=ApiResponse
)
async def get_user_profile(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = user_profile_service.get_user_profile(
        user_id=current_user.id,
        db=db
    )
    return success_response(data=profile, msg="用户画像查询成功")