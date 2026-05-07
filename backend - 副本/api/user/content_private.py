"""
用户-私有内容管理接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from service.user.content_private_service import content_private_service
from middleware.auth_middleware import get_current_user
from models.schemas import (
    DocumentUploadResponse,
    DocumentInfoResponse,
    KnowledgePointResponse,
    SuccessResponse,
    DocumentUpdateRequest
)
from models.db_models import SysUser
from utils.response import success_response

router = APIRouter(
    prefix="/content/private",
    tags=["用户-私有内容管理"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/document/upload", summary="上传私有文档", response_model=SuccessResponse[DocumentUploadResponse])
async def upload_private_document(
    file: UploadFile = File(..., description="上传的文件"),
    title: str = Form(..., description="文档标题"),
    category_id: Optional[int] = Form(None, description="所属分类ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    result = await content_private_service.upload_document(db, file, title, category_id, current_user.id)
    return success_response(data=result, msg="文档上传成功")


@router.get("/document/list", summary="获取私有文档列表", response_model=SuccessResponse[List[DocumentInfoResponse]])
async def get_private_document_list(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    result = content_private_service.get_private_document_list(db, current_user.id)
    return success_response(data=result, msg="获取成功")


@router.put("/document/{doc_id}", summary="修改私有文档", response_model=SuccessResponse[DocumentInfoResponse])
async def update_private_document(
    doc_id: int = Path(..., description="文档ID"),
    request: DocumentUpdateRequest = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    result = content_private_service.update_document(db, doc_id, request, current_user.id)
    return success_response(data=result, msg="文档修改成功")


@router.delete("/document/{doc_id}", summary="删除私有文档")
async def delete_private_document(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    content_private_service.delete_document(db, doc_id, current_user.id)
    return success_response(msg="文档删除成功")


@router.post("/document/{doc_id}/parse", summary="解析私有文档并提取知识点")
async def parse_private_document(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    result = content_private_service.parse_and_extract_points(db, doc_id, current_user.id)
    return success_response(data=result, msg="文档解析成功")


@router.get("/document/{doc_id}/points", summary="获取私有文档知识点列表")
async def get_private_knowledge_points(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    result = content_private_service.get_private_knowledge_points(db, doc_id, current_user.id)
    return success_response(data=result, msg="获取成功")