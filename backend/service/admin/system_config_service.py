"""
管理员-系统配置业务逻辑
"""
from typing import Dict
from utils.logger import logger


class SystemConfigService:
    """系统配置服务类"""

    # 系统默认配置
    _default_config = {
        "llm_model": "glm-4",
        "llm_temperature": 0.7,
        "llm_max_tokens": 2048,
        "recommend_top_k": 10,
        "learning_path_max_length": 10,
        "system_announcement": "欢迎使用基于RAG的个性化学习推荐系统！",
        "file_upload_max_size": 10 * 1024 * 1024,  # 10MB
        "allowed_file_types": ["txt", "pdf", "docx"]
    }

    # 内存中的配置
    _config = _default_config.copy()

    @staticmethod
    def get_system_config() -> Dict:
        """
        获取系统配置
        """
        return SystemConfigService._config

    @staticmethod
    def update_system_config(new_config: Dict) -> Dict:
        """
        更新系统配置
        """
        for key, value in new_config.items():
            if key in SystemConfigService._config:
                SystemConfigService._config[key] = value
                logger.info(f"系统配置更新: {key} = {value}")

        return SystemConfigService._config


system_config_service = SystemConfigService()