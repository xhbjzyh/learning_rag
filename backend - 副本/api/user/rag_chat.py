"""
用户-RAG问答接口
"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from core.rag_engine import rag_engine
from core.llm import llm
from utils.response import success_response, ApiResponse
from db.sqlite_conn import get_db
from models.db_models import KnowledgePoint, KnowledgePointTagRel
from service.user.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["用户-RAG问答"])


@router.get(
    "/search",
    summary="检索知识点",
    description="根据用户问题，检索相关的知识点原文",
    tags=["RAG检索模块"],
    response_model=ApiResponse
)
async def search_knowledge(
        query: str = Query(..., description="用户的检索问题"),
        top_k: int = Query(3, description="返回的相关知识点数量", ge=1, le=10)
):
    result = rag_engine.search(query, top_k=top_k)
    return success_response(
        data=result,
        msg="知识点检索成功"
    )


@router.post(
    "/sync/point/{point_id}",
    summary="同步单个知识点到向量库",
    tags=["RAG检索模块"],
    response_model=ApiResponse
)
async def sync_single_point(
        point_id: int,
        db: Session = Depends(get_db)
):
    success = rag_service.sync_point_to_vector(db, point_id)
    if not success:
        return success_response(code=400, msg="知识点不存在")

    # 自动打标签
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
    db.query(KnowledgePointTagRel).filter(KnowledgePointTagRel.point_id == point_id).delete()
    rel1 = KnowledgePointTagRel(point_id=point_id, tag_id=1)
    rel2 = KnowledgePointTagRel(point_id=point_id, tag_id=2)
    db.add(rel1)
    db.add(rel2)
    db.commit()

    return success_response(msg="知识点同步成功，已自动打上推荐标签")


@router.post(
    "/sync/all",
    summary="全量同步知识点到向量库",
    tags=["RAG检索模块"],
    response_model=ApiResponse
)
async def sync_all_points(
        db: Session = Depends(get_db)
):
    result = rag_service.sync_all_points_to_vector(db)

    # 全量同步时自动打标签
    points = db.query(KnowledgePoint).all()
    for point in points:
        db.query(KnowledgePointTagRel).filter(KnowledgePointTagRel.point_id == point.id).delete()
        rel1 = KnowledgePointTagRel(point_id=point.id, tag_id=1)
        rel2 = KnowledgePointTagRel(point_id=point.id, tag_id=2)
        db.add(rel1)
        db.add(rel2)
    db.commit()

    return success_response(msg=f"全量同步成功，共同步{result['total']}个知识点，已自动打上推荐标签")


@router.post(
    "/answer",
    summary="RAG问答",
    description="根据用户问题，检索知识点并生成AI回答",
    tags=["RAG问答模块"],
    response_model=ApiResponse
)
async def rag_answer(
        query: str = Query(..., description="用户的问题")
):
    search_result = rag_engine.search(query, top_k=3)
    context_text = "\n".join([f"- {item['content']}" for item in search_result])

    system_prompt = f"""
    你是一位专业的学习助手，请根据以下知识点回答问题。
    规则：
    1. 只使用提供的知识点回答
    2. 回答专业、有条理、有深度
    3. 分点作答更清晰
    4. 不编造内容

    参考知识点：
    {context_text}
    """

    final_answer = llm.chat(
        user_prompt=query,
        system_prompt=system_prompt
    )

    return success_response(
        data={
            "query": query,
            "answer": final_answer
        },
        msg="问答生成成功"
    )


@router.get(
    "/points/list",
    summary="获取所有知识点列表",
    tags=["RAG检索模块"],
    response_model=ApiResponse
)
async def get_all_points(
        db: Session = Depends(get_db)
):
    points = db.query(KnowledgePoint).all()
    result = []
    for point in points:
        result.append({
            "id": point.id,
            "title": point.title,
            "content": point.content[:100] + "..." if len(point.content) > 100 else point.content,
            "created_at": point.create_time.strftime("%Y-%m-%d %H:%M:%S") if point.create_time else ""
        })
    return success_response(
        data=result,
        msg="获取知识点列表成功"
    )