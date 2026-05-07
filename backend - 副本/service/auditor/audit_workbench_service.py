"""
审核员-审核工作台业务逻辑
处理内容公开申请的审核、驳回、统计等功能
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.sql import func

from models.db_models import KnowledgeDocument, ContentPublicApply, SysUser, KnowledgePoint
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class AuditWorkbenchService:
    """审核工作台服务类"""

    @staticmethod
    def get_pending_audit_list(db: Session) -> List[dict]:
        """
        获取待审核内容列表
        返回：包含申请信息、文档信息、申请人信息的完整列表
        """
        applies = db.query(ContentPublicApply).filter(
            ContentPublicApply.apply_status == 0
        ).order_by(ContentPublicApply.create_time.desc()).all()

        result = []
        for apply in applies:
            # 获取文档信息
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == apply.doc_id
            ).first()

            # 获取申请人信息
            apply_user = db.query(SysUser).filter(
                SysUser.id == apply.apply_user_id
            ).first()

            if doc and apply_user:
                result.append({
                    "apply_id": apply.id,
                    "doc_id": doc.id,
                    "doc_title": doc.title,
                    "doc_type": doc.file_type,
                    "doc_size": doc.file_size,
                    "apply_user_id": apply.apply_user_id,
                    "apply_username": apply_user.username,
                    "apply_remark": apply.apply_remark,
                    "create_time": apply.create_time.strftime("%Y-%m-%d %H:%M:%S") if apply.create_time else ""
                })
        return result

    @staticmethod
    def get_audit_history(db: Session, auditor_id: int = None) -> List[dict]:
        """
        获取审核历史记录
        :param auditor_id: 审核人ID，为None时返回所有审核记录
        """
        query = db.query(ContentPublicApply).filter(
            ContentPublicApply.apply_status != 0
        ).order_by(ContentPublicApply.audit_time.desc())

        if auditor_id:
            query = query.filter(ContentPublicApply.audit_user_id == auditor_id)

        applies = query.all()

        result = []
        for apply in applies:
            doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == apply.doc_id).first()
            apply_user = db.query(SysUser).filter(SysUser.id == apply.apply_user_id).first()
            audit_user = db.query(SysUser).filter(SysUser.id == apply.audit_user_id).first()

            status_text = "已通过" if apply.apply_status == 1 else "已驳回"

            result.append({
                "apply_id": apply.id,
                "doc_title": doc.title if doc else "文档已删除",
                "apply_username": apply_user.username if apply_user else "用户已删除",
                "audit_username": audit_user.username if audit_user else "审核人已删除",
                "apply_status": apply.apply_status,
                "status_text": status_text,
                "apply_remark": apply.apply_remark,
                "audit_remark": apply.audit_remark,
                "apply_time": apply.create_time.strftime("%Y-%m-%d %H:%M:%S") if apply.create_time else "",
                "audit_time": apply.audit_time.strftime("%Y-%m-%d %H:%M:%S") if apply.audit_time else ""
            })
        return result

    @staticmethod
    def audit_document(
        db: Session,
        apply_id: int,
        audit_status: int,
        audit_remark: Optional[str],
        auditor_id: int
    ):
        """
        审核文档公开申请
        :param audit_status: 1=通过，2=驳回
        """
        # 1. 校验申请记录
        apply = db.query(ContentPublicApply).filter(
            ContentPublicApply.id == apply_id
        ).first()
        if not apply:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="申请记录不存在"
            )

        if apply.apply_status != 0:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="该申请已审核，不可重复操作"
            )

        # 2. 更新申请状态
        apply.apply_status = audit_status
        apply.audit_user_id = auditor_id
        apply.audit_remark = audit_remark
        apply.audit_time = func.now()

        # 3. 审核通过：更新文档为公开状态
        # 如果审核通过，更新文档为公开状态
        if audit_status == 1:
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == apply.doc_id
            ).first()
            if doc:
                doc.is_public = 1
                doc.audit_status = 1

                # 新增：自动同步到向量库
                from core.rag_engine import rag_engine
                points = db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc.id).all()
                for point in points:
                    rag_engine.add_document(doc_id=point.id, title=point.title, content=point.content)
                logger.info(f"文档{doc.id}审核通过，已自动同步到向量库")

        db.commit()
        logger.info(f"审核员{auditor_id}完成申请{apply_id}的审核，结果：{audit_status}")
        return {"msg": "审核完成"}

    @staticmethod
    def get_audit_stats(db: Session) -> dict:
        """
        获取审核统计数据
        """
        total_pending = db.query(ContentPublicApply).filter(ContentPublicApply.apply_status == 0).count()
        total_passed = db.query(ContentPublicApply).filter(ContentPublicApply.apply_status == 1).count()
        total_rejected = db.query(ContentPublicApply).filter(ContentPublicApply.apply_status == 2).count()

        return {
            "total_pending": total_pending,
            "total_passed": total_passed,
            "total_rejected": total_rejected,
            "total_apply": total_pending + total_passed + total_rejected
        }


audit_workbench_service = AuditWorkbenchService()