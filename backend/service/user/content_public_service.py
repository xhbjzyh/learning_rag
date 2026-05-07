"""
用户-公共内容消费业务逻辑
"""
from typing import List
from sqlalchemy.orm import Session

from models.db_models import KnowledgeDocument, KnowledgePoint, KnowledgeCategory
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
        return [DocumentInfoResponse.model_validate(item) for item in documents]

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
        return DocumentInfoResponse.model_validate(doc)

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