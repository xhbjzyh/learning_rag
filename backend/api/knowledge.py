"""
知识库相关接口
文档上传、解析、分类管理、知识点查询等接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from service.knowledge_service import knowledge_service
from middleware.auth_middleware import get_current_user
from models.schemas import (
    CategoryCreateRequest,
    CategoryInfoResponse,
    DocumentUploadResponse,
    DocumentInfoResponse,
    KnowledgePointResponse,
    SuccessResponse,
    DocumentUpdateRequest,
    DocumentAuditRequest  # 新增审核模型
)
from models.db_models import SysUser
from utils.response import success_response, BusinessException

# ==================== 核心修复：删除内部重复前缀 /knowledge ====================
router = APIRouter(tags=["知识库模块"])


# ==================== 分类管理接口 ====================
@router.post("/category", summary="创建知识库分类", response_model=SuccessResponse[CategoryInfoResponse])
async def create_category(
    request: CategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建新的知识库分类（需要登录）"""
    result = knowledge_service.create_category(db, request)
    return success_response(data=result, msg="分类创建成功")


@router.get("/category/list", summary="获取分类列表", response_model=SuccessResponse[List[CategoryInfoResponse]])
async def get_category_list(
    db: Session = Depends(get_db)
):
    """获取所有知识库分类列表（无需登录）"""
    result = knowledge_service.get_category_list(db)
    return success_response(data=result, msg="获取成功")


# ==================== 文档管理接口 ====================
@router.post("/document/upload", summary="上传文档", response_model=SuccessResponse[DocumentUploadResponse])
async def upload_document(
    file: UploadFile = File(..., description="上传的文件"),
    title: str = Form(..., description="文档标题"),
    category_id: Optional[int] = Form(None, description="所属分类ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """上传文档到知识库（需要登录）"""
    result = await knowledge_service.upload_document(db, file, title, category_id, current_user.id)
    return success_response(data=result, msg="文档上传成功")


@router.get("/document/list", summary="获取文档列表", response_model=SuccessResponse[List[DocumentInfoResponse]])
async def get_document_list(
    my: bool = Query(False, description="是否只看自己上传的"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取文档列表（需要登录）"""
    user_id = current_user.id if my else None
    result = knowledge_service.get_document_list(db, user_id)
    return success_response(data=result, msg="获取成功")


@router.get("/document/{doc_id}", summary="获取文档详情", response_model=SuccessResponse[DocumentInfoResponse])
async def get_document_detail(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """获取文档详情（无需登录）"""
    result = knowledge_service.get_document_detail(db, doc_id)
    return success_response(data=result, msg="获取成功")

# 新增：修改文档信息（RESTful规范）
@router.put("/document/{doc_id}", summary="修改文档信息", response_model=SuccessResponse[DocumentInfoResponse])
async def update_document(
    doc_id: int,
    request: DocumentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """修改文档信息（仅上传者/管理员可操作）"""
    result = knowledge_service.update_document(db, doc_id, request, current_user.id, current_user.role_id)
    return success_response(data=result, msg="文档修改成功")

# 新增：文档审核接口（仅管理员/审核员可调用）
@router.put("/document/{doc_id}/audit", summary="文档审核", response_model=SuccessResponse[DocumentInfoResponse])
async def audit_document(
    doc_id: int,
    request: DocumentAuditRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    文档审核
    权限：超级管理员(1)、审核员(2)
    状态：1=通过，2=驳回
    """
    result = knowledge_service.audit_document(db, doc_id, request, current_user.role_id)
    return success_response(data=result, msg="文档审核成功")

# 新增：级联删除文档（RESTful规范）
@router.delete("/document/{doc_id}", summary="删除文档", response_model=SuccessResponse)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除文档（仅上传者/管理员可操作），自动删除知识点+本地文件"""
    knowledge_service.delete_document(db, doc_id, current_user.id, current_user.role_id)
    return success_response(msg="文档及关联数据删除成功")


@router.post("/document/{doc_id}/parse", summary="解析文档并提取知识点", response_model=SuccessResponse[dict])
async def parse_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """解析文档并提取知识点（需要登录，仅审核通过的文档可解析）"""
    result = knowledge_service.parse_and_extract_points(db, doc_id)
    return success_response(data=result, msg="文档解析成功")


# ==================== 知识点接口 ====================
@router.get("/document/{doc_id}/points", summary="获取文档知识点列表", response_model=SuccessResponse[List[KnowledgePointResponse]])
async def get_knowledge_points(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的所有知识点（无需登录）"""
    result = knowledge_service.get_knowledge_points(db, doc_id)
    return success_response(data=result, msg="获取成功")