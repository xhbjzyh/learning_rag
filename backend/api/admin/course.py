from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

# 数据库连接
from db.sqlite_conn import get_db
# 数据库模型
from models.db_models import CourseCategory, Course, CourseResource
# 校验模型
from models.schemas import (
    AdminCourseCreateRequest, AdminCourseUpdateRequest,
    CourseResourceCreate, CourseResourceUpdate, ResourceProgressUpdate,CourseResourceFileUpload
)
# 业务逻辑
from service.admin.course_service import admin_course_service
# 日志
from utils.logger import logger

# 路由配置：最终路径 /api/admin/course/xxx
router = APIRouter(
    prefix="/course",
    tags=["管理员-课程管理"]
)


# ==============================================
# 🔴 课程分类管理 接口
# ==============================================
class CourseCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: int = 0
    sort_order: int = 0


class CourseCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("/categories", summary="获取课程分类树形列表")
def get_course_categories(db: Session = Depends(get_db)):
    try:
        def build_tree(parent_id: int = 0):
            categories = db.query(CourseCategory).filter(CourseCategory.parent_id == parent_id).all()
            return [{
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "parent_id": cat.parent_id,
                "level": cat.level,
                "sort_order": cat.sort_order,
                "children": build_tree(cat.id)
            } for cat in categories]

        return {"code": 0, "msg": "success", "data": build_tree()}
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程分类失败")


@router.post("/categories", summary="新增课程分类")
def create_category(data: CourseCategoryCreate, db: Session = Depends(get_db)):
    try:
        # 校验父分类
        if data.parent_id != 0:
            parent = db.query(CourseCategory).get(data.parent_id)
            if not parent:
                raise HTTPException(status_code=400, detail="父分类不存在")
            if parent.level >= 3:
                raise HTTPException(status_code=400, detail="最多支持三级分类")
            level = parent.level + 1
        else:
            level = 1

        # 校验同级重名
        exist = db.query(CourseCategory).filter(
            CourseCategory.name == data.name,
            CourseCategory.parent_id == data.parent_id
        ).first()
        if exist:
            raise HTTPException(status_code=400, detail="同级分类名称已存在")

        category = CourseCategory(
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            level=level,
            sort_order=data.sort_order
        )
        db.add(category)
        db.commit()
        return {"code": 0, "msg": "新增分类成功"}
    except Exception as e:
        db.rollback()
        logger.error(f"新增分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail="新增分类失败")


@router.put("/categories/{category_id}", summary="编辑课程分类")
def update_category(category_id: int, data: CourseCategoryUpdate, db: Session = Depends(get_db)):
    category = db.query(CourseCategory).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    if data.name:
        exist = db.query(CourseCategory).filter(
            CourseCategory.name == data.name,
            CourseCategory.parent_id == category.parent_id,
            CourseCategory.id != category_id
        ).first()
        if exist:
            raise HTTPException(status_code=400, detail="分类名称重复")
        category.name = data.name

    if data.description is not None:
        category.description = data.description
    if data.sort_order is not None:
        category.sort_order = data.sort_order

    db.commit()
    return {"code": 0, "msg": "编辑成功"}


@router.delete("/categories/{category_id}", summary="删除课程分类")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(CourseCategory).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 校验子分类
    if db.query(CourseCategory).filter(CourseCategory.parent_id == category_id).count() > 0:
        raise HTTPException(status_code=400, detail="该分类下存在子分类，无法删除")
    # 校验关联课程
    if db.query(Course).filter(Course.category_id == category_id).count() > 0:
        raise HTTPException(status_code=400, detail="该分类下存在课程，无法删除")

    db.delete(category)
    db.commit()
    return {"code": 0, "msg": "删除成功"}


# ==============================================
# 🔵 课程管理 接口
# ==============================================
@router.get("/list", summary="课程列表（分页+搜索）")
def get_course_list(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        title: Optional[str] = None,
        db: Session = Depends(get_db)
):
    try:
        data = admin_course_service.get_course_list(db, page, size, title)
        return {"code": 0, "msg": "获取课程列表成功", "data": data}
    except Exception as e:
        logger.error(f"获取课程列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程列表失败")


@router.post("/create", summary="创建课程")
def create_course(data: AdminCourseCreateRequest, db: Session = Depends(get_db)):
    try:
        course = admin_course_service.create_course(db, data)
        return {"code": 0, "msg": "创建课程成功", "data": course}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"创建课程失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建课程失败")


@router.put("/update/{course_id}", summary="更新课程")
def update_course(
        course_id: int,
        data: AdminCourseUpdateRequest,
        db: Session = Depends(get_db)
):
    try:
        course = admin_course_service.update_course(db, course_id, data)
        return {"code": 0, "msg": "更新课程成功", "data": course}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"更新课程失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新课程失败")


@router.delete("/delete/{course_id}", summary="删除课程")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    try:
        admin_course_service.delete_course(db, course_id)
        return {"code": 0, "msg": "删除课程成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除课程失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除课程失败")


# ==============================================
# 🟢 新增：课程资料管理 接口
# ==============================================
@router.get("/{course_id}/materials", summary="获取课程所有资料（支持按类型筛选）")
def get_course_materials(
        course_id: int,
        resource_type: Optional[str] = Query(None, description="资源类型：video/document/exercise"),
        db: Session = Depends(get_db)
):
    try:
        materials = admin_course_service.get_course_resources(db, course_id, resource_type)
        return {"code": 0, "msg": "获取课程资料成功", "data": materials}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取课程资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程资料失败")


@router.post("/{course_id}/materials", summary="创建课程资料并关联知识点")
def create_course_material(
        course_id: int,
        data: CourseResourceCreate,
        db: Session = Depends(get_db)
):
    try:
        material = admin_course_service.create_resource(db, course_id, data)
        return {"code": 0, "msg": "创建课程资料成功", "data": material}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"创建课程资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建课程资料失败")


@router.put("/materials/{material_id}", summary="更新课程资料及关联知识点")
def update_course_material(
        material_id: int,
        data: CourseResourceUpdate,
        db: Session = Depends(get_db)
):
    try:
        material = admin_course_service.update_resource(db, material_id, data)
        return {"code": 0, "msg": "更新课程资料成功", "data": material}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"更新课程资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新课程资料失败")


@router.delete("/materials/{material_id}", summary="删除课程资料（级联删除学习进度）")
def delete_course_material(
        material_id: int,
        db: Session = Depends(get_db)
):
    try:
        admin_course_service.delete_resource(db, material_id)
        return {"code": 0, "msg": "删除课程资料成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除课程资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除课程资料失败")


# ==============================================
# 🟡 新增：学习进度管理 接口（管理员测试用）
# ==============================================
@router.post("/materials/{material_id}/progress", summary="更新用户学习进度（管理员测试专用）")
def update_material_progress(
        material_id: int,
        user_id: int = Query(..., description="用户ID"),
        data: ResourceProgressUpdate = ...,
        db: Session = Depends(get_db)
):
    try:
        # 获取资源类型，自动分发到对应的更新方法
        resource = db.query(CourseResource).get(material_id)
        if not resource:
            raise HTTPException(status_code=404, detail="课程资料不存在")

        if resource.type == "video":
            progress = admin_course_service.update_video_progress(db, user_id, material_id, data)
        elif resource.type == "exercise":
            progress = admin_course_service.update_exercise_result(db, user_id, material_id, data)
        elif resource.type == "document":
            progress = admin_course_service.update_document_progress(db, user_id, material_id, data)
        else:
            raise HTTPException(status_code=400, detail="不支持的资源类型")

        return {"code": 0, "msg": "更新学习进度成功", "data": progress}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"更新学习进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新学习进度失败")
from fastapi import File, UploadFile
from fastapi.responses import FileResponse

# 上传课程资料（文件 + 关联知识点）
@router.post("/resource/upload")
def upload_resource(
    course_id: int,
    knowledge_ids: list[int],
    title: str,
    type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    data = CourseResourceFileUpload(
        course_id=course_id,
        title=title,
        type=type,
        knowledge_ids=knowledge_ids
    )
    return admin_course_service.create_resource_with_file(db, course_id, data, file)

# 下载课程资料
@router.get("/resource/download/{resource_id}")
def download_resource(resource_id: int, db: Session=Depends(get_db)):
    path, name = admin_course_service.download_resource(db, resource_id)
    return FileResponse(path, filename=name)