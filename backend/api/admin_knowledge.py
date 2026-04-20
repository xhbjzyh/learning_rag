from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser, KnowledgePoint, KnowledgePointTagRel
from models.schemas import KnowledgePointResponse
from utils.response import success_response, BusinessException

router = APIRouter()

# 权限校验
def check_admin(user: SysUser):
    if user.role_id not in (1, 2):
        raise BusinessException(msg="无权限，仅管理员可操作")

# 管理员分页查询知识点
@router.get("/admin/knowledge/list", summary="管理员分页查询知识点", tags=["管理员-知识点管理"])
async def admin_get_knowledge_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    query = db.query(KnowledgePoint)
    total = query.count()
    points = query.offset((page-1)*size).limit(size).all()
    items = [KnowledgePointResponse.model_validate(p) for p in points]
    return success_response(data={"total": total, "items": items, "page": page, "size": size})

# 管理员查看知识点详情
@router.get("/admin/knowledge/point/{point_id}", summary="管理员查看知识点详情", tags=["管理员-知识点管理"])
async def admin_get_knowledge_detail(
    point_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    if not point:
        raise BusinessException(msg="知识点不存在")
    return success_response(data=KnowledgePointResponse.model_validate(point))

# 管理员修改知识点
@router.post("/admin/knowledge/point/{point_id}", summary="管理员修改知识点", tags=["管理员-知识点管理"])
async def admin_update_knowledge(
    point_id: int,
    title: str = Query(None),
    content: str = Query(None),
    difficulty: str = Query(None),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    if not point:
        raise BusinessException(msg="知识点不存在")
    if title: point.title = title
    if content: point.content = content
    if difficulty: point.difficulty = difficulty
    db.commit()
    return success_response(data=KnowledgePointResponse.model_validate(point), msg="修改成功")

# ==================== RESTful规范修复：删除知识点（DELETE+路径参数） ====================
@router.delete("/admin/knowledge/point/{point_id}", summary="管理员删除知识点", tags=["管理员-知识点管理"])
async def admin_delete_knowledge(
    point_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    if not point:
        raise BusinessException(msg="知识点不存在")
    # 级联删除标签关联
    db.query(KnowledgePointTagRel).filter(KnowledgePointTagRel.point_id == point_id).delete()
    db.delete(point)
    db.commit()
    return success_response(msg="知识点删除成功")