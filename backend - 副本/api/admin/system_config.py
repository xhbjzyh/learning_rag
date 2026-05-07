"""
管理员-系统配置接口
"""
from fastapi import APIRouter, Depends, Body
from middleware.auth_middleware import role_required
from service.admin.system_config_service import system_config_service
from utils.response import success_response, ApiResponse

router = APIRouter(
    prefix="/system",
    tags=["管理员-系统配置"],
    dependencies=[Depends(role_required([1]))]
)


@router.get(
    "/config",
    summary="获取系统配置",
    response_model=ApiResponse
)
async def get_system_config():
    return success_response(
        data=system_config_service.get_system_config(),
        msg="获取系统配置成功"
    )


@router.post(
    "/config",
    summary="更新系统配置",
    response_model=ApiResponse
)
async def update_system_config(
    new_config: dict = Body(..., description="新的系统配置")
):
    return success_response(
        data=system_config_service.update_system_config(new_config),
        msg="系统配置更新成功"
    )