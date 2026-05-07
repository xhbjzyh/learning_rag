from fastapi import APIRouter, Query, Depends, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from utils.logger import logger
from core.rag_engine import rag_engine
from utils.response import success_response, ApiResponse
from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser, KnowledgePoint
from service.user.rag_service import rag_service

# 核心修复：去掉所有前缀！main.py 已经注册了 /api/user/rag
router = APIRouter(tags=["用户-RAG问答"])

# ==============================================
# 原有接口保持不变
# ==============================================
@router.post("/answer", summary="RAG问答(公共/私有切换)", response_model=ApiResponse)
async def rag_answer(
        query: str = Body(..., embed=True),
        kb_type: str = Body("private", embed=True, description="public=公共 private=私有"),
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    try:
        # 调用RAG引擎
        answer = rag_engine.answer(query, current_user.id, kb_type)

        # 个性化推荐
        try:
            from service.user.personal_recommend_service import personal_recommend_service
            recommendations = {
                "knowledge_points": personal_recommend_service.get_related_points(query, current_user.id, db, 3),
                "exercises": personal_recommend_service.get_related_exercises(query, current_user.id, db, 2)
            }
        except:
            recommendations = {}

        return success_response(data={
            "answer": answer,
            "recommendations": recommendations,
            "kb_type": kb_type
        })
    except Exception as e:
        logger.error(f"RAG问答失败: {str(e)}")
        return success_response(code=500, msg="问答失败，请稍后重试")

# ==============================================
# 🔥 终极修复：流式RAG问答接口（保证db传递+学习记录）
# ==============================================
@router.get("/answer/stream", summary="RAG问答(流式输出+上下文记忆+自动记录学习)")
async def rag_answer_stream(
        query: str = Query(..., description="用户问题"),
        kb_type: str = Query("private", description="public=公共 private=私有"),
        clear_history: bool = Query(False, description="是否清除历史对话"),
        db: Session = Depends(get_db),
        current_user: SysUser = Depends(get_current_user)
):
    """
    流式RAG问答接口
    - 支持对话上下文记忆
    - 支持公共/私有知识库切换
    - 自动记录学习行为
    - 流式输出，打字机效果
    """
    # 🔥 核心修复：在接口内定义生成器，保证db不丢失
    async def generate():
        async for chunk in rag_service.chat_stream(
            query=query,
            user_id=current_user.id,
            db=db,
            kb_type=kb_type,
            clear_history=clear_history
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")

# ==============================================
# 清除对话历史接口
# ==============================================
@router.post("/history/clear", summary="清除对话历史", response_model=ApiResponse)
async def clear_conversation_history(
        current_user: SysUser = Depends(get_current_user)
):
    conversation_memory = rag_service.conversation_memory
    conversation_memory.clear_history(current_user.id)
    logger.info(f"用户 {current_user.id} 的对话历史已清除")
    return success_response(msg="对话历史已清除")

# ==============================================
# 其他原有接口保持不变
# ==============================================
@router.get("/search", summary="检索知识点", response_model=ApiResponse)
async def search_knowledge(query: str, top_k: int = 3):
    result = rag_engine.search(query, 0, "public", top_k)
    return success_response(data=result, msg="检索成功")

@router.post("/sync/point/{point_id}", summary="同步知识点", response_model=ApiResponse)
async def sync_single_point(point_id: int, db: Session = Depends(get_db)):
    success = rag_service.sync_point_to_vector(db, point_id)
    return success_response(msg="同步成功") if success else success_response(code=400, msg="失败")

@router.get("/points/list", summary="知识点列表", response_model=ApiResponse)
async def get_all_points(db: Session = Depends(get_db)):
    points = db.query(KnowledgePoint).all()
    return success_response(data=points)