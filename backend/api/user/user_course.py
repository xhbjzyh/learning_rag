from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

# 数据库连接（完全对齐管理员端导入路径）
from db.sqlite_conn import get_db
# 数据库模型
from models.db_models import Course, CourseResource, Exercise, WrongQuestion, CourseCategory, SysUser
# 校验模型
from models.schemas import (
    ResourceProgressUpdate, ExerciseSubmit
)
# 业务逻辑
from service.user.user_course_service import user_course_service
# 日志
from utils.logger import logger
# 认证中间件
from middleware.auth_middleware import get_current_user

# 路由配置（用户端专属标签）
router = APIRouter(
    prefix="/course",
    tags=["用户-课程学习"]
)


# ==============================================
# 🔵 0. 课程分类管理（新增：供前端三级筛选使用）
# ==============================================
@router.get("/categories", summary="获取课程分类树形列表")
def get_course_categories(db: Session = Depends(get_db)):
    """
    获取三级分类树形结构
    返回格式：[{id, name, description, parent_id, level, sort_order, children: [...]}]
    """
    try:
        def build_tree(parent_id: int = 0):
            categories = db.query(CourseCategory).filter(
                CourseCategory.parent_id == parent_id
            ).order_by(CourseCategory.sort_order).all()
            
            return [{
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "parent_id": cat.parent_id,
                "level": cat.level,
                "sort_order": cat.sort_order,
                "children": build_tree(cat.id)
            } for cat in categories]

        return {"code": 0, "msg": "获取分类成功", "data": build_tree()}
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程分类失败")


# ==============================================
# 🔵 1. 课程列表与详情
# ==============================================
@router.get("/list", summary="获取用户可见课程列表（分页+筛选）")
def get_course_list(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页条数"),
        category_id: Optional[int] = Query(None, description="分类ID"),
        difficulty: Optional[str] = Query(None, description="难度：简单/中等/困难"),
        title: Optional[str] = Query(None, description="课程名称模糊搜索"),
        keyword: Optional[str] = Query(None, description="关键词搜索（兼容前端）"),
        db: Session = Depends(get_db)
):
    try:
        # ✅ 兼容前端的 keyword 参数
        search_title = keyword or title
        
        result = user_course_service.get_course_list(db, page, size, category_id, difficulty, search_title)

        # 转换ORM对象为字典（对齐管理员端返回格式）
        course_list = []
        for course in result["items"]:
            course_list.append({
                "id": course.id,
                "title": course.title,
                "cover_url": course.cover_url,
                "description": course.description,
                "lecturer": course.lecturer,
                "category_id": course.category_id,
                "difficulty": course.difficulty,
                "view_count": course.view_count,
                "is_public": course.is_public,
                "create_time": course.create_time.isoformat() if course.create_time else None
            })

        return {
            "code": 0,
            "msg": "获取课程列表成功",
            "data": {
                "total": result["total"],
                "list": course_list,
                "page": result["page"],
                "size": result["size"]
            }
        }
    except Exception as e:
        logger.error(f"获取课程列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程列表失败")


@router.get("/course/{course_id}", summary="获取课程详情及用户学习进度")
def get_course_detail(
        course_id: int,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取课程详情
    - 自动从JWT Token获取当前用户ID
    - 无需前端传递user_id参数
    """
    try:
        result = user_course_service.get_course_detail(db, current_user.id, course_id)
        course = result["course"]
        user_progress = result["user_progress"]

        # 转换课程详情
        course_data = {
            "id": course.id,
            "title": course.title,
            "cover_url": course.cover_url,
            "description": course.description,
            "lecturer": course.lecturer,
            "category_id": course.category_id,
            "difficulty": course.difficulty,
            "view_count": course.view_count,
            "is_public": course.is_public,
            "create_time": course.create_time.isoformat() if course.create_time else None,
            "update_time": course.update_time.isoformat() if course.update_time else None,
            "resources": result["resources"],
            "user_progress": {
                "id": user_progress.id,
                "user_id": user_progress.user_id,
                "course_id": user_progress.course_id,
                "progress": user_progress.progress,
                "is_finished": user_progress.is_finished,
                "last_study_time": user_progress.last_study_time.isoformat() if user_progress.last_study_time else None,
                "total_study_duration": user_progress.total_study_duration
            } if user_progress else None
        }

        return {"code": 0, "msg": "获取课程详情成功", "data": course_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取课程详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程详情失败")


# ==============================================
# 🟢 2. 课程资源与学习进度
# ==============================================
@router.get("/{course_id}/materials", summary="获取课程所有资料（支持按类型筛选）")
def get_course_materials(
        course_id: int,
        resource_type: Optional[str] = Query(None, description="资源类型：videos/document/exercise"),
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        # 调用service层筛选逻辑
        materials = user_course_service.get_course_resources(db, course_id, resource_type, current_user.id)
        return {"code": 0, "msg": "获取课程资料成功", "data": materials}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取课程资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程资料失败")

# ==============================================
# 【原有】单个资源详情接口（不动，仅获取单个资源）
# ==============================================
@router.get("/resource/{resource_id}", summary="获取资源详情及用户学习进度")
def get_resource_detail(
        resource_id: int,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.get_resource_detail(db, current_user.id, resource_id)
        resource = result["resource"]
        progress = result["user_progress"]

        resource_data = {
            "id": resource.id,
            "course_id": resource.course_id,
            "title": resource.title,
            "type": resource.type,
            "description": resource.description,
            "url": resource.url,
            "duration": resource.duration,
            "file_size": resource.file_size,
            "file_type": resource.file_type,
            "exercise_id": resource.exercise_id,
            "sort_order": resource.sort_order,
            "is_published": resource.is_published,
            "create_time": resource.create_time.isoformat() if resource.create_time else None,
            "user_progress": {
                "id": progress.id,
                "user_id": progress.user_id,
                "resource_id": progress.resource_id,
                "progress": progress.progress,
                "is_finished": progress.is_finished,
                "last_study_time": progress.last_study_time.isoformat() if progress.last_study_time else None,
                "total_study_duration": progress.total_study_duration
            } if progress else None
        }

        return {"code": 0, "msg": "获取资源详情成功", "data": resource_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取资源详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源详情失败")

@router.post("/resource/{resource_id}/progress", summary="更新资源学习进度（视频/文档通用）")
def update_resource_progress(
        resource_id: int,
        data: ResourceProgressUpdate,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        progress = user_course_service.update_resource_progress(db, current_user.id, resource_id, data)
        
        # 如果是视频资源，同步更新知识点掌握度
        resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
        if resource and resource.type == "video":
            try:
                user_course_service.update_video_mastery(db, current_user.id, resource_id, data.progress)
            except Exception as e:
                logger.warning(f"更新视频掌握度失败: {str(e)}")
                # 不影响主流程，继续返回
        
        return {
            "code": 0,
            "msg": "更新学习进度成功",
            "data": {
                "progress": progress.progress,
                "is_finished": progress.is_finished,
                "total_study_duration": progress.total_study_duration
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"更新学习进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新学习进度失败")


# ==============================================
# 🟣 3. 习题练习与批改
# ==============================================
@router.get("/exercise/list", summary="获取习题列表（支持按课程筛选）")
def get_exercise_list(
        course_id: Optional[int] = Query(None, description="课程ID"),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.get_exercise_list(db, course_id, page, size)
        return {"code": 0, "msg": "获取习题列表成功", "data": result}
    except Exception as e:
        logger.error(f"获取习题列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取习题列表失败")


@router.get("/exercise/{exercise_id}", summary="获取习题详情（隐藏答案）")
def get_exercise_detail(
        exercise_id: int,
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.get_exercise_detail(db, exercise_id)
        return {"code": 0, "msg": "获取习题详情成功", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取习题详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取习题详情失败")


@router.post("/exercise/submit", summary="提交习题答案并自动记录错题")
def submit_exercise_answer(
        data: ExerciseSubmit,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.submit_exercise_answer(db, current_user.id, data)
        return {"code": 0, "msg": "提交答案成功", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"提交习题答案失败: {str(e)}")
        raise HTTPException(status_code=500, detail="提交答案失败")


# ==============================================
# 🟡 4. 错题本管理
# ==============================================
@router.get("/wrong-question/list", summary="获取错题本列表")
def api_get_wrong_question_list(
    current_user: SysUser = Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, le=100, description="每页条数"),
    db: Session = Depends(get_db)
):
    # 直接调用服务层，返回处理好的字典
    return user_course_service.get_wrong_question_list(db, current_user.id, page, size)

@router.post("/wrong-question/{wrong_id}/mastered", summary="标记错题已掌握")
def mark_wrong_mastered(
        wrong_id: int,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.mark_wrong_mastered(db, current_user.id, wrong_id)
        return {"code": 0, "msg": "标记成功", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"标记错题失败: {str(e)}")
        raise HTTPException(status_code=500, detail="标记失败")


@router.delete("/wrong-question/{wrong_id}", summary="从错题本移除题目")
def remove_wrong_question(
        wrong_id: int,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.remove_wrong_question(db, current_user.id, wrong_id)
        return {"code": 0, "msg": "移除成功", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"移除错题失败: {str(e)}")
        raise HTTPException(status_code=500, detail="移除失败")


# ==============================================
# 🟠 5. 大模型专项练习与个性化推荐
# ==============================================
@router.post("/practice/generate", summary="基于错题/知识点生成专项练习题")
async def generate_special_practice(
        wrong_id: Optional[int] = Query(None, description="错题ID"),
        point_id: Optional[int] = Query(None, description="知识点ID"),
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        result = await user_course_service.generate_special_practice(db, current_user.id, wrong_id, point_id)
        return {"code": 0, "msg": "生成练习题成功", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"生成专项练习失败: {str(e)}")
        raise HTTPException(status_code=500, detail="生成练习题失败，请稍后重试")


@router.get("/recommendations", summary="获取个性化课程推荐")
def get_personalized_recommendations(
        limit: int = Query(10, ge=1, le=20),
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        result = user_course_service.get_personalized_recommendations(db, current_user.id, limit)
        return {"code": 0, "msg": "获取推荐成功", "data": result}
    except Exception as e:
        logger.error(f"获取个性化推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取推荐失败")


# ==============================================
# 🟣 6. 课程个性化推荐与掌握情况
# ==============================================
@router.get("/{course_id}/recommendations", summary="获取课程个性化学习路径推荐")
def get_course_recommendations(
        course_id: int,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    基于用户画像和课程知识点，生成个性化学习路径推荐
    """
    try:
        result = user_course_service.get_course_learning_path(db, current_user.id, course_id)
        return {"code": 0, "msg": "获取学习路径成功", "data": result}
    except Exception as e:
        logger.error(f"获取学习路径失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取学习路径失败")


@router.get("/{course_id}/mastery", summary="获取课程知识点掌握情况")
def get_course_mastery(
        course_id: int,
        current_user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取用户对课程知识点的掌握情况统计
    """
    try:
        result = user_course_service.get_course_knowledge_mastery(db, current_user.id, course_id)
        return {"code": 0, "msg": "获取掌握情况成功", "data": result}
    except Exception as e:
        logger.error(f"获取掌握情况失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取掌握情况失败")
