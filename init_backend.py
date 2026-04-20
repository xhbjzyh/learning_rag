# init_backend.py
import os

# 定义后端根目录
BACKEND_ROOT = "backend"

# 定义完整的目录结构
directories = [
    f"{BACKEND_ROOT}/api",
    f"{BACKEND_ROOT}/service",
    f"{BACKEND_ROOT}/models",
    f"{BACKEND_ROOT}/db",
    f"{BACKEND_ROOT}/core",
    f"{BACKEND_ROOT}/middleware",
    f"{BACKEND_ROOT}/utils",
    f"{BACKEND_ROOT}/config",
    f"{BACKEND_ROOT}/tests",
    f"{BACKEND_ROOT}/scripts",
    f"{BACKEND_ROOT}/static/files",
    f"{BACKEND_ROOT}/data/sqlite",
    f"{BACKEND_ROOT}/data/faiss",
]

# 定义需要创建的空文件（__init__.py 和核心文件）
files = [
    f"{BACKEND_ROOT}/main.py",
    f"{BACKEND_ROOT}/requirements.txt",
    f"{BACKEND_ROOT}/pyproject.toml",
    f"{BACKEND_ROOT}/.env.example",
    f"{BACKEND_ROOT}/.gitignore",
    # API层
    f"{BACKEND_ROOT}/api/__init__.py",
    f"{BACKEND_ROOT}/api/user.py",
    f"{BACKEND_ROOT}/api/knowledge.py",
    f"{BACKEND_ROOT}/api/recommend.py",
    f"{BACKEND_ROOT}/api/audit.py",
    f"{BACKEND_ROOT}/api/admin.py",
    # Service层
    f"{BACKEND_ROOT}/service/__init__.py",
    f"{BACKEND_ROOT}/service/user_service.py",
    f"{BACKEND_ROOT}/service/knowledge_service.py",
    f"{BACKEND_ROOT}/service/rag_service.py",
    f"{BACKEND_ROOT}/service/recommend_service.py",
    f"{BACKEND_ROOT}/service/audit_service.py",
    # Models层
    f"{BACKEND_ROOT}/models/__init__.py",
    f"{BACKEND_ROOT}/models/db_models.py",
    f"{BACKEND_ROOT}/models/schemas.py",
    # DB层
    f"{BACKEND_ROOT}/db/__init__.py",
    f"{BACKEND_ROOT}/db/sqlite_conn.py",
    f"{BACKEND_ROOT}/db/vector_db.py",
    f"{BACKEND_ROOT}/db/file_storage.py",
    # Core层
    f"{BACKEND_ROOT}/core/__init__.py",
    f"{BACKEND_ROOT}/core/rag_engine.py",
    f"{BACKEND_ROOT}/core/embedder.py",
    f"{BACKEND_ROOT}/core/llm.py",
    f"{BACKEND_ROOT}/core/recommender.py",
    # Middleware层
    f"{BACKEND_ROOT}/middleware/__init__.py",
    f"{BACKEND_ROOT}/middleware/auth_middleware.py",
    f"{BACKEND_ROOT}/middleware/log_middleware.py",
    # Utils层
    f"{BACKEND_ROOT}/utils/__init__.py",
    f"{BACKEND_ROOT}/utils/jwt_utils.py",
    f"{BACKEND_ROOT}/utils/password_utils.py",
    f"{BACKEND_ROOT}/utils/logger.py",
    f"{BACKEND_ROOT}/utils/document_parser.py",
    # Config层
    f"{BACKEND_ROOT}/config/__init__.py",
    f"{BACKEND_ROOT}/config/settings.py",
    # Tests层
    f"{BACKEND_ROOT}/tests/__init__.py",
    f"{BACKEND_ROOT}/tests/test_user.py",
    f"{BACKEND_ROOT}/tests/test_rag.py",
    # Scripts层
    f"{BACKEND_ROOT}/scripts/__init__.py",
    f"{BACKEND_ROOT}/scripts/init_db.py",
]


def create_structure():
    print("开始创建后端目录结构...")

    # 1. 创建目录
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"[创建目录] {directory}")

    # 2. 创建空文件
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                # 给 __init__.py 文件添加简单的注释
                if file_path.endswith("__init__.py"):
                    f.write('"""\n模块初始化文件\n"""\n')
            print(f"[创建文件] {file_path}")

    print("\n✅ 后端目录结构创建完成！")


if __name__ == "__main__":
    create_structure()