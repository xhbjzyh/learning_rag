
"""
系统配置服务
"""
from sqlalchemy.orm import Session
from models.db_models import SystemConfig
from models.schemas import SystemConfigCreate, SystemConfigUpdate
from fastapi import HTTPException
from utils.logger import logger
from typing import Optional, Dict, Any
import json


class SystemConfigService:
    """系统配置管理服务"""

    def get_config(self, db: Session, config_key: str) -> Optional[SystemConfig]:
        """获取单个配置"""
        return db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key,
            SystemConfig.is_enabled == True
        ).first()

    def get_config_value(self, db: Session, config_key: str, default: str = None) -> Optional[str]:
        """获取配置值"""
        config = self.get_config(db, config_key)
        return config.config_value if config else default

    def get_all_configs(self, db: Session, page: int = 1, size: int = 20):
        """获取所有配置（分页）"""
        query = db.query(SystemConfig)
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return {"total": total, "items": items, "page": page, "size": size}

    def create_config(self, db: Session, data: SystemConfigCreate):
        """创建配置"""
        # 检查配置键是否已存在
        exist = db.query(SystemConfig).filter(
            SystemConfig.config_key == data.config_key
        ).first()
        if exist:
            raise HTTPException(status_code=400, detail=f"配置键 {data.config_key} 已存在")

        config = SystemConfig(**data.model_dump())
        db.add(config)
        db.commit()
        db.refresh(config)
        logger.info(f"✅ 创建系统配置: {config.config_key}")
        return config

    def update_config(self, db: Session, config_id: int, data: SystemConfigUpdate):
        """更新配置"""
        config = db.query(SystemConfig).get(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(config, k, v)

        db.commit()
        db.refresh(config)
        logger.info(f"✅ 更新系统配置: {config.config_key}")
        return config

    def delete_config(self, db: Session, config_id: int):
        """删除配置"""
        config = db.query(SystemConfig).get(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        db.delete(config)
        db.commit()
        logger.info(f"✅ 删除系统配置: {config.config_key}")
        return True

    def init_default_llm_config(self, db: Session):
        """初始化默认的大模型配置"""
        default_configs = [
            {
                "config_key": "llm.provider",
                "config_value": "zhipu",
                "config_type": "string",
                "description": "大模型提供商：zhipu(智谱AI)"
            },
            {
                "config_key": "llm.api_key",
                "config_value": "",
                "config_type": "string",
                "description": "大模型API Key"
            },
            {
                "config_key": "llm.model_name",
                "config_value": "glm-4-flash",
                "config_type": "string",
                "description": "大模型名称"
            },
            {
                "config_key": "llm.timeout",
                "config_value": "100",
                "config_type": "int",
                "description": "大模型调用超时时间（秒）"
            },
            # 🔥 RAG检索配置
            {
                "config_key": "rag.top_k",
                "config_value": "5",
                "config_type": "int",
                "description": "RAG检索返回的知识点数量"
            },
            {
                "config_key": "rag.similarity_threshold",
                "config_value": "0.7",
                "config_type": "float",
                "description": "向量相似度阈值（0-1），越高越严格"
            },
            {
                "config_key": "rag.max_context_length",
                "config_value": "4000",
                "config_type": "int",
                "description": "RAG最大上下文长度（token数）"
            },
            {
                "config_key": "embedding.batch_size",
                "config_value": "32",
                "config_type": "int",
                "description": "向量化批处理大小"
            }
        ]

        for cfg in default_configs:
            exist = db.query(SystemConfig).filter(
                SystemConfig.config_key == cfg["config_key"]
            ).first()
            if not exist:
                config = SystemConfig(**cfg)
                db.add(config)

        db.commit()
        logger.info("✅ 初始化默认大模型和RAG配置完成")


# 全局单例
system_config_service = SystemConfigService()
