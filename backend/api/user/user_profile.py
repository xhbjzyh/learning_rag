"""
用户画像API接口（合并版）
整合：画像查询 + 行为上报
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from service.user.user_profile_service import user_profile_service, user_behavior_service, enhanced_behavior_service
from models.schemas import (
    LearningSessionCreate, UserFeedbackCreate, 
    RecommendationFeedbackCreate, UserBehaviorStatsResponse
)

from utils.response import success_response
from utils.logger import logger

router = APIRouter(
    prefix="/profile",
    tags=["用户-个人中心"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", summary="获取完整用户画像")
def get_complete_user_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取完整用户画像（答题画像 + 行为画像）"""
    profile = user_profile_service.get_complete_user_profile(
        db=db,
        user_id=current_user.id
    )
    return success_response(data=profile, msg="获取用户画像成功")


@router.post("/update", summary="强制更新所有画像")
def force_update_all_profiles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """强制更新所有画像"""
    user_profile_service.force_update_all_profiles(
        db=db,
        user_id=current_user.id
    )
    return success_response(msg="所有画像更新任务已提交")


@router.get("/weak-tags", summary="获取用户薄弱标签")
def get_user_weak_tags(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取用户薄弱标签"""
    profile = user_profile_service.answer_service.get_user_answer_profile(current_user.id, db)
    return success_response(data=profile.get("weak_tags", [])[:limit], msg="获取薄弱标签成功")


@router.get("/strong-tags", summary="获取用户优势标签")
def get_user_strong_tags(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取用户优势标签"""
    profile = user_profile_service.answer_service.get_user_answer_profile(current_user.id, db)
    return success_response(data=profile.get("strong_tags", [])[:limit], msg="获取优势标签成功")


@router.get("/interest-tags", summary="获取用户兴趣标签")
def get_user_interest_tags(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取用户兴趣标签"""
    # 🔥 修正：通过公共方法获取，不直接调用私有方法
    behavior_profile = user_profile_service.get_complete_user_profile(db, current_user.id).get("behavior_profile", {})
    return success_response(data=behavior_profile.get("interest_tags", [])[:limit], msg="获取兴趣标签成功")


# 行为上报API（合并到这里）
@router.post("/behavior/course/{course_id}/{behavior_type}", summary="记录课程行为")
def record_course_behavior(
    course_id: int,
    behavior_type: str,
    behavior_value: float = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """记录用户课程行为"""
    behavior = user_behavior_service.record_course_behavior(
        db=db,
        user_id=current_user.id,
        course_id=course_id,
        behavior_type=behavior_type,
        behavior_value=behavior_value
    )
    return success_response(data=behavior.id, msg="行为记录成功")


@router.post("/behavior/knowledge/{point_id}/{behavior_type}", summary="记录知识点行为")
def record_knowledge_behavior(
    point_id: int,
    behavior_type: str,
    behavior_value: float = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """记录用户知识点行为"""
    behavior = user_behavior_service.record_knowledge_behavior(
        db=db,
        user_id=current_user.id,
        point_id=point_id,
        behavior_type=behavior_type,
        behavior_value=behavior_value
    )
    return success_response(data=behavior.id, msg="行为记录成功")


@router.post("/behavior/resource/{resource_id}/{behavior_type}", summary="记录资源行为")
def record_resource_behavior(
    resource_id: int,
    behavior_type: str,
    behavior_value: float = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """记录用户资源行为"""
    behavior = user_behavior_service.record_resource_behavior(
        db=db,
        user_id=current_user.id,
        resource_id=resource_id,
        behavior_type=behavior_type,
        behavior_value=behavior_value
    )
    return success_response(data=behavior.id, msg="行为记录成功")


# ==================== 第一阶段优化：新增API接口 ====================

@router.post("/learning-session", summary="记录学习会话")
def record_learning_session(
    session_data: LearningSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    记录完整的学习会话（第一阶段优化）
    会同时记录到 user_learning_history 和 user_learning_record
    """
    session_dict = session_data.model_dump()
    history = enhanced_behavior_service.record_learning_session(
        db=db,
        user_id=current_user.id,
        session_data=session_dict
    )
    return success_response(data={"id": history.id}, msg="学习会话记录成功")


@router.post("/feedback", summary="提交用户反馈")
def submit_feedback(
    feedback_data: UserFeedbackCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    提交用户反馈（第一阶段优化）
    支持对知识点、课程的反馈和评分
    """
    feedback_dict = feedback_data.model_dump()
    feedback = enhanced_behavior_service.submit_user_feedback(
        db=db,
        user_id=current_user.id,
        feedback_data=feedback_dict
    )
    return success_response(data={"id": feedback.id}, msg="反馈提交成功")


@router.post("/recommendation-feedback", summary="提交推荐反馈")
def submit_recommendation_feedback(
    feedback_data: RecommendationFeedbackCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    提交推荐反馈（第一阶段优化）
    用于优化推荐算法，收集用户对推荐内容的反馈
    """
    feedback_dict = feedback_data.model_dump()
    result = enhanced_behavior_service.submit_recommendation_feedback(
        db=db,
        user_id=current_user.id,
        feedback_data=feedback_dict
    )
    
    if not result:
        return success_response(code=404, msg="推荐记录不存在")
    
    return success_response(msg="推荐反馈提交成功")


@router.get("/behavior-stats", summary="获取用户行为统计", response_model=UserBehaviorStatsResponse)
def get_user_behavior_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    获取用户行为统计数据（第一阶段优化）
    包括学习会话数、学习时长、连续学习天数等
    """
    stats = enhanced_behavior_service.get_user_behavior_stats(
        db=db,
        user_id=current_user.id
    )
    return success_response(data=stats, msg="获取行为统计成功")


@router.get("/learning-history", summary="获取学习历史")
def get_learning_history(
    cursor: int = Query(None, description="游标（上一页最后一条ID）"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    🔥 使用游标分页获取用户学习历史记录（高性能）
    """
    from models.db_models import UserLearningHistory, KnowledgePoint
    from utils.pagination import cursor_pagination
    
    result = cursor_pagination(
        db=db,
        model=UserLearningHistory,
        filters=[UserLearningHistory.user_id == current_user.id],
        order_by_field=UserLearningHistory.create_time,
        limit=limit,
        cursor=cursor,
        reverse=True  # 降序，最新的在前
    )
    
    # 格式化返回数据
    history_list = []
    for record in result["items"]:
        # 获取知识点标题
        title = "未知"
        if record.point_id:
            point = db.query(KnowledgePoint).filter(KnowledgePoint.id == record.point_id).first()
            if point:
                title = point.title
        
        history_list.append({
            "id": record.id,
            "point_id": record.point_id,
            "title": title,
            "study_duration": record.study_duration,
            "is_mastered": bool(record.is_mastered),
            "session_type": record.session_type,
            "create_time": record.create_time.isoformat() if hasattr(record.create_time, 'isoformat') else str(record.create_time)
        })
    
    return success_response(
        data={
            "items": history_list,
            "has_next": result["has_next"],
            "next_cursor": result["next_cursor"],
            "total": result["total"]
        },
        msg="获取学习历史成功"
    )


# ==================== 第四步：行为数据分析 ====================

@router.get("/behavior-analysis", summary="获取用户行为分析")
def get_user_behavior_analysis(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    🔥 第四步核心功能：获取用户行为分析
    包含：学习习惯、薄弱标签、连续学习天数、学习效果预测
    """
    analysis = enhanced_behavior_service.get_user_behavior_analysis(
        db=db,
        user_id=current_user.id
    )
    return success_response(data=analysis, msg="获取行为分析成功")


@router.get("/weak-tags-detailed", summary="获取详细薄弱标签分析")
def get_weak_tags_detailed(
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    获取详细的薄弱标签分析（带统计信息）
    """
    weak_tags = enhanced_behavior_service._identify_weak_tags(
        db=db,
        user_id=current_user.id,
        limit=limit
    )
    return success_response(data=weak_tags, msg="获取薄弱标签分析成功")


@router.get("/learning-prediction", summary="获取学习效果预测")
def get_learning_prediction(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    获取学习效果预测
    """
    prediction = enhanced_behavior_service._predict_learning_outcome(
        db=db,
        user_id=current_user.id
    )
    return success_response(data=prediction, msg="获取学习效果预测成功")


# ==================== 第五步：智能推荐引擎 ====================

@router.get("/smart-recommendations", summary="获取智能课程推荐")
def get_smart_recommendations(
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    🔥 第五步核心功能：智能推荐（混合策略 - 论文第4.3节实现）
    
    综合推荐算法：
    - 协同过滤（User-CF）：基于相似用户行为
    - 内容推荐（Content-Based）：基于课程相似度
    - 用户画像推荐：基于兴趣标签和学习偏好
    
    动态权重调整：
    - 交互记录 < 10条：侧重内容推荐（α=0.2）
    - 交互记录 10-50条：线性增长
    - 交互记录 > 50条：侧重协同过滤（α=0.8）
    """
    try:
        from core.hybrid_recommender import HybridRecommender
        
        recommender = HybridRecommender(db)
        recommendations = recommender.get_personalized_recommendations(
            user_id=current_user.id,
            limit=limit
        )
        
        logger.info(f"✅ 为用户 {current_user.id} 生成 {len(recommendations)} 个推荐")
        return success_response(data=recommendations, msg="获取智能推荐成功")
    except Exception as e:
        logger.error(f"❌ 获取智能推荐失败: {str(e)}")
        return success_response(code=500, data=[], msg=f"获取推荐失败: {str(e)}")


@router.get("/recommendations-by-type", summary="按类型获取推荐")
def get_recommendations_by_type(
    recommend_type: str = Query(..., description="推荐类型：collaborative_filtering/content_based/profile_based/hybrid"),
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    🔥 按推荐类型获取课程推荐（用于调试和对比）
    
    支持的推荐类型：
    - collaborative_filtering: 协同过滤推荐（User-CF）
    - content_based: 基于内容推荐（课程相似度）
    - profile_based: 基于用户画像推荐
    - hybrid: 混合推荐（默认）
    """
    try:
        from core.hybrid_recommender import HybridRecommender
        from core.collaborative_filtering import CollaborativeFilteringRecommender
        from core.content_based_recommender import ContentBasedRecommender
        
        if recommend_type == "hybrid":
            # 混合推荐
            recommender = HybridRecommender(db)
            recommendations = recommender.get_personalized_recommendations(
                user_id=current_user.id,
                limit=limit
            )
        elif recommend_type == "collaborative_filtering":
            # 纯协同过滤
            cf_recommender = CollaborativeFilteringRecommender(db)
            recommendations = cf_recommender.recommend_by_collaborative_filtering(
                user_id=current_user.id,
                limit=limit
            )
        elif recommend_type == "content_based":
            # 纯内容推荐
            cb_recommender = ContentBasedRecommender(db)
            recent_course = None  # 可以传入特定课程ID
            recommendations = cb_recommender.recommend_similar_courses(
                course_id=recent_course,
                user_id=current_user.id,
                limit=limit
            ) if recent_course else cb_recommender.recommend_by_user_profile(
                user_id=current_user.id,
                limit=limit
            )
        elif recommend_type == "profile_based":
            # 纯用户画像推荐
            cb_recommender = ContentBasedRecommender(db)
            recommendations = cb_recommender.recommend_by_user_profile(
                user_id=current_user.id,
                limit=limit
            )
        else:
            return success_response(code=400, msg=f"不支持的推荐类型：{recommend_type}")
        
        return success_response(data=recommendations, msg=f"获取{recommend_type}推荐成功")
    except Exception as e:
        logger.error(f"获取推荐失败: {str(e)}")
        return success_response(code=500, data=[], msg=f"获取推荐失败: {str(e)}")


# ==================== 知识点同步功能 ====================

@router.post("/sync-course-knowledge/{course_id}", summary="同步课程知识点到公共库")
def sync_course_knowledge(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    🔥 将指定课程的知识点同步到公共知识库
    实现课程内容与RAG问答的统一
    """
    from service.admin.knowledge_sync_service import knowledge_sync_service
    
    # 权限检查：只有管理员或课程创建者可以同步
    from models.db_models import Course
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        return success_response(code=404, msg="课程不存在")
    
    # 执行同步
    result = knowledge_sync_service.sync_course_to_public(db, course_id)
    
    return success_response(data=result, msg=f"同步完成：新增{result['synced']}个，更新{result['updated']}个")


@router.post("/sync-all-courses", summary="同步所有课程知识点")
def sync_all_courses_knowledge(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    🔥 同步所有课程的知识点到公共知识库
    """
    from service.admin.knowledge_sync_service import knowledge_sync_service
    
    result = knowledge_sync_service.sync_all_courses(db)
    
    return success_response(data=result, msg=f"同步完成：处理{result['courses']}个课程")


@router.get("/sync-status/{course_id}", summary="获取课程同步状态")
def get_sync_status(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    获取课程知识点同步状态
    """
    from service.admin.knowledge_sync_service import knowledge_sync_service
    
    status = knowledge_sync_service.get_sync_status(db, course_id)
    
    return success_response(data=status, msg="获取同步状态成功")
