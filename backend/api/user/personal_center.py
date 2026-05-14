"""
用户-个人中心接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from db.sqlite_conn import get_db
from service.user.personal_dashboard_service import personal_dashboard_service
from utils.response import success_response

router = APIRouter(
    prefix="/personal",
    tags=["用户-个人中心"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/dashboard", summary="个人中心仪表盘")
async def get_personal_dashboard(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户仪表盘数据"""
    dashboard_data = personal_dashboard_service.get_dashboard_data(db, current_user.id)
    return success_response(data=dashboard_data, msg="获取仪表盘数据成功")
