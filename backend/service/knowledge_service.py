"""
知识库业务逻辑实现
处理文档上传、解析、分类管理、知识点提取等核心业务
"""
import os
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile
from utils.document_parser import document_parser, calculate_md5
from models.db_models import KnowledgeCategory, KnowledgeDocument, KnowledgePoint
from models.schemas import (
    CategoryCreateRequest,
    CategoryInfoResponse,
    DocumentUploadResponse,
    DocumentInfoResponse,
    KnowledgePointResponse,
    DocumentUpdateRequest,
    DocumentAuditRequest
)
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger
from config import settings


class KnowledgeService:
    """知识库服务类"""

    @staticmethod
    def create_category(db: Session, request: CategoryCreateRequest) -> CategoryInfoResponse:
        """
        创建知识库分类
        """
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
    def get_category_list(db: Session) -> List[CategoryInfoResponse]:
        """
        获取分类列表
        """
        categories = db.query(KnowledgeCategory).order_by(KnowledgeCategory.create_time.desc()).all()
        return [CategoryInfoResponse.model_validate(item) for item in categories]

    @staticmethod
    async def upload_document(
            db: Session,
            file: UploadFile,
            title: str,
            category_id: Optional[int],
            user_id: int
    ) -> DocumentUploadResponse:
        """
        上传文档（防重复版本）
        """
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
            KnowledgeDocument.file_md5 == file_md5
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
            audit_status=0  # 默认为待审核
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        logger.info(f"文档上传成功: {file.filename}, 文档ID: {new_doc.id}")
        return DocumentUploadResponse.model_validate(new_doc)

    @staticmethod
    def get_document_list(db: Session, user_id: Optional[int] = None) -> List[DocumentInfoResponse]:
        """
        获取文档列表
        """
        query = db.query(KnowledgeDocument)
        if user_id:
            query = query.filter(KnowledgeDocument.upload_user_id == user_id)
        documents = query.order_by(KnowledgeDocument.create_time.desc()).all()
        return [DocumentInfoResponse.model_validate(item) for item in documents]

    @staticmethod
    def get_document_detail(db: Session, doc_id: int) -> DocumentInfoResponse:
        """
        获取文档详情
        """
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在"
            )
        return DocumentInfoResponse.model_validate(doc)

    # 修改文档信息
    @staticmethod
    def update_document(
        db: Session,
        doc_id: int,
        request: DocumentUpdateRequest,
        user_id: int,
        role_id: int
    ) -> DocumentInfoResponse:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        # 权限校验：仅上传者/管理员可修改
        if doc.upload_user_id != user_id and role_id not in (1, 2):
            raise BusinessException(msg="无权限修改此文档")

        # 更新字段
        if request.title:
            doc.title = request.title
        if request.category_id is not None:
            doc.category_id = request.category_id

        db.commit()
        db.refresh(doc)
        logger.info(f"文档修改成功，文档ID: {doc_id}")
        return DocumentInfoResponse.model_validate(doc)

    # 新增：文档审核逻辑
    @staticmethod
    def audit_document(
        db: Session,
        doc_id: int,
        request: DocumentAuditRequest,
        role_id: int
    ) -> DocumentInfoResponse:
        # 权限校验：仅管理员和审核员可审核
        if role_id not in (1, 2):
            raise BusinessException(msg="无权限进行文档审核")

        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        # 更新审核状态
        doc.audit_status = request.audit_status
        if request.audit_remark:
            doc.audit_remark = request.audit_remark

        db.commit()
        db.refresh(doc)
        logger.info(f"文档审核完成，文档ID: {doc_id}, 状态: {request.audit_status}")
        return DocumentInfoResponse.model_validate(doc)

    # 级联删除文档
    @staticmethod
    def delete_document(db: Session, doc_id: int, user_id: int, role_id: int):
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        # 权限校验：仅上传者/管理员可删除
        if doc.upload_user_id != user_id and role_id not in (1, 2):
            raise BusinessException(msg="无权限删除此文档")

        # 1. 删除关联的知识点
        db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).delete()

        # 2. 删除本地文件
        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"删除本地文件失败: {str(e)}")

        # 3. 删除文档记录
        db.delete(doc)
        db.commit()
        logger.info(f"文档级联删除成功，文档ID: {doc_id}")

    @staticmethod
    def parse_and_extract_points(db: Session, doc_id: int) -> dict:
        """
        解析文档并提取知识点（防重复版本）
        【新增校验】仅审核通过的文档可以解析
        """
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在"
            )

        # 核心校验：只有审核通过(1)的文档才能解析
        if doc.audit_status != 1:
            raise BusinessException(
                code=BusinessErrorCode.PARAM_VALID_ERROR,
                msg="仅审核通过的文档可解析提取知识点"
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
    def get_knowledge_points(db: Session, doc_id: int) -> List[KnowledgePointResponse]:
        """
        获取文档的知识点列表
        """
        points = db.query(KnowledgePoint).filter(
            KnowledgePoint.doc_id == doc_id
        ).order_by(KnowledgePoint.create_time.asc()).all()
        return [KnowledgePointResponse.model_validate(item) for item in points]


knowledge_service = KnowledgeService()