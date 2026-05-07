"""
管理员-内容全局管理接口
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from urllib.parse import quote

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user, role_required
from models.schemas import (
    CategoryCreateRequest,
    CategoryInfoResponse,
    KnowledgePointResponse,
    DocumentInfoResponse,
    SuccessResponse
)
from models.db_models import (
    SysUser, KnowledgePoint, KnowledgePointTagRel,
    KnowledgeDocument, KnowledgeCategory
)
from service.admin.content_global_service import content_global_service
from utils.response import success_response, BusinessException

router = APIRouter(
    prefix="/content",
    tags=["管理员-内容全局管理"],
    dependencies=[Depends(role_required([1, 2]))]
)


# ==================== 分类管理（完善） ====================
@router.post("/category", summary="创建知识库分类", response_model=SuccessResponse[CategoryInfoResponse])
async def create_category(
    request: CategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    result = content_global_service.create_category(db, request)
    return success_response(data=result, msg="分类创建成功")


@router.get("/category/list", summary="获取分类列表", response_model=SuccessResponse[list[CategoryInfoResponse]])
async def get_category_list(db: Session = Depends(get_db)):
    result = content_global_service.get_category_list(db)
    return success_response(data=result, msg="获取成功")


@router.put("/category/{category_id}", summary="修改知识库分类")
async def update_category(
    category_id: int,
    category_name: str = Query(..., description="分类名称"),
    description: str = Query(None, description="分类描述"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """新增：修改分类"""
    category = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == category_id).first()
    if not category:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="分类不存在")

    category.category_name = category_name
    if description:
        category.description = description

    db.commit()
    db.refresh(category)
    return success_response(msg="分类修改成功")


@router.delete("/category/{category_id}", summary="删除知识库分类")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """新增：删除分类"""
    category = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == category_id).first()
    if not category:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="分类不存在")

    # 检查是否有文档使用该分类
    doc_count = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.category_id == category_id
    ).count()

    if doc_count > 0:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="该分类下还有文档，无法删除")

    db.delete(category)
    db.commit()
    return success_response(msg="分类删除成功")


# ==================== 知识点管理（保持原样） ====================
@router.get("/knowledge/list", summary="管理员分页查询知识点")
async def admin_get_knowledge_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgePoint)
    total = query.count()
    points = query.order_by(KnowledgePoint.create_time.desc()).offset((page-1)*size).limit(size).all()
    items = [KnowledgePointResponse.model_validate(p) for p in points]
    return success_response(data={"total": total, "items": items, "page": page, "size": size})


@router.get("/knowledge/point/{point_id}", summary="管理员查看知识点详情")
async def admin_get_knowledge_detail(
    point_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    if not point:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="知识点不存在")
    return success_response(data=KnowledgePointResponse.model_validate(point))


@router.post("/knowledge/point/{point_id}", summary="管理员修改知识点")
async def admin_update_knowledge(
    point_id: int,
    title: str = Query(None),
    content: str = Query(None),
    difficulty: str = Query(None),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    if not point:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="知识点不存在")
    if title: point.title = title
    if content: point.content = content
    if difficulty: point.difficulty = difficulty
    db.commit()
    return success_response(data=KnowledgePointResponse.model_validate(point), msg="修改成功")


@router.delete("/knowledge/point/{point_id}", summary="管理员删除知识点")
async def admin_delete_knowledge(
    point_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    if not point:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="知识点不存在")
    db.query(KnowledgePointTagRel).filter(KnowledgePointTagRel.point_id == point_id).delete()
    db.delete(point)
    db.commit()
    return success_response(msg="知识点删除成功")


# ==================== 全局文档管理（完善核心功能） ====================
@router.get("/document/list", summary="管理员获取全局文档列表")
async def get_global_document_list(
    category_id: Optional[int] = Query(None, description="分类ID，可选"),
    audit_status: Optional[int] = Query(None, description="审核状态：0-未提交，1-已通过，2-待审核，3-已拒绝"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """新增：管理员获取全局文档列表（核心功能）"""
    # 构建查询
    query = db.query(KnowledgeDocument)

    # 分类筛选
    if category_id:
        query = query.filter(KnowledgeDocument.category_id == category_id)

    # 审核状态筛选
    if audit_status is not None:
        query = query.filter(KnowledgeDocument.audit_status == audit_status)

    # 公开状态筛选
    if is_public is not None:
        query = query.filter(KnowledgeDocument.is_public == is_public)

    # 计算总数
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    documents = query.order_by(KnowledgeDocument.create_time.desc()).offset(offset).limit(page_size).all()

    # 构建返回数据
    result_list = []
    for doc in documents:
        # 查询分类
        category = db.query(KnowledgeCategory).filter(
            KnowledgeCategory.id == doc.category_id
        ).first()

        # 查询上传用户
        user = db.query(SysUser).filter(
            SysUser.id == doc.upload_user_id
        ).first()

        result_list.append({
            "id": doc.id,
            "title": doc.title,
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "category_id": doc.category_id,
            "category_name": category.category_name if category else "未分类",
            "upload_user_id": doc.upload_user_id,
            "upload_username": user.username if user else "未知用户",
            "audit_status": doc.audit_status,
            "is_public": doc.is_public,
            "create_time": doc.create_time.strftime("%Y-%m-%d %H:%M:%S") if doc.create_time else None,
            "update_time": doc.update_time.strftime("%Y-%m-%d %H:%M:%S") if doc.update_time else None
        })

    return success_response(data={
        "list": result_list,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/document/{doc_id}", summary="管理员获取文档详情")
async def get_global_document_detail(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """新增：管理员获取文档详情"""
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not document:
        # ✅ 修复：添加 code 参数
        raise BusinessException(code=-1, msg="文档不存在")

    # 查询分类
    category = db.query(KnowledgeCategory).filter(
        KnowledgeCategory.id == document.category_id
    ).first()

    # 查询上传用户
    user = db.query(SysUser).filter(
        SysUser.id == document.upload_user_id
    ).first()

    return success_response(data={
        "id": document.id,
        "title": document.title,
        "file_name": document.file_name,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "category_id": document.category_id,
        "category_name": category.category_name if category else "未分类",
        "upload_user_id": document.upload_user_id,
        "upload_username": user.username if user else "未知用户",
        "audit_status": document.audit_status,
        "is_public": document.is_public,
        "create_time": document.create_time.strftime("%Y-%m-%d %H:%M:%S") if document.create_time else None,
        "update_time": document.update_time.strftime("%Y-%m-%d %H:%M:%S") if document.update_time else None
    })


@router.get("/document/{doc_id}/download", summary="管理员下载任意文档")
async def download_global_document(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """新增：管理员下载任意文档（包括未公开的）"""
    # 查询文档信息（不限制公开状态）
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

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


@router.delete("/document/{doc_id}", summary="全局删除文档")
async def delete_document_global(
    doc_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content_global_service.delete_document_global(db, doc_id)
    return success_response(msg="文档删除成功")