# 管理员模块所有子路由统一导出
# 用户管理
from .user_manage import router as user_manage_router
# 审核员管理
from .auditor_manage import router as auditor_manage_router
# 全局内容管理
from .content_global import router as content_global_router
# 审核管理
from .audit_manage import router as audit_manage_router
# 系统配置
from .system_config import router as system_config_router
# 系统审计
from .system_audit import router as system_audit_router

# 课程管理（已包含习题接口）
from .course import router as admin_course_router
