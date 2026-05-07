from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from models.schemas import (
    ExerciseSubmitRequest,
    SuccessResponse,
    ExerciseSubmitResponse,
    UserExerciseRecordItem,
    WrongQuestionItem
)
from service.user.exercise_record_service import exercise_record_service

router = APIRouter()


@router.post("/submit", summary="提交答题", response_model=SuccessResponse[ExerciseSubmitResponse])
async def submit_exercise(
    data: ExerciseSubmitRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """提交答题并自动判分"""
    result = exercise_record_service.submit_answer(db, current_user.id, data)
    return SuccessResponse(data=result)


@router.get("/records", summary="获取我的答题记录", response_model=SuccessResponse[dict])
async def get_my_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取当前用户的答题记录"""
    result = exercise_record_service.get_user_records(db, current_user.id, page, size)
    return SuccessResponse(data=result)


@router.get("/wrong", summary="获取我的错题本", response_model=SuccessResponse[dict])
async def get_my_wrong_questions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取当前用户的错题本"""
    result = exercise_record_service.get_wrong_questions(db, current_user.id, page, size)
    return SuccessResponse(data=result)


@router.post("/wrong/{wrong_id}/master", summary="标记错题已掌握", response_model=SuccessResponse)
async def mark_wrong_mastered(
    wrong_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """标记错题为已掌握"""
    exercise_record_service.mark_wrong_mastered(db, current_user.id, wrong_id)
    return SuccessResponse(msg="标记成功")


@router.delete("/wrong/{wrong_id}", summary="移除错题", response_model=SuccessResponse)
async def remove_wrong_question(
    wrong_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """从错题本移除错题"""
    exercise_record_service.remove_wrong_question(db, current_user.id, wrong_id)
    return SuccessResponse(msg="移除成功")