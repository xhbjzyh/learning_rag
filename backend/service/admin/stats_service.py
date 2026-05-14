"""
管理员仪表盘统计服务
"""
from sqlalchemy.orm import Session
from models.db_models import SysUser, KnowledgeDocument, ContentPublicApply, SysRole
from utils.logger import logger


class AdminStatsService:
    """管理员统计服务"""

    def get_dashboard_stats(self, db: Session):
        """获取仪表盘统计数据"""
        try:
            # 1. 注册用户总数（排除管理员和审核员）
            user_role = db.query(SysRole).filter(SysRole.role_name == "user").first()
            user_count = 0
            if user_role:
                user_count = db.query(SysUser).filter(
                    SysUser.role_id == user_role.id,
                    SysUser.is_active == 1
                ).count()

            # 2. 待审核申请数量
            pending_audit_count = db.query(ContentPublicApply).filter(
                ContentPublicApply.apply_status == 0  # 0=待审核
            ).count()

            # 3. 平台文档总数（已公开的文档）
            doc_count = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.is_public == 1
            ).count()

            # 4. 审核员数量
            auditor_role = db.query(SysRole).filter(SysRole.role_name == "auditor").first()
            auditor_count = 0
            if auditor_role:
                auditor_count = db.query(SysUser).filter(
                    SysUser.role_id == auditor_role.id,
                    SysUser.is_active == 1
                ).count()

            # 5. 最近待审核申请（最近5条）
            recent_pending = db.query(ContentPublicApply).filter(
                ContentPublicApply.apply_status == 0
            ).order_by(
                ContentPublicApply.create_time.desc()
            ).limit(5).all()

            pending_list = []
            for apply in recent_pending:
                # 获取申请人信息
                applicant = db.query(SysUser).filter(SysUser.id == apply.apply_user_id).first()
                # 获取文档标题
                doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == apply.doc_id).first()
                pending_list.append({
                    "id": apply.id,
                    "doc_title": doc.title if doc else "未知文档",
                    "username": applicant.username if applicant else "未知用户",
                    "create_time": apply.create_time.strftime("%Y-%m-%d %H:%M:%S") if apply.create_time else ""
                })

            return {
                "user_count": user_count,
                "pending_audit_count": pending_audit_count,
                "doc_count": doc_count,
                "auditor_count": auditor_count,
                "recent_pending": pending_list
            }

        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}")
            raise


admin_stats_service = AdminStatsService()
