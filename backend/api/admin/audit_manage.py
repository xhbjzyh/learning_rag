"""
管理员-审核全局管理接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import role_required

router = APIRouter(
    prefix="/audit",
    tags=["管理员-审核管理"],
    dependencies=[Depends(role_required([1]))]
)


# 预留接口，后续可添加审核统计、审核规则配置等
@router.get("/stats", summary="审核统计")
async def get_audit_stats():
    return {"msg": "审核统计接口，后续实现"}