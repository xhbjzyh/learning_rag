
"""
学习路径规划API接口
基于DAG和拓扑排序的个性化学习路径生成

论文第4.4节实现
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from core.learning_path_planner import get_learning_path_planner
from utils.response import success_response

router = APIRouter(
    prefix="/learning-path",
    tags=["用户-学习路径"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/generate", summary="生成个性化学习路径")
def generate_learning_path(
        target_point_id: int = Query(None, description="目标知识点ID（可选）"),
        max_length: int = Query(20, ge=1, le=50, description="最大路径长度"),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    🔥 生成个性化学习路径（论文第4.4节）

    算法流程：
    1. 构建知识点依赖关系DAG
    2. 执行拓扑排序获取学习顺序
    3. 个性化剪枝（移除已掌握节点）
    4. 最短路径搜索（如果指定了目标点）

    Args:
        target_point_id: 目标知识点ID，不指定则学习所有未掌握知识点
        max_length: 最大路径长度（1-50）

    Returns:
        学习路径列表，按学习顺序排列
    """
    try:
        # 创建学习路径规划器
        planner = get_learning_path_planner(db)

        # 生成学习路径
        learning_path = planner.generate_learning_path(
            user_id=current_user.id,
            target_point_id=target_point_id,
            max_length=max_length
        )

        return success_response(
            data={
                'path': learning_path,
                'total_points': len(learning_path),
                'target_point_id': target_point_id,
                'user_id': current_user.id
            },
            msg="学习路径生成成功"
        )
    except Exception as e:
        return success_response(
            code=500,
            data=[],
            msg=f"学习路径生成失败: {str(e)}"
        )


@router.get("/shortest-path", summary="查找两点间最短路径")
def find_shortest_path(
        start_point_id: int = Query(..., description="起点知识点ID"),
        end_point_id: int = Query(..., description="终点知识点ID"),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    查找从起点到终点的最短学习路径

    Args:
        start_point_id: 起点知识点ID
        end_point_id: 终点知识点ID

    Returns:
        最短路径上的知识点列表
    """
    try:
        from models.db_models import KnowledgePoint

        # 验证知识点是否存在
        start_point = db.query(KnowledgePoint).filter(
            KnowledgePoint.id == start_point_id
        ).first()

        end_point = db.query(KnowledgePoint).filter(
            KnowledgePoint.id == end_point_id
        ).first()

        if not start_point or not end_point:
            return success_response(code=404, data=[], msg="知识点不存在")

        # 创建规划器并查找最短路径
        planner = get_learning_path_planner(db)

        # 获取所有相关知识点构建DAG
        all_prereqs = planner._get_all_prerequisites(end_point_id)
        knowledge_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.id.in_(all_prereqs)
        ).all()

        planner.build_dag(knowledge_points)

        shortest_path = planner.find_shortest_path(
            start_point_id,
            end_point_id,
            current_user.id
        )

        # 获取详细信息
        path_details = []
        for i, point_id in enumerate(shortest_path):
            point = db.query(KnowledgePoint).filter(
                KnowledgePoint.id == point_id
            ).first()

            if point:
                path_details.append({
                    'order': i + 1,
                    'point_id': point.id,
                    'title': point.title,
                    'difficulty': point.difficulty
                })

        return success_response(
            data={
                'path': path_details,
                'start': start_point_id,
                'end': end_point_id,
                'length': len(path_details)
            },
            msg="最短路径查找成功"
        )
    except Exception as e:
        return success_response(
            code=500,
            data=[],
            msg=f"最短路径查找失败: {str(e)}"
        )


@router.get("/dag-info", summary="获取DAG图信息")
def get_dag_info(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    获取知识点依赖DAG图的统计信息

    Returns:
        DAG图的节点数、边数等统计信息
    """
    try:
        from models.db_models import KnowledgePoint

        # 获取所有已发布的知识点
        knowledge_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.is_published == True
        ).all()

        # 创建规划器并构建DAG
        planner = get_learning_path_planner(db)
        planner.build_dag(knowledge_points)

        # 统计信息
        node_count = len(planner.nodes)
        edge_count = sum(len(v) for v in planner.graph.values())

        # 找出入度为0的节点（起点）
        start_nodes = [nid for nid in planner.nodes if planner.in_degree[nid] == 0]

        # 找出出度为0的节点（终点）
        end_nodes = [nid for nid in planner.nodes if nid not in planner.graph or len(planner.graph[nid]) == 0]

        return success_response(
            data={
                'node_count': node_count,
                'edge_count': edge_count,
                'start_nodes': start_nodes[:10],  # 最多返回10个
                'end_nodes': end_nodes[:10],
                'avg_edges_per_node': round(edge_count / node_count, 2) if node_count > 0 else 0
            },
            msg="DAG图信息获取成功"
        )
    except Exception as e:
        return success_response(
            code=500,
            data={},
            msg=f"DAG图信息获取失败: {str(e)}"
        )
