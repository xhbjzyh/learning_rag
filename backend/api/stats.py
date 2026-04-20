"""
系统统计接口
仅管理员/审核员可访问
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser, KnowledgePoint
from utils.response import success_response, BusinessException

router = APIRouter(tags=["系统统计模块"])

# ==================== 权限校验：仅管理员/审核员可访问 ====================
def check_admin_permission(current_user):
    if current_user.role_id not in [1, 2]:
        raise BusinessException(code=403, msg="您没有权限访问该接口")

# ==================== 获取系统概览统计 ====================
@router.get(
    "/stats/overview",
    summary="获取系统概览统计数据",
    description="仅管理员/审核员可访问"
)
async def get_stats_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 校验权限
    check_admin_permission(current_user)

    # 统计数据（仅使用你已有的数据库模型）
    user_count = db.query(func.count(SysUser.id)).scalar() # 注册用户总数
    knowledge_count = db.query(func.count(KnowledgePoint.id)).scalar() # 知识点总数
    online_count = 15 # 在线人数（后续可对接在线用户逻辑）
    chat_count = 0 # 问答次数（后续新增问答记录表后可统计）

    return success_response(
        data={
            "user_count": user_count,
            "knowledge_count": knowledge_count,
            "online_count": online_count,
            "chat_count": chat_count
        },
        msg="获取统计数据成功"
    )