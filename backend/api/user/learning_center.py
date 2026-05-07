"""
用户-学习中心接口
新增：错题本、学习进度、学习统计
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from service.user.learning_center_service import learning_center_service
from utils.response import success_response, ApiResponse

router = APIRouter(
    prefix="/learning",
    tags=["用户-学习中心"],
    dependencies=[Depends(get_current_user)]
)


# ... 保留原有 add_learning_record 和 get_learn_history 接口 ...

# ==================== 错题本接口 ====================
@router.post(
    "/wrong/add",
    summary="添加错题记录",
    response_model=ApiResponse
)
async def add_wrong_question(
    point_id: int = Query(..., description="知识点ID", ge=1),
    question: str = Query(..., description="题目内容"),
    user_answer: str = Query(..., description="用户答案"),
    correct_answer: str = Query(..., description="正确答案"),
    error_reason: str = Query(None, description="错误原因"),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=learning_center_service.add_wrong_question(
            db=db,
            user_id=current_user.id,
            point_id=point_id,
            question=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            error_reason=error_reason
        ),
        msg="错题添加成功"
    )


@router.get(
    "/wrong/list",
    summary="获取错题列表",
    response_model=ApiResponse
)
async def get_wrong_question_list(
    master_level: int = Query(None, description="掌握程度：0=未掌握，1=部分掌握，2=已掌握", ge=0, le=2),
    page: int = Query(1, description="页码", ge=1),
    size: int = Query(10, description="每页数量", ge=1, le=50),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=learning_center_service.get_wrong_question_list(
            db=db,
            user_id=current_user.id,
            master_level=master_level,
            page=page,
            size=size
        ),
        msg="获取错题列表成功"
    )


@router.put(
    "/wrong/{wrong_id}/mastery",
    summary="更新错题掌握程度",
    response_model=ApiResponse
)
async def update_wrong_question_mastery(
    wrong_id: int = Path(..., description="错题ID", ge=1),
    master_level: int = Query(..., description="掌握程度：0=未掌握，1=部分掌握，2=已掌握", ge=0, le=2),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=learning_center_service.update_wrong_question_mastery(
            db=db,
            user_id=current_user.id,
            wrong_id=wrong_id,
            master_level=master_level
        ),
        msg="掌握程度更新成功"
    )


# ==================== 学习进度接口 ====================
@router.post(
    "/progress/update",
    summary="更新学习进度",
    response_model=ApiResponse
)
async def update_learning_progress(
    point_id: int = Query(..., description="知识点ID", ge=1),
    progress: float = Query(..., description="学习进度：0-100%", ge=0, le=100),
    study_duration: int = Query(0, description="本次学习时长，单位：秒", ge=0),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=learning_center_service.update_learning_progress(
            db=db,
            user_id=current_user.id,
            point_id=point_id,
            progress=progress,
            study_duration=study_duration
        ),
        msg="学习进度更新成功"
    )


@router.get(
    "/stats",
    summary="获取学习统计数据",
    response_model=ApiResponse
)
async def get_learning_stats(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=learning_center_service.get_user_learning_stats(db, current_user.id),
        msg="获取学习统计成功"
    )