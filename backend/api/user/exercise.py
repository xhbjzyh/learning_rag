"""
习题模块接口
权限设计：
- 普通用户：仅可查询（列表、详情）、提交答题
- 管理员/审核员：可增删改查
"""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional

from db.sqlite_conn import get_db
from middleware.auth_middleware import role_required, get_current_user
from service.user.exercise_service import exercise_service
from models.schemas import ExerciseCreate, ExerciseUpdate, ExerciseListResponse, ExerciseItem
from models.db_models import SysUser
from utils.response import success_response

router = APIRouter(
    tags=["用户端-习题管理"]
)


# ------------------------------
# 普通用户可访问接口（仅查询 + 提交答题）
# ------------------------------
@router.get("/list", summary="习题分页列表", response_model=ExerciseListResponse)
async def exercise_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return exercise_service.get_list(db, page, size, keyword)


@router.get("/{exercise_id}", summary="习题详情", response_model=ExerciseItem)
async def exercise_detail(exercise_id: int, db: Session = Depends(get_db)):
    return exercise_service.get_detail(db, exercise_id)


# 🔥 新增：提交答题接口
@router.post("/submit", summary="提交答题")
async def submit_exercise_answer(
    exercise_id: int = Body(..., embed=True, description="习题ID"),
    user_answer: str = Body(..., embed=True, description="用户答案"),
    answer_time: int = Body(None, embed=True, description="答题时长（秒）"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """
    提交答题并自动更新知识点掌握度
    """
    result = exercise_service.submit_answer(
        db=db,
        exercise_id=exercise_id,
        user_answer=user_answer,
        user_id=current_user.id,
        answer_time=answer_time
    )
    return success_response(data=result)


# ------------------------------
# 仅管理员/审核员可访问接口（增删改）
# ------------------------------
@router.post("/add", summary="新增习题", dependencies=[Depends(role_required([1, 2]))])
async def exercise_add(
    data: ExerciseCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    eid = exercise_service.create_exercise(db, data, current_user.id)
    return {"code": 0, "msg": "新增成功", "data": {"exercise_id": eid}}


@router.post("/edit", summary="编辑习题", dependencies=[Depends(role_required([1, 2]))])
async def exercise_edit(
    data: ExerciseUpdate = Body(...),
    db: Session = Depends(get_db)
):
    exercise_service.update_exercise(db, data)
    return {"code": 0, "msg": "编辑成功"}


@router.delete("/{exercise_id}", summary="删除习题", dependencies=[Depends(role_required([1, 2]))])
async def exercise_del(
    exercise_id: int,
    db: Session = Depends(get_db)
):
    exercise_service.delete_exercise(db, exercise_id)
    return {"code": 0, "msg": "删除成功"}