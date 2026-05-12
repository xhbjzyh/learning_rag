"""
数据库初始化脚本
功能：
1. 创建所有数据库表结构（基于models/db_models.py中定义的ORM模型）
2. 初始化默认角色数据（超级管理员、审核员、普通用户）
3. 初始化默认管理员账号（admin/admin123）
4. 初始化默认知识点标签（用于个性化推荐）

使用方法：
在项目根目录下执行：python scripts/init_db.py

注意事项：
1. 仅在首次部署或重置数据库时运行
2. 运行前请确保config/settings.py中的路径配置正确
3. 已存在的表不会被重复创建，已存在的默认数据不会被覆盖
"""
# ==================== 标准库导入 ====================
import sys
import os

# ==================== 内部模块导入 ====================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.sqlite_conn import engine, Base, SessionLocal
# 🔥 关键：显式导入【所有课程模型】，强制加载到Base.metadata
from models.db_models import (
    # 用户模块
    SysRole, SysUser, UserProfile, UserLearningHistory,
    UserLearningRecord, UserFeedback,
    # 知识库模块
    KnowledgeCategory, KnowledgeDocument, KnowledgeTag,
    KnowledgePointTagRel, KnowledgePoint,
    # 审核&内容模块
    AuditRecord, ContentPublicApply, WrongQuestion, LearningProgress,
    # 习题系统
    Exercise, ExerciseOption, UserExerciseRecord, UserKnowledgeMastery,
    # 问答记录
    UserQaRecord,
    # 推荐基础表
    RecommendationRecord,
    # ✅ 课程系统全部表（核心修复，必须显式列出）
    CourseCategory, Course, CourseResource,
    UserCourseProgress, UserResourceProgress,
    # ✅ 课程推荐系统表
    UserCourseBehavior, CourseTag, CourseTagRel, UserInterestTag,
    UserLearningPreference, UserSimilarity, CourseSimilarity,
    # ✅ 课程知识点相关表
    CourseKnowledgePoint, UserCourseKnowledgeProgress, UserCourseKnowledgeMastery
)
from utils.password_utils import hash_password
from utils.logger import logger


def init_tables():
    """
    创建数据库表结构
    基于Base.metadata中注册的所有ORM模型（models/db_models.py中的类）创建表
    特性：
    - 已存在的表不会被重复创建（安全）
    - 表结构与模型定义完全一致
    - 自动创建新增的个性化推荐相关表
    """
    logger.info("开始创建数据库表结构...")
    # SQLAlchemy核心方法：创建所有继承自Base的模型对应的表
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库表结构创建完成")


def init_default_data():
    """
    初始化默认数据
    包括：
    1. 默认角色（超级管理员、审核员、普通用户）
    2. 默认管理员账号（admin/admin123）
    3. 默认知识点标签（用于个性化推荐）

    设计原则：
    - 幂等性：已存在的数据不会被重复插入，避免报错
    - 安全性：管理员密码使用hash_password加密存储
    """
    # 创建数据库会话
    db = SessionLocal()
    try:
        logger.info("开始初始化默认角色...")

        # ==================== 1. 初始化默认角色 ====================
        # 检查是否已存在角色（通过id=1判断，避免重复初始化）
        exist_admin_role = db.query(SysRole).filter(SysRole.id == 1).first()
        if not exist_admin_role:
            # 创建三个默认角色
            roles = [
                SysRole(id=1, role_name="超级管理员", description="系统最高权限管理员，拥有所有操作权限"),
                SysRole(id=2, role_name="审核员", description="负责文档审核的管理员，可审核文档、查看审核记录"),
                SysRole(id=3, role_name="普通用户", description="普通学习用户，可上传文档、检索知识、收藏、查看推荐")
            ]
            # 批量插入角色
            db.add_all(roles)
            # 提交事务
            db.commit()
            logger.info("✅ 默认角色初始化完成")
        else:
            logger.info("默认角色已存在，跳过初始化")

        # ==================== 2. 初始化默认管理员账号 ====================
        logger.info("开始初始化默认管理员账号...")
        # 检查是否已存在管理员账号（通过id=1判断）
        exist_admin_user = db.query(SysUser).filter(SysUser.id == 1).first()
        if not exist_admin_user:
            # 创建默认管理员账号
            admin_user = SysUser(
                id=1,
                username="admin",
                password=hash_password("admin123"),  # 密码加密存储，严禁明文
                role_id=1,  # 关联超级管理员角色
                is_active=1  # 账号默认启用
            )
            # 插入管理员账号
            db.add(admin_user)
            # 提交事务
            db.commit()
            logger.info("✅ 默认管理员账号初始化完成")
            logger.info("👉 管理员账号：admin")
            logger.info("👉 管理员密码：admin123")
            logger.info("⚠️  生产环境请立即修改默认密码！")
        else:
            logger.info("默认管理员账号已存在，跳过初始化")

        # ==================== 3. 初始化默认知识点标签（新增，用于个性化推荐） ====================
        logger.info("开始初始化默认知识点标签...")
        # 预设的默认标签列表
        default_tags = [
            {"name": "Python", "description": "Python编程语言相关知识点"},
            {"name": "机器学习", "description": "机器学习算法与应用相关知识点"},
            {"name": "RAG", "description": "检索增强生成技术相关知识点"},
            {"name": "数据库", "description": "数据库原理与应用相关知识点"},
            {"name": "前端开发", "description": "前端开发技术相关知识点"},
            {"name": "后端开发", "description": "后端开发技术相关知识点"},
            {"name": "深度学习", "description": "深度学习算法与应用相关知识点"},
            {"name": "自然语言处理", "description": "NLP技术相关知识点"}
        ]

        # 批量插入标签，已存在的标签跳过
        for tag_data in default_tags:
            # 检查标签是否已存在（通过name判断，因为name是唯一的）
            exist_tag = db.query(KnowledgeTag).filter(KnowledgeTag.name == tag_data["name"]).first()
            if not exist_tag:
                # 创建标签对象
                tag = KnowledgeTag(
                    name=tag_data["name"],
                    description=tag_data["description"]
                )
                db.add(tag)
        # 提交事务
        db.commit()
        logger.info("✅ 默认知识点标签初始化完成")

        # ==================== 4. 初始化默认文档分类（新增，大方向分类） ====================
        logger.info("开始初始化默认文档分类...")
        default_categories = [
            {"category_name": "技术文档", "description": "编程、框架、工具等技术类文档"},
            {"category_name": "学术论文", "description": "科研论文、学术报告等"},
            {"category_name": "教程指南", "description": "学习教程、操作手册、最佳实践"},
            {"category_name": "项目资料", "description": "项目文档、需求说明、设计文档"},
            {"category_name": "读书笔记", "description": "书籍摘要、读后感、知识总结"},
            {"category_name": "其他", "description": "其他类型文档"}
        ]

        # 批量插入分类，已存在的分类跳过
        for cat_data in default_categories:
            # 检查分类是否已存在（通过category_name判断）
            exist_cat = db.query(KnowledgeCategory).filter(
                KnowledgeCategory.category_name == cat_data["category_name"]
            ).first()
            if not exist_cat:
                # 创建分类对象
                category = KnowledgeCategory(
                    category_name=cat_data["category_name"],
                    description=cat_data["description"]
                )
                db.add(category)
        # 提交事务
        db.commit()
        logger.info("✅ 默认文档分类初始化完成")

    except Exception as e:
        # 发生异常时回滚事务，保证数据一致性
        db.rollback()
        logger.error(f"❌ 初始化默认数据失败: {str(e)}")
        # 重新抛出异常，让调用者知道失败
        raise e
    finally:
        # 无论成功或失败，都关闭数据库会话，避免连接泄漏
        db.close()


if __name__ == "__main__":
    """
    脚本独立运行入口
    执行顺序：
    1. 创建表结构
    2. 初始化默认数据
    """
    logger.info("=" * 50)
    logger.info("开始数据库初始化...")
    logger.info("=" * 50)

    # 执行初始化
    init_tables()
    init_default_data()

    logger.info("=" * 50)
    logger.info("🎉 数据库初始化全部完成")
    logger.info("=" * 50)