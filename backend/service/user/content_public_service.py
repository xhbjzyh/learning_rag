"""
用户-公共内容消费业务逻辑
"""
from typing import List
from sqlalchemy.orm import Session

from models.db_models import KnowledgeDocument, KnowledgePoint, KnowledgeCategory, SysUser
from models.schemas import (
    DocumentInfoResponse,
    KnowledgePointResponse,
    CategoryInfoResponse
)
from utils.response import BusinessErrorCode, BusinessException


class ContentPublicService:
    """公共内容消费服务类"""

    @staticmethod
    def get_public_category_list(db: Session) -> List[CategoryInfoResponse]:
        categories = db.query(KnowledgeCategory).order_by(KnowledgeCategory.create_time.desc()).all()
        return [CategoryInfoResponse.model_validate(item) for item in categories]

    @staticmethod
    def get_public_document_list(db: Session, category_id: int = None):
        query = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.audit_status == 1
        )
        if category_id:
            query = query.filter(KnowledgeDocument.category_id == category_id)
        documents = query.order_by(KnowledgeDocument.create_time.desc()).all()
        
        # 🔥 批量获取上传用户名
        user_ids = [doc.upload_user_id for doc in documents if doc.upload_user_id]
        users = db.query(SysUser).filter(SysUser.id.in_(user_ids)).all() if user_ids else []
        user_map = {user.id: user.username for user in users}
        
        result = []
        for doc in documents:
            doc_dict = DocumentInfoResponse.model_validate(doc).model_dump()
            doc_dict['upload_username'] = user_map.get(doc.upload_user_id)
            result.append(DocumentInfoResponse(**doc_dict))
        
        return result

    @staticmethod
    def get_public_document_detail(db: Session, doc_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.audit_status == 1
        ).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在或未通过审核"
            )
        
        # 🔥 获取上传用户名
        uploader = db.query(SysUser).filter(SysUser.id == doc.upload_user_id).first()
        doc_dict = DocumentInfoResponse.model_validate(doc).model_dump()
        doc_dict['upload_username'] = uploader.username if uploader else None
        
        return DocumentInfoResponse(**doc_dict)

    @staticmethod
    def get_public_knowledge_points(db: Session, doc_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.audit_status == 1
        ).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在或未通过审核"
            )

        points = db.query(KnowledgePoint).filter(
            KnowledgePoint.doc_id == doc_id
        ).order_by(KnowledgePoint.create_time.asc()).all()
        return [KnowledgePointResponse.model_validate(item) for item in points]


content_public_service = ContentPublicService()