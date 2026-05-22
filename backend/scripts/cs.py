
"""
初始化RAG Prompt模板配置
一次性脚本，用于在数据库中创建Prompt模板配置项
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from db.sqlite_conn import SessionLocal
from models.db_models import SystemConfig
from utils.logger import logger


def init_prompt_templates():
    """初始化RAG Prompt模板配置"""
    print("=" * 80)
    print("🔧 初始化RAG Prompt模板配置")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # 定义Prompt模板配置
        templates = [
            {
                "config_key": "rag.prompt.system_with_history",
                "config_value": (
                    "你是专业学习助手，基于知识点和对话历史回答问题，不编造。\n"
                    "参考知识点：\n{context_text}\n\n"
                    "规则：\n"
                    "1. 参考之前的对话历史，保持对话连贯性\n"
                    "2. 如果有知识点，基于知识点回答；如果没有，直接回答\n"
                    "3. 分点作答、专业清晰"
                ),
                "config_type": "string",
                "description": "RAG系统提示词模板（有历史对话）- 支持{context_text}占位符"
            },
            {
                "config_key": "rag.prompt.system_without_history",
                "config_value": (
                    "你是专业学习助手，基于知识点回答问题，不编造。\n"
                    "参考知识点：\n{context_text}\n"
                    "规则：分点作答、专业清晰"
                ),
                "config_type": "string",
                "description": "RAG系统提示词模板（无历史对话）- 支持{context_text}占位符"
            },
            {
                "config_key": "rag.prompt.fallback",
                "config_value": "你是专业学习助手，直接回答用户问题",
                "config_type": "string",
                "description": "RAG知识库为空时的兜底提示词"
            }
        ]

        created_count = 0
        updated_count = 0

        for template in templates:
            # 检查是否已存在
            existing = db.query(SystemConfig).filter(
                SystemConfig.config_key == template["config_key"]
            ).first()

            if existing:
                # 更新现有配置
                existing.config_value = template["config_value"]
                existing.description = template["description"]
                updated_count += 1
                print(f"✅ 更新配置: {template['config_key']}")
            else:
                # 创建新配置
                new_config = SystemConfig(**template)
                db.add(new_config)
                created_count += 1
                print(f"✅ 创建配置: {template['config_key']}")

        db.commit()

        print("\n" + "=" * 80)
        print(f"✅ 初始化完成！")
        print(f"   - 新建配置: {created_count}个")
        print(f"   - 更新配置: {updated_count}个")
        print(f"   - 总计: {created_count + updated_count}个")
        print("=" * 80)
        
        # 🔥 验证配置是否正确加载
        print("\n🔍 验证配置加载...")
        print("-" * 80)
        
        from service.admin.system_config_service import system_config_service
        
        for template in templates:
            config_value = system_config_service.get_config_value(db, template["config_key"])
            if config_value:
                print(f"✅ {template['config_key']}: {len(config_value)}字符")
            else:
                print(f"❌ {template['config_key']}: 未找到")
        
        # 🔥 测试RAG引擎配置加载
        print("\n🔍 测试RAG引擎配置加载...")
        print("-" * 80)
        
        from core.rag_engine import rag_engine
        rag_engine._load_config_from_db()
        
        cache = rag_engine._config_cache
        print(f"✅ RAG引擎缓存中的Prompt模板:")
        print(f"   有历史: {len(cache.get('prompt_system_with_history', ''))}字符")
        print(f"   无历史: {len(cache.get('prompt_system_without_history', ''))}字符")
        print(f"   兜底: {len(cache.get('prompt_fallback', ''))}字符")

    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_prompt_templates()
