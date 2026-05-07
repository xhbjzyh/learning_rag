"""
用户-内容公开申请业务逻辑
处理用户提交公开申请、查看申请历史等功能
"""
from sqlalchemy.orm import Session
from typing import Optional

from models.db_models import KnowledgeDocument, ContentPublicApply
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger
# 顶部新增导入
from utils.vector_store import get_global_vector_store
from service.user.rag_service import rag_service

class ContentApplyService:
    """内容公开申请服务类"""

    @staticmethod
    def apply_public(
        db: Session,
        doc_id: int,
        user_id: int,
        apply_remark: Optional[str] = None
    ):
        """
        申请公开文档
        """
        # 1. 校验文档权限
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在或您无权限操作"
            )

        # 2. 校验文档状态
        if doc.is_public == 1:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="该文档已经是公开状态"
            )

        # 3. 校验是否已有待审核申请
        exist_apply = db.query(ContentPublicApply).filter(
            ContentPublicApply.doc_id == doc_id,
            ContentPublicApply.apply_status == 0
        ).first()
        if exist_apply:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="该文档已有待审核的公开申请，请耐心等待"
            )

        # 4. 创建申请记录
        new_apply = ContentPublicApply(
            doc_id=doc_id,
            apply_user_id=user_id,
            apply_remark=apply_remark,
            apply_status=0
        )
        db.add(new_apply)
        db.commit()
        db.refresh(new_apply)

        logger.info(f"用户{user_id}提交文档{doc_id}的公开申请，申请ID: {new_apply.id}")
        return {
            "apply_id": new_apply.id,
            "msg": "申请提交成功，我们会尽快审核"
        }

    @staticmethod
    def get_my_apply_list(db: Session, user_id: int) -> list[dict]:
        """
        获取我的公开申请列表
        """
        applies = db.query(ContentPublicApply).filter(
            ContentPublicApply.apply_user_id == user_id
        ).order_by(ContentPublicApply.create_time.desc()).all()

        result = []
        for apply in applies:
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == apply.doc_id
            ).first()

            status_map = {0: "待审核", 1: "已通过", 2: "已驳回"}

            result.append({
                "apply_id": apply.id,
                "doc_id": apply.doc_id,
                "doc_title": doc.title if doc else "文档已删除",
                "apply_status": apply.apply_status,
                "status_text": status_map.get(apply.apply_status, "未知"),
                "apply_remark": apply.apply_remark,
                "audit_remark": apply.audit_remark,
                "create_time": apply.create_time.strftime("%Y-%m-%d %H:%M:%S") if apply.create_time else "",
                "audit_time": apply.audit_time.strftime("%Y-%m-%d %H:%M:%S") if apply.audit_time else ""
            })
        return result

    @staticmethod
    def cancel_apply(db: Session, apply_id: int, user_id: int):
        """
        取消待审核的公开申请
        """
        apply = db.query(ContentPublicApply).filter(
            ContentPublicApply.id == apply_id,
            ContentPublicApply.apply_user_id == user_id
        ).first()
        if not apply:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="申请记录不存在或您无权限操作"
            )

        if apply.apply_status != 0:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="只能取消待审核状态的申请"
            )

        db.delete(apply)
        db.commit()
        logger.info(f"用户{user_id}取消了申请{apply_id}")
        return {"msg": "申请已取消"}


content_apply_service = ContentApplyService()


# 在类中新增方法
@staticmethod
def audit_apply(db: Session, apply_id: int, audit_status: int, audit_remark: str = None):
    """审核公开申请（管理员接口）"""
    apply = db.query(ContentPublicApply).filter(ContentPublicApply.id == apply_id).first()
    if not apply:
        raise BusinessException(msg="申请不存在")

    apply.apply_status = audit_status
    apply.audit_remark = audit_remark
    db.commit()

    # 🔥 核心：审核通过 → 同步文档向量到公共库(user_0)
    if audit_status == 1:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == apply.doc_id).first()
        if doc:
            doc.is_public = 1
            db.commit()
            # 同步知识点到公共向量库
            rag_service.sync_point_to_vector(db, doc.id)
            logger.info(f"文档{doc.id}已公开，同步到公共知识库")

    return {"msg": "审核成功"}