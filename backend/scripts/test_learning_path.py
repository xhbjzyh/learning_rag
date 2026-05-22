
"""
学习路径规划测试脚本
验证DAG构建、拓扑排序、个性化剪枝、最短路径搜索功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from db.sqlite_conn import SessionLocal
from core.learning_path_planner import LearningPathPlanner
from models.db_models import KnowledgePoint


def test_learning_path_planner():
    """测试学习路径规划器"""
    print("=" * 80)
    print("🧪 学习路径规划器测试")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # 1. 准备测试数据
        print("\n📝 步骤1：准备测试知识点数据")
        print("-" * 80)

        # 创建测试知识点（模拟依赖关系）
        test_points_data = [
            {'id': 101, 'title': 'Python基础', 'content': '变量、数据类型、控制流', 'prerequisites': []},
            {'id': 102, 'title': '函数', 'content': '函数定义、参数传递、返回值', 'prerequisites': [101]},
            {'id': 103, 'title': '面向对象编程', 'content': '类、对象、继承、多态', 'prerequisites': [102]},
            {'id': 104, 'title': '数据结构', 'content': '列表、字典、集合、元组', 'prerequisites': [101]},
            {'id': 105, 'title': '算法基础', 'content': '排序、查找、递归', 'prerequisites': [101, 104]}
        ]

        # 检查数据库中是否已有这些数据
        existing_ids = [p['id'] for p in test_points_data]
        existing_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.id.in_(existing_ids)
        ).all()

        if len(existing_points) < len(test_points_data):
            print("⚠️ 数据库中缺少测试数据，请先运行以下SQL插入测试知识点：")
            print("""
                  -- 插入测试知识点
                  INSERT INTO knowledge_point (id, title, content, key_points, difficulty, is_published)
                  VALUES (101, 'Python基础', '变量、数据类型、控制流', '{"prerequisites": []}', '简单', 1),
                         (102, '函数', '函数定义、参数传递、返回值', '{"prerequisites": [101]}', '中等', 1),
                         (103, '面向对象编程', '类、对象、继承、多态', '{"prerequisites": [102]}', '困难', 1),
                         (104, '数据结构', '列表、字典、集合、元组', '{"prerequisites": [101]}', '中等', 1),
                         (105, '算法基础', '排序、查找、递归', '{"prerequisites": [101, 104]}', '困难', 1);
                  """)
            return

        # 获取知识点
        knowledge_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.id.in_(existing_ids)
        ).all()

        print(f"✅ 加载了 {len(knowledge_points)} 个知识点")
        for point in knowledge_points:
            print(f"   - ID={point.id}: {point.title}")

        # 2. 构建DAG
        print("\n\n📊 步骤2：构建知识点依赖DAG")
        print("-" * 80)

        planner = LearningPathPlanner(db)
        planner.build_dag(knowledge_points)

        print(f"✅ DAG构建完成: {len(planner.nodes)}个节点")
        print(f"   边数: {sum(len(v) for v in planner.graph.values())}")

        # 3. 拓扑排序
        print("\n\n📐 步骤3：执行拓扑排序")
        print("-" * 80)

        sorted_order = planner.topological_sort()
        print(f"✅ 拓扑排序结果:")
        for i, point_id in enumerate(sorted_order, 1):
            point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
            print(f"   {i}. ID={point_id}: {point.title}")

        # 4. 个性化剪枝（模拟用户已掌握某些知识点）
        print("\n\n✂️ 步骤4：个性化剪枝测试")
        print("-" * 80)

        test_user_id = 1
        pruned_path = planner.prune_mastered_nodes(test_user_id, threshold=70.0)
        print(f"✅ 剪枝后路径: {len(pruned_path)}个节点")

        # 5. 最短路径搜索
        print("\n\n🎯 步骤5：最短路径搜索")
        print("-" * 80)

        if 101 in planner.nodes and 105 in planner.nodes:
            shortest = planner.find_shortest_path(101, 105)
            print(f"✅ 从 Python基础(101) 到 算法基础(105) 的最短路径:")
            for i, point_id in enumerate(shortest, 1):
                point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
                print(f"   {i}. {point.title}")

        print("\n" + "=" * 80)
        print("✅ 学习路径规划器测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_learning_path_planner()
