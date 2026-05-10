"""
课程系统接口
接口列表：
1. GET /categories - 获取三级分类
2. GET /list - 获取课程列表
3. GET /{course_id} - 获取课程详情
4. POST /{course_id}/progress - 更新课程进度
5. POST /resource/{resource_id}/progress - 更新资源进度
6. POST /qa/ask - 知识点问答（调用大模型）
7. PUT /qa/{qa_id}/feedback - 问答结果反馈
8. GET /qa/history - 获取问答历史
9. GET /qa/{qa_id} - 获取问答详情
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser, CourseResource
from models.schemas import (
    SuccessResponse, CourseCategoryItem, CourseListItem, CourseDetailItem,
    ResourceProgressUpdate, KnowledgeQaFeedbackUpdate
)
# 🔥 修复：导入正确的服务单例
from service.user.course_service import user_course_service
from service.user.qa_service import user_qa_service
from utils.response import success_response

router = APIRouter(
    prefix="/course",
    tags=["用户-课程中心"],
    dependencies=[Depends(get_current_user)]
)


# ==============================================
# 🔵 原有课程管理接口（完全保留，修复单例调用）
# ==============================================
@router.get(
    "/categories",
    summary="获取课程三级分类",
    response_model=SuccessResponse[list[CourseCategoryItem]]
)
async def get_course_categories(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取所有课程分类（三级树形结构）"""
    # 🔥 修复：使用正确的单例名称
    result = user_course_service.get_course_categories(db)
    return success_response(data=result, msg="获取分类成功")


@router.get(
    "/list",
    summary="获取课程列表",
    response_model=SuccessResponse[dict]
)
async def get_course_list(
    category_id: Optional[int] = Query(None, description="分类ID（不传则查全部）"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取课程列表（带分类筛选、关键词搜索、分页）"""
    # 🔥 修复：使用正确的单例名称
    result = user_course_service.get_course_list(
        db=db,
        category_id=category_id,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    return success_response(data=result, msg="获取课程列表成功")


@router.get(
    "/{course_id}",
    summary="获取课程详情",
    response_model=SuccessResponse[CourseDetailItem]
)
async def get_course_detail(
    course_id: int = Path(..., description="课程ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取课程详情（包含资源、知识点、习题、用户进度）"""
    # 🔥 修复：使用正确的单例名称
    result = user_course_service.get_course_detail(
        db=db,
        course_id=course_id,
        user_id=current_user.id
    )
    return success_response(data=result, msg="获取课程详情成功")


@router.post(
    "/{course_id}/progress",
    summary="更新课程学习进度",
    response_model=SuccessResponse[dict]
)
async def update_course_progress(
    course_id: int = Path(..., description="课程ID"),
    progress: float = Query(..., description="学习进度（0-100）", ge=0, le=100),
    study_duration: int = Query(0, description="本次学习时长（秒）", ge=0),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新课程学习进度"""
    # 🔥 修复：使用正确的单例名称
    result = user_course_service.update_course_progress(
        db=db,
        course_id=course_id,
        user_id=current_user.id,
        progress=progress,
        study_duration=study_duration
    )
    return success_response(data=result, msg="更新进度成功")


@router.post(
    "/resource/{resource_id}/progress",
    summary="更新资源学习进度",
    response_model=SuccessResponse[dict]
)
async def update_resource_progress(
        *,  # 🔥 加入这一行，强制后面的参数为关键字参数
        resource_id: int = Path(..., description="资源ID"),
        data: ResourceProgressUpdate,
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    # 函数体保持不变
    resource = db.query(CourseResource).get(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    if resource.type == "video":
        result = user_course_service.update_video_progress(db, current_user.id, resource_id, data)
    elif resource.type == "exercise":
        result = user_course_service.submit_exercise(db, current_user.id, resource_id, data)
    elif resource.type == "document":
        result = user_course_service.update_document_progress(db, current_user.id, resource_id, data)
    else:
        raise HTTPException(status_code=400, detail="不支持的资源类型")

    return success_response(data=result, msg="更新进度成功")
# ==============================================
# 🟢 知识点问答接口（修复参数顺序）
# ==============================================
@router.post(
    "/qa/ask",
    summary="知识点问答（调用大模型回答）",
    response_model=SuccessResponse[dict]
)
async def ask_knowledge_question(
    knowledge_point_id: int = Query(..., description="关联知识点ID"),
    question: str = Query(..., min_length=1, description="用户问题"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    用户针对指定知识点提问
    系统会调用大模型基于知识点内容回答，并自动保存问答记录
    问答结果会同步更新用户的知识点掌握度
    """
    result = await user_qa_service.ask_question(
        db=db,
        user_id=current_user.id,
        knowledge_point_id=knowledge_point_id,
        question=question
    )
    return success_response(data=result, msg="提问成功")


@router.put(
    "/qa/{qa_id}/feedback",
    summary="提交问答结果反馈",
    response_model=SuccessResponse[dict]
)
def submit_qa_feedback(
    *,  # 🔥 加入这一行
    qa_id: int = Path(..., description="问答记录ID"),
    data: KnowledgeQaFeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    # 函数体保持不变
    result = user_qa_service.update_feedback(
        db=db,
        user_id=current_user.id,
        qa_id=qa_id,
        data=data
    )
    return success_response(data=result, msg="反馈提交成功")


@router.get(
    "/qa/history",
    summary="获取我的问答历史",
    response_model=SuccessResponse[dict]
)
def get_my_qa_history(
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(10, description="每页数量", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取当前用户的所有问答历史记录（分页）"""
    result = user_qa_service.get_user_qa_history(
        db=db,
        user_id=current_user.id,
        page=page,
        size=page_size
    )
    return success_response(data=result, msg="获取历史记录成功")


@router.get(
    "/qa/{qa_id}",
    summary="获取问答详情",
    response_model=SuccessResponse[dict]
)
def get_qa_detail(
    qa_id: int = Path(..., description="问答记录ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取指定问答记录的详细信息及关联资源"""
    result = user_qa_service.get_qa_detail(
        db=db,
        user_id=current_user.id,
        qa_id=qa_id
    )
    return success_response(data=result, msg="获取问答详情成功")