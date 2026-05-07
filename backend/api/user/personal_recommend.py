"""
用户-个性化推荐接口
新增：学习路径生成
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List  # 🔥 添加这一行！
from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from models.schemas import SuccessResponse, KnowledgePointRecommendItem, LearningPathItem
from service.user.personal_recommend_service import personal_recommend_service

router = APIRouter(
    tags=["用户-个性化推荐"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "/personal",
    summary="获取个性化推荐知识点",
    description="基于用户画像标签权重，优先推荐薄弱知识点",
    response_model=SuccessResponse[List[KnowledgePointRecommendItem]]
)
async def get_personal_recommend(
    top_k: int = Query(10, description="推荐的知识点数量", ge=1, le=20),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recommend_list = personal_recommend_service.get_personal_recommend(
        user_id=current_user.id,
        db=db,
        top_k=top_k
    )
    return SuccessResponse(
        data=recommend_list,
        msg="个性化推荐生成成功"
    )


@router.get(
    "/learning-path",
    summary="生成个性化学习路径",
    description="基于用户学习进度和薄弱点，生成循序渐进的学习顺序",
    response_model=SuccessResponse[List[LearningPathItem]]
)
async def generate_learning_path(
    max_length: int = Query(10, description="学习路径最大长度", ge=1, le=20),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    learning_path = personal_recommend_service.generate_learning_path(
        user_id=current_user.id,
        db=db,
        max_length=max_length
    )
    return SuccessResponse(
        data=learning_path,
        msg="学习路径生成成功"
    )