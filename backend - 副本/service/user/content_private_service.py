"""
用户-私有内容管理业务逻辑
"""
import os
import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from utils.document_parser import document_parser, calculate_md5
from models.db_models import KnowledgeDocument, KnowledgePoint, LearningProgress, WrongQuestion
from models.schemas import (
    DocumentUploadResponse,
    DocumentInfoResponse,
    DocumentUpdateRequest,
    KnowledgePointResponse
)
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger
from config import settings


class ContentPrivateService:
    """私有内容管理服务类"""

    @staticmethod
    async def upload_document(
            db: Session,
            file: UploadFile,
            title: str,
            category_id: Optional[int],
            user_id: int
    ) -> DocumentUploadResponse:
        allowed_types = ["txt", "pdf", "docx"]
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in allowed_types:
            raise BusinessException(
                code=BusinessErrorCode.FILE_TYPE_NOT_SUPPORT,
                msg=f"不支持的文件类型，仅支持: {', '.join(allowed_types)}"
            )

        file_content = await file.read()
        file_md5 = calculate_md5(file_content)

        exist_doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.file_md5 == file_md5,
            KnowledgeDocument.upload_user_id == user_id
        ).first()

        if exist_doc:
            logger.info(f"文件已存在，直接返回已有记录，文档ID: {exist_doc.id}")
            return DocumentUploadResponse.model_validate(exist_doc)

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        file_uuid = str(uuid.uuid4())
        save_filename = f"{file_uuid}.{file_ext}"
        save_path = os.path.join(upload_dir, save_filename)

        with open(save_path, "wb") as f:
            f.write(file_content)

        file_size = len(file_content)

        new_doc = KnowledgeDocument(
            title=title,
            file_name=file.filename,
            file_path=save_path,
            file_md5=file_md5,
            file_type=file_ext,
            file_size=file_size,
            category_id=category_id,
            upload_user_id=user_id,
            audit_status=0
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        logger.info(f"文档上传成功: {file.filename}, 文档ID: {new_doc.id}")
        return DocumentUploadResponse.model_validate(new_doc)

    @staticmethod
    def get_private_document_list(db: Session, user_id: int):
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.upload_user_id == user_id
        ).order_by(KnowledgeDocument.create_time.desc()).all()
        return [DocumentInfoResponse.model_validate(item) for item in documents]

    @staticmethod
    def update_document(db: Session, doc_id: int, request: DocumentUpdateRequest, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        if request.title:
            doc.title = request.title
        if request.category_id is not None:
            doc.category_id = request.category_id

        db.commit()
        db.refresh(doc)
        logger.info(f"文档修改成功，文档ID: {doc_id}")
        return DocumentInfoResponse.model_validate(doc)

    @staticmethod
    def delete_document(db: Session, doc_id: int, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")
        db.query(LearningProgress).filter(
            LearningProgress.point_id.in_(
                db.query(KnowledgePoint.id).filter(KnowledgePoint.doc_id == doc_id)
            )
        ).delete(synchronize_session=False)

        # 新增：级联删除错题记录
        db.query(WrongQuestion).filter(
            WrongQuestion.point_id.in_(
                db.query(KnowledgePoint.id).filter(KnowledgePoint.doc_id == doc_id)
            )
        ).delete(synchronize_session=False)
        db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).delete()

        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"删除本地文件失败: {str(e)}")

        db.delete(doc)
        db.commit()
        logger.info(f"文档删除成功，文档ID: {doc_id}")

    @staticmethod
    def parse_and_extract_points(db: Session, doc_id: int, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在"
            )

        exist_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.doc_id == doc_id
        ).first()

        if exist_points:
            points_count = db.query(KnowledgePoint).filter(
                KnowledgePoint.doc_id == doc_id
            ).count()
            logger.info(f"文档已解析过，直接返回已有数据，知识点数量: {points_count}")
            return {"doc_id": doc_id, "points_count": points_count, "is_new": False}

        try:
            text_content = document_parser.parse_document(doc.file_path, doc.file_type)
        except Exception as e:
            logger.error(f"文档解析失败: {doc_id}, 错误: {str(e)}")
            raise BusinessException(
                code=BusinessErrorCode.DOC_PARSE_ERROR,
                msg="文档解析失败"
            )

        chunks = document_parser.split_into_chunks(text_content, chunk_size=500, overlap=50)

        points_created = 0
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            point_title = f"{doc.title} - 第{i + 1}部分"

            new_point = KnowledgePoint(
                doc_id=doc_id,
                title=point_title,
                content=chunk,
                difficulty="中等"
            )
            db.add(new_point)
            points_created += 1

        db.commit()
        logger.info(f"知识点提取完成，文档ID: {doc_id}, 共提取 {points_created} 个知识点")
        return {"doc_id": doc_id, "points_count": points_created, "is_new": True}

    @staticmethod
    def get_private_knowledge_points(db: Session, doc_id: int, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        points = db.query(KnowledgePoint).filter(
            KnowledgePoint.doc_id == doc_id
        ).order_by(KnowledgePoint.create_time.asc()).all()
        return [KnowledgePointResponse.model_validate(item) for item in points]


content_private_service = ContentPrivateService()