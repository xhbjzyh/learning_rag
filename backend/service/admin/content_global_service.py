"""
管理员-内容全局管理业务逻辑
"""
import os
from sqlalchemy.orm import Session

from models.db_models import KnowledgeDocument, KnowledgePoint, KnowledgeCategory
from models.schemas import CategoryCreateRequest, CategoryInfoResponse
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class ContentGlobalService:
    """内容全局管理服务类"""

    @staticmethod
    def create_category(db: Session, request: CategoryCreateRequest) -> CategoryInfoResponse:
        exist_category = db.query(KnowledgeCategory).filter(
            KnowledgeCategory.category_name == request.category_name
        ).first()
        if exist_category:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="分类名称已存在"
            )

        new_category = KnowledgeCategory(
            category_name=request.category_name,
            description=request.description
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        logger.info(f"知识库分类创建成功: {request.category_name}")
        return CategoryInfoResponse.model_validate(new_category)

    @staticmethod
    def get_category_list(db: Session):
        categories = db.query(KnowledgeCategory).order_by(KnowledgeCategory.create_time.desc()).all()
        return [CategoryInfoResponse.model_validate(item) for item in categories]

    @staticmethod
    def delete_document_global(db: Session, doc_id: int):
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).delete()

        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"删除本地文件失败: {str(e)}")

        db.delete(doc)
        db.commit()
        logger.info(f"文档全局删除成功，文档ID: {doc_id}")


content_global_service = ContentGlobalService()