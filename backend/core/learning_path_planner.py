
"""
学习路径规划引擎
基于DAG（有向无环图）的知识点依赖关系和拓扑排序算法

论文第4.4节实现：
1. 构建知识点依赖关系DAG
2. 执行拓扑排序获取学习顺序
3. 个性化剪枝（移除已掌握节点）
4. 最短路径搜索
"""
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque
from sqlalchemy.orm import Session
import json

from models.db_models import KnowledgePoint, UserKnowledgeMastery, LearningProgress
from utils.logger import logger


class LearningPathPlanner:
    """学习路径规划器（基于DAG + 拓扑排序）"""

    def __init__(self, db: Session):
        self.db = db
        self.graph = defaultdict(list)  # 邻接表：节点 -> [后继节点]
        self.in_degree = defaultdict(int)  # 入度表
        self.nodes = set()  # 所有节点

        logger.info("✅ 学习路径规划器初始化完成")

    def build_dag(self, knowledge_points: List[KnowledgePoint]):
        """
        构建知识点依赖关系DAG（有向无环图）

        Args:
            knowledge_points: 知识点列表
        """
        # 清空图数据
        self.graph.clear()
        self.in_degree.clear()
        self.nodes.clear()

        # 添加所有节点
        for point in knowledge_points:
            self.nodes.add(point.id)
            if point.id not in self.in_degree:
                self.in_degree[point.id] = 0

        # 构建依赖关系边
        for point in knowledge_points:
            # 解析前置知识点
            if point.key_points:
                try:
                    key_points_data = json.loads(point.key_points)
                    prerequisites = key_points_data.get('prerequisites', [])

                    for prereq_id in prerequisites:
                        if prereq_id in self.nodes:
                            # 添加边：prereq_id -> point.id
                            self.graph[prereq_id].append(point.id)
                            self.in_degree[point.id] += 1

                            logger.debug(f"  添加依赖边: {prereq_id} -> {point.id}")
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"⚠️ 知识点 {point.id} 的key_points格式错误")

        logger.info(f"📊 DAG构建完成: {len(self.nodes)}个节点, {sum(len(v) for v in self.graph.values())}条边")

    def topological_sort(self) -> List[int]:
        """
        执行拓扑排序（Kahn算法）

        Returns:
            拓扑排序后的节点ID列表
        """
        # 复制入度表（避免修改原数据）
        in_degree_copy = dict(self.in_degree)

        # 找到所有入度为0的节点（起点）
        queue = deque([node for node in self.nodes if in_degree_copy[node] == 0])

        sorted_order = []

        while queue:
            node = queue.popleft()
            sorted_order.append(node)

            # 处理后继节点
            for successor in self.graph[node]:
                in_degree_copy[successor] -= 1
                if in_degree_copy[successor] == 0:
                    queue.append(successor)

        # 检查是否有环
        if len(sorted_order) != len(self.nodes):
            logger.warning("⚠️ 检测到图中存在环，拓扑排序可能不完整")

        logger.info(f"📐 拓扑排序完成: {len(sorted_order)}个节点")

        return sorted_order

    def prune_mastered_nodes(self, user_id: int, threshold: float = 70.0) -> List[int]:
        """
        个性化剪枝：移除用户已掌握的节点

        Args:
            user_id: 用户ID
            threshold: 掌握度阈值（默认70分）

        Returns:
            剪枝后的学习路径
        """
        # 查询用户已掌握的知识点
        mastered_points = self.db.query(UserKnowledgeMastery.knowledge_point_id).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.mastery_score >= threshold
        ).all()

        mastered_ids = set([mp[0] for mp in mastered_points])

        logger.info(f"✂️ 个性化剪枝: 用户{user_id}已掌握{len(mastered_ids)}个知识点（≥{threshold}分）")

        # 执行拓扑排序
        full_path = self.topological_sort()

        # 移除已掌握的节点
        pruned_path = [pid for pid in full_path if pid not in mastered_ids]

        logger.info(f"📍 剪枝后路径: {len(full_path)} → {len(pruned_path)}个节点")

        return pruned_path

    def find_shortest_path(
            self,
            start_id: int,
            target_id: int,
            user_id: Optional[int] = None
    ) -> List[int]:
        """
        寻找从起点到目标点的最短路径（BFS算法）

        Args:
            start_id: 起点知识点ID
            target_id: 目标知识点ID
            user_id: 用户ID（可选，用于个性化剪枝）

        Returns:
            最短路径上的节点ID列表
        """
        if start_id not in self.nodes or target_id not in self.nodes:
            logger.error(f"❌ 起点或目标点不在图中")
            return []

        # BFS搜索
        queue = deque([(start_id, [start_id])])
        visited = {start_id}

        while queue:
            current_node, path = queue.popleft()

            if current_node == target_id:
                logger.info(f"🎯 找到最短路径: {start_id} → {target_id}, 长度={len(path)}")
                return path

            for neighbor in self.graph[current_node]:
                if neighbor not in visited:
                    # 如果提供了user_id，跳过已掌握的节点
                    if user_id:
                        mastery = self.db.query(UserKnowledgeMastery).filter(
                            UserKnowledgeMastery.user_id == user_id,
                            UserKnowledgeMastery.knowledge_point_id == neighbor
                        ).first()

                        if mastery and mastery.mastery_score >= 70:
                            continue  # 跳过已掌握节点

                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        logger.warning(f"⚠️ 未找到从 {start_id} 到 {target_id} 的路径")
        return []

    def generate_learning_path(
            self,
            user_id: int,
            target_point_id: Optional[int] = None,
            max_length: int = 20
    ) -> List[Dict]:
        """
        生成完整的学习路径

        Args:
            user_id: 用户ID
            target_point_id: 目标知识点ID（可选，不指定则学习所有未掌握知识点）
            max_length: 最大路径长度

        Returns:
            学习路径列表，每个元素包含知识点详细信息
        """
        # 1. 获取所有相关知识点
        if target_point_id:
            # 获取目标点及其所有前置知识点
            all_point_ids = self._get_all_prerequisites(target_point_id)
            knowledge_points = self.db.query(KnowledgePoint).filter(
                KnowledgePoint.id.in_(all_point_ids)
            ).all()
        else:
            # 获取所有知识点
            knowledge_points = self.db.query(KnowledgePoint).filter(
                KnowledgePoint.is_published == True
            ).all()

        # 2. 构建DAG
        self.build_dag(knowledge_points)

        # 3. 个性化剪枝
        learning_path_ids = self.prune_mastered_nodes(user_id)

        # 4. 如果指定了目标点，寻找最短路径
        if target_point_id:
            if target_point_id in learning_path_ids:
                shortest_path = self.find_shortest_path(
                    learning_path_ids[0],
                    target_point_id,
                    user_id
                )
                learning_path_ids = shortest_path

        # 5. 限制路径长度
        learning_path_ids = learning_path_ids[:max_length]

        # 6. 获取详细信息
        learning_path = []
        for i, point_id in enumerate(learning_path_ids):
            point = self.db.query(KnowledgePoint).filter(
                KnowledgePoint.id == point_id
            ).first()

            if point:
                # 获取用户当前掌握度
                mastery = self.db.query(UserKnowledgeMastery).filter(
                    UserKnowledgeMastery.user_id == user_id,
                    UserKnowledgeMastery.knowledge_point_id == point_id
                ).first()

                mastery_score = mastery.mastery_score if mastery else 0

                learning_path.append({
                    'order': i + 1,
                    'point_id': point.id,
                    'title': point.title,
                    'difficulty': point.difficulty,
                    'mastery_score': mastery_score,
                    'estimated_duration': len(point.content) // 100 + 1,  # 预估学习时长（分钟）
                    'reason': f'第{i + 1}步学习内容' if i == 0 else f'前置知识完成后学习'
                })

        logger.info(f"✅ 为用户{user_id}生成学习路径: {len(learning_path)}个知识点")

        return learning_path

    def _get_all_prerequisites(self, point_id: int) -> Set[int]:
        """
        递归获取所有前置知识点

        Args:
            point_id: 知识点ID

        Returns:
            所有前置知识点ID集合（包含自身）
        """
        prerequisites = {point_id}

        point = self.db.query(KnowledgePoint).filter(
            KnowledgePoint.id == point_id
        ).first()

        if point and point.key_points:
            try:
                key_points_data = json.loads(point.key_points)
                prereq_ids = key_points_data.get('prerequisites', [])

                for prereq_id in prereq_ids:
                    prerequisites.update(self._get_all_prerequisites(prereq_id))
            except (json.JSONDecodeError, TypeError):
                pass

        return prerequisites


# 全局单例工厂函数
def get_learning_path_planner(db: Session) -> LearningPathPlanner:
    """获取学习路径规划器实例"""
    return LearningPathPlanner(db)
