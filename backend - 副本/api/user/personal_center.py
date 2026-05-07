"""
用户-个人中心接口
"""
from fastapi import APIRouter, Depends
from middleware.auth_middleware import get_current_user

router = APIRouter(
    prefix="/personal",
    tags=["用户-个人中心"],
    dependencies=[Depends(get_current_user)]
)


# 个人中心主要调用 auth_service 的接口，这里可以预留个人中心特有的接口
@router.get("/dashboard", summary="个人中心仪表盘")
async def get_personal_dashboard():
    return {"msg": "个人中心仪表盘接口，后续实现"}