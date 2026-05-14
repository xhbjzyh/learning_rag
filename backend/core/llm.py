"""
智谱AI大模型调用引擎（异步版 + 超时控制 + 动态配置）
"""
# ==================== 标准库导入 ====================
import asyncio
from typing import Optional

# ==================== 第三方库导入 ====================
from zhipuai import ZhipuAI

# ==================== 内部模块导入 ====================
from config.settings import settings
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException


class LLM:
    """智谱AI大模型引擎类（异步单例 + 动态配置）"""
    _instance: Optional["LLM"] = None
    _client: Optional[ZhipuAI] = None
    _model_name: str = ""
    _api_key: str = ""
    _timeout: int = 100

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def _load_config_from_db(self):
        """从数据库加载大模型配置（🔥 延迟导入，避免循环依赖）"""
        try:
            # 🔥 关键修复：在使用时才导入，避免循环依赖
            from db.sqlite_conn import SessionLocal
            from service.admin.system_config_service import system_config_service
            
            db = SessionLocal()
            
            # 加载配置
            api_key = system_config_service.get_config_value(db, "llm.api_key", "")
            model_name = system_config_service.get_config_value(db, "llm.model_name", "glm-4-flash")
            timeout_str = system_config_service.get_config_value(db, "llm.timeout", "100")
            
            self._api_key = api_key or settings.ZHIPU_API_KEY  # 降级到环境变量
            self._model_name = model_name or settings.ZHIPU_MODEL_NAME
            self._timeout = int(timeout_str) if timeout_str.isdigit() else 100
            
            logger.info(f"📦 从数据库加载大模型配置: model={self._model_name}, timeout={self._timeout}s")
            db.close()
        except Exception as e:
            logger.warning(f"⚠️ 从数据库加载配置失败，使用环境变量: {str(e)}")
            self._api_key = settings.ZHIPU_API_KEY
            self._model_name = settings.ZHIPU_MODEL_NAME
            self._timeout = 100

    def _init_client(self):
        """内部方法：懒初始化客户端"""
        if self._client is not None:
            return
        
        # 🔥 从数据库加载配置
        self._load_config_from_db()
        
        if not self._api_key:
            logger.error("❌ 大模型API Key未配置")
            return
        
        logger.info(f"正在初始化大模型引擎，模型: {self._model_name}...")
        self._client = ZhipuAI(api_key=self._api_key)
        logger.info("✅ 大模型引擎初始化完成")

    async def chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        timeout: Optional[int] = None  # 🔥 允许覆盖默认超时
    ) -> str:
        """异步单轮对话接口（带超时）"""
        self._init_client()

        if not self._api_key:
            logger.error("大模型调用失败：API Key 未配置")
            raise BusinessException(
                code=BusinessErrorCode.LLM_CALL_ERROR,
                msg="大模型 API Key 未配置，请在【系统配置】中配置"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # 使用传入的超时或配置中的超时
        actual_timeout = timeout or self._timeout

        try:
            logger.info(f"正在调用大模型，模型: {self._model_name}，提示词长度: {len(user_prompt)}")

            # 🔥 核心：用线程池包装同步调用，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._client.chat.completions.create(
                        model=self._model_name,
                        messages=messages
                    )
                ),
                timeout=actual_timeout
            )

            result = response.choices[0].message.content
            logger.info(f"✅ 大模型调用成功，响应长度: {len(result)}")
            return result

        except asyncio.TimeoutError:
            logger.error(f"❌ 大模型调用超时（{actual_timeout}秒）")
            raise BusinessException(
                code=BusinessErrorCode.LLM_CALL_ERROR,
                msg=f"大模型响应超时（{actual_timeout}秒），请稍后重试"
            )
        except Exception as e:
            logger.error(f"❌ 大模型调用失败: {str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.LLM_CALL_ERROR,
                msg=f"大模型调用失败: {str(e)}"
            )

    def reload_config(self):
        """重新加载配置（用于管理员修改配置后）"""
        self._client = None  # 重置客户端
        self._load_config_from_db()
        logger.info("🔄 大模型配置已重新加载")


# 全局单例
llm = LLM()