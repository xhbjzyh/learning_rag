
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from db.sqlite_conn import get_db
from models.db_models import SystemConfig
from models.schemas import SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse
from service.admin.system_config_service import system_config_service
from utils.logger import logger

router = APIRouter(
    prefix="/system-config",
    tags=["管理员-系统配置"]
)


@router.get("/list", summary="获取系统配置列表")
def get_config_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        data = system_config_service.get_all_configs(db, page, size)
        return {"code": 0, "msg": "获取配置列表成功", "data": data}
    except Exception as e:
        logger.error(f"获取配置列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置列表失败")


@router.get("/{config_key}", summary="获取单个配置")
def get_config(config_key: str, db: Session = Depends(get_db)):
    try:
        config = system_config_service.get_config(db, config_key)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        return {"code": 0, "msg": "获取配置成功", "data": config}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/create", summary="创建系统配置")
def create_config(data: SystemConfigCreate, db: Session = Depends(get_db)):
    try:
        config = system_config_service.create_config(db, data)
        return {"code": 0, "msg": "创建配置成功", "data": config}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"创建配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建配置失败")


@router.put("/update/{config_id}", summary="更新系统配置")
def update_config(config_id: int, data: SystemConfigUpdate, db: Session = Depends(get_db)):
    try:
        config = system_config_service.update_config(db, config_id, data)
        return {"code": 0, "msg": "更新配置成功", "data": config}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新配置失败")


@router.delete("/delete/{config_id}", summary="删除系统配置")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    try:
        system_config_service.delete_config(db, config_id)
        return {"code": 0, "msg": "删除配置成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除配置失败")


@router.post("/init-llm-config", summary="初始化大模型默认配置")
def init_llm_config(db: Session = Depends(get_db)):
    try:
        system_config_service.init_default_llm_config(db)
        return {"code": 0, "msg": "初始化大模型配置成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"初始化大模型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="初始化失败")
