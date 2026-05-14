
"""
管理员仪表盘统计接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.sqlite_conn import get_db
from service.admin.stats_service import admin_stats_service
from utils.logger import logger

router = APIRouter(prefix="/stats", tags=["管理员-仪表盘统计"])


@router.get("/dashboard", summary="获取仪表盘统计数据")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取管理员仪表盘统计数据"""
    try:
        stats = admin_stats_service.get_dashboard_stats(db)
        return {"code": 0, "msg": "获取成功", "data": stats}
    except Exception as e:
        logger.error(f"获取仪表盘统计数据失败: {str(e)}")
        return {"code": 500, "msg": f"获取失败: {str(e)}", "data": None}
