"""
审核员-公共内容查看接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from urllib.parse import quote

# ✅ 修正：使用绝对导入，和你项目其他文件保持一致
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
from middleware.auth_middleware import role_required

router = APIRouter(
    prefix="/content",
    tags=["审核员-公共内容查看"],
    dependencies=[Depends(role_required([1, 2]))]
)


@router.get(
    "/category/list",
    summary="审核员获取公共分类列表",
    response_model=SuccessResponse[List[CategoryInfoResponse]]
)
async def get_public_category_list_for_auditor(db: Session = Depends(get_db)):
    """审核员查看公共分类（复用用户逻辑）"""
    result = content_public_service.get_public_category_list(db)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/list",
    summary="审核员获取公共文档列表",
    response_model=SuccessResponse[List[DocumentInfoResponse]]
)
async def get_public_document_list_for_auditor(
    category_id: int = Query(None, description="分类ID"),
    db: Session = Depends(get_db)
):
    """审核员查看公共文档列表（复用用户逻辑）"""
    result = content_public_service.get_public_document_list(db, category_id)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/{doc_id}",
    summary="审核员获取公共文档详情",
    response_model=SuccessResponse[DocumentInfoResponse]
)
async def get_public_document_detail_for_auditor(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db)
):
    """审核员查看公共文档详情（复用用户逻辑）"""
    result = content_public_service.get_public_document_detail(db, doc_id)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/{doc_id}/points",
    summary="审核员获取公共文档知识点列表",
    response_model=SuccessResponse[List[KnowledgePointResponse]]
)
async def get_public_knowledge_points_for_auditor(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db)
):
    """审核员查看公共文档知识点（复用用户逻辑）"""
    result = content_public_service.get_public_knowledge_points(db, doc_id)
    return success_response(data=result, msg="获取成功")


@router.get(
    "/document/{doc_id}/download",
    summary="审核员下载公共文档"
)
async def download_public_document_for_auditor(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db)
):
    """审核员下载公共文档（复用用户逻辑）"""
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

    # 文件名编码
    encoded_filename = quote(document.file_name, encoding='utf-8')

    # 返回文件下载响应
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )