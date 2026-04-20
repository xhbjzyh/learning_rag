"""
智谱AI大模型调用引擎（懒加载版）
"""
# ==================== 标准库导入 ====================
from typing import Optional

# ==================== 第三方库导入 ====================
from zhipuai import ZhipuAI

# ==================== 内部模块导入 ====================
from config.settings import settings
from utils.logger import logger
from utils.response import BusinessErrorCode, BusinessException


class LLM:
    """智谱AI大模型引擎类（懒加载单例）"""
    _instance: Optional["LLM"] = None
    _client: Optional[ZhipuAI] = None
    _model_name: str = ""

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def _init_client(self):
        """内部方法：懒初始化客户端"""
        if self._client is not None:
            return
        logger.info(f"正在懒初始化大模型引擎，模型: {settings.ZHIPU_MODEL_NAME}...")
        self._client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
        self._model_name = settings.ZHIPU_MODEL_NAME
        logger.info("✅ 大模型引擎懒初始化完成")

    def chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """单轮对话接口"""
        self._init_client()

        if not settings.ZHIPU_API_KEY:
            logger.error("大模型调用失败：智谱AI API Key 未配置")
            raise BusinessException(
                code=BusinessErrorCode.LLM_CALL_ERROR,
                msg="大模型 API Key 未配置，请联系管理员"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        try:
            logger.info(f"正在调用大模型，模型: {self._model_name}，提示词长度: {len(user_prompt)}")
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages
            )
            result = response.choices[0].message.content
            logger.info(f"✅ 大模型调用成功，响应长度: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"❌ 大模型调用失败: {str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.LLM_CALL_ERROR,
                msg=f"大模型调用失败: {str(e)}"
            )


# 全局单例
llm = LLM()