"""
学习路径规划完整测试脚本
使用现有数据库数据进行测试，不会删除或修改任何数据

论文第4.4节实现验证
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from db.sqlite_conn import SessionLocal
from models.db_models import KnowledgePoint
import json


def check_existing_data():
    """检查现有数据并统计"""
    print("=" * 80)
    print("📊 步骤1：检查现有知识点数据")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # 统计总知识点数
        total_count = db.query(KnowledgePoint).filter(
            KnowledgePoint.is_published == True
        ).count()

        # 获取前5个知识点示例
        sample_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.is_published == True
        ).limit(5).all()

        print(f"\n✅ 数据库中共有 {total_count} 个已发布知识点")

        if sample_points:
            print("\n📋 前5个知识点示例：")
            for point in sample_points:
                has_prereqs = "有依赖" if point.key_points and 'prerequisites' in point.key_points else "无依赖"
                print(f"   - ID={point.id}: {point.title[:30]} ({point.difficulty}) [{has_prereqs}]")

        print("\n" + "=" * 80)

        if total_count == 0:
            print("⚠️ 数据库中没有知识点，建议先上传一些文档")
            return False

        return True

    except Exception as e:
        print(f"\n❌ 数据检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_learning_path_algorithm():
    """测试学习路径算法（使用现有数据）"""
    print("\n\n" + "=" * 80)
    print("🧪 步骤2：测试学习路径核心算法")
    print("=" * 80)

    from core.learning_path_planner import LearningPathPlanner

    db: Session = SessionLocal()

    try:
        # 获取所有已发布的知识点
        knowledge_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.is_published == True
        ).all()

        if len(knowledge_points) < 2:
            print(f"⚠️ 数据库中只有{len(knowledge_points)}个知识点，建议至少5个")
            print("💡 提示：可以通过上传文档来创建知识点")
            return False

        print(f"\n✅ 加载了 {len(knowledge_points)} 个知识点")

        # 构建DAG
        print("\n📊 构建知识点依赖DAG...")
        planner = LearningPathPlanner(db)
        planner.build_dag(knowledge_points)

        node_count = len(planner.nodes)
        edge_count = sum(len(v) for v in planner.graph.values())

        print(f"✅ DAG构建完成: {node_count}个节点, {edge_count}条边")

        if edge_count == 0:
            print("\n⚠️ 检测到没有依赖关系")
            print("💡 提示：可以在知识点的 key_points 字段中添加 prerequisites 数组")
            print("   例如：{\"prerequisites\": [1, 2], \"key_concepts\": [...]}")

        # 拓扑排序
        print("\n📐 执行拓扑排序...")
        sorted_order = planner.topological_sort()

        print(f"✅ 拓扑排序结果（前10个）:")
        for i, point_id in enumerate(sorted_order[:10], 1):
            point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
            if point:
                print(f"   {i}. {point.title[:40]} (ID={point_id})")

        if len(sorted_order) > 10:
            print(f"   ... 还有 {len(sorted_order) - 10} 个知识点")

        # 最短路径搜索（如果有依赖关系）
        if edge_count > 0:
            print("\n🎯 测试最短路径搜索...")

            # 找到第一个有依赖的知识点作为目标
            target_point = None
            for point in knowledge_points:
                if point.key_points:
                    try:
                        kp_data = json.loads(point.key_points)
                        prereqs = kp_data.get('prerequisites', [])
                        if prereqs:
                            target_point = point
                            start_id = prereqs[0]
                            break
                    except:
                        pass

            if target_point:
                shortest = planner.find_shortest_path(start_id, target_point.id)

                if shortest:
                    print(f"✅ 最短路径示例:")
                    for i, point_id in enumerate(shortest, 1):
                        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
                        if point:
                            print(f"   {i}. {point.title}")
        else:
            print("\n⚠️ 跳过最短路径测试（没有依赖关系）")

        print("\n" + "=" * 80)
        print("✅ 算法测试完成！")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ 算法测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """主测试流程"""
    print("\n" + "=" * 80)
    print("🚀 学习路径规划完整测试（使用现有数据）")
    print("=" * 80)
    print("\n说明：本测试不会删除或修改任何数据库内容")
    print("=" * 80)

    # 1. 检查现有数据
    has_data = check_existing_data()

    if not has_data:
        print("\n❌ 测试中止：数据库中没有足够的知识点")
        print("💡 建议：先通过上传文档创建知识点")
        return

    # 2. 测试算法
    success = test_learning_path_algorithm()

    if success:
        print("\n\n" + "=" * 80)
        print("🎉 测试完成！")
        print("=" * 80)
        print("\n下一步操作：")
        print("1. 启动后端服务: python main.py")
        print("2. 访问Swagger文档: http://localhost:8000/docs")
        print("3. 测试API接口:")
        print("   - GET /api/user/learning-path/generate")
        print("   - GET /api/user/learning-path/shortest-path?start_point_id=xxx&end_point_id=yyy")
        print("   - GET /api/user/learning-path/dag-info")
        print("=" * 80)
    else:
        print("\n\n⚠️ 测试未完成，请检查上述错误信息")


if __name__ == "__main__":
    main()
