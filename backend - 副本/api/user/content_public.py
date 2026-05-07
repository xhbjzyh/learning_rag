"""
用户-公共内容消费接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from db.sqlite_conn import get_db
from models.db_models import KnowledgeDocument, SysUser
from service.user.content_public_service import content_public_service
from models.schemas import (
    DocumentInfoResponse,
    KnowledgePointResponse,
    CategoryInfoResponse,
    SuccessResponse
)
from utils.response import success_response
# ✅ 修复：正确的导入路径（auth.py在api/common下）
from api.common.auth import get_current_user

router = APIRouter(
    prefix="/content/public",
    tags=["用户-公共内容消费"]
)


@router.get(
    "/category/list",
    summary="获取公共分类列表",
    response_model=SuccessResponse[List[CategoryInfoResponse]]
)
async def get_public_category_list(db: Session = Depends(get_db)):
    result = content_public_service.get_public_category_list(db)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/list",
    summary="获取公共文档列表",
    response_model=SuccessResponse[List[DocumentInfoResponse]]
)
async def get_public_document_list(
    category_id: int = Query(None, description="分类ID"),
    db: Session = Depends(get_db)
):
    result = content_public_service.get_public_document_list(db, category_id)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/{doc_id}",
    summary="获取公共文档详情",
    response_model=SuccessResponse[DocumentInfoResponse]
)
async def get_public_document_detail(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db)
):
    result = content_public_service.get_public_document_detail(db, doc_id)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/{doc_id}/points",
    summary="获取公共文档知识点列表",
    response_model=SuccessResponse[List[KnowledgePointResponse]]
)
async def get_public_knowledge_points(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db)
):
    result = content_public_service.get_public_knowledge_points(db, doc_id)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/{doc_id}/download",
    summary="下载公共文档"
)
async def download_public_document(
        doc_id: int = Path(..., description="文档ID"),
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    # 查询文档信息
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.audit_status == 1,
        KnowledgeDocument.is_public == 1
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在或未公开")

    # 检查文件是否存在
    file_path = document.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除或损坏")

    # ✅ 修复文件名乱码：使用标准RFC 5987编码
    from urllib.parse import quote
    encoded_filename = quote(document.file_name, encoding='utf-8')

    # 返回文件下载响应
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )