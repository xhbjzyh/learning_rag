"""
初始化系统配置
运行此脚本会在数据库中创建默认的大模型配置
"""
import sys
from pathlib import Path

# 🔥 关键修复：添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.sqlite_conn import SessionLocal
from service.admin.system_config_service import system_config_service

def init_system_config():
    """初始化系统配置"""
    db = SessionLocal()
    try:
        print("正在初始化系统配置...")
        system_config_service.init_default_llm_config(db)
        print("✅ 系统配置初始化成功！")
        
        # 验证配置是否创建成功
        configs = [
            'llm.provider',
            'llm.api_key', 
            'llm.model_name',
            'llm.timeout'
        ]
        
        print("\n已创建的配置：")
        for key in configs:
            config = system_config_service.get_config(db, key)
            if config:
                value = config.config_value if key != 'llm.api_key' else '***'
                print(f"  - {key}: {value}")
            else:
                print(f"  - {key}: ❌ 未找到")
                
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_system_config()
