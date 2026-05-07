"""
管理员-系统审计接口
"""
from fastapi import APIRouter, Depends
from middleware.auth_middleware import role_required

router = APIRouter(
    prefix="/audit",
    tags=["管理员-系统审计"],
    dependencies=[Depends(role_required([1]))]
)


@router.get("/logs", summary="操作日志查询")
async def get_operation_logs():
    return {"msg": "操作日志接口，后续实现"}