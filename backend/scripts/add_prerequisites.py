
"""
为现有知识点添加依赖关系
不会删除任何数据，只更新key_points字段
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


def add_prerequisites_to_existing_data():
    """为现有背包问题知识点添加合理的依赖关系"""
    print("=" * 80)
    print("🔧 为现有知识点添加依赖关系")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # 获取所有背包问题知识点
        knowledge_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.is_published == True
        ).all()

        print(f"\n📊 找到 {len(knowledge_points)} 个知识点")

        # 定义合理的依赖关系（基于背包问题的学习顺序）
        dependency_map = {
            1: {'title': '01背包问题', 'prerequisites': [], 'concepts': ['动态规划', '状态转移']},
            2: {'title': '完全背包问题', 'prerequisites': [1], 'concepts': ['无限物品', '优化技巧']},
            3: {'title': '多重背包问题', 'prerequisites': [1], 'concepts': ['二进制优化', '单调队列']},
            4: {'title': '混合背包问题', 'prerequisites': [1, 2, 3], 'concepts': ['分类讨论']},
            5: {'title': '二维费用背包', 'prerequisites': [1], 'concepts': ['多维约束']},
            6: {'title': '分组背包问题', 'prerequisites': [1], 'concepts': ['每组选一个']},
            7: {'title': '有依赖的背包', 'prerequisites': [1, 6], 'concepts': ['树形DP', '依赖关系']}
        }

        updated_count = 0

        for point in knowledge_points:
            if point.id in dependency_map:
                dep_info = dependency_map[point.id]

                # 构建新的key_points
                new_key_points = {
                    'prerequisites': dep_info['prerequisites'],
                    'key_concepts': dep_info['concepts']
                }

                # 更新数据库
                point.key_points = json.dumps(new_key_points, ensure_ascii=False)
                updated_count += 1

                prereq_str = f"依赖: {dep_info['prerequisites']}" if dep_info['prerequisites'] else "无依赖"
                print(f"✅ 更新 {point.title}: {prereq_str}")

        db.commit()

        print("\n" + "=" * 80)
        print(f"✅ 成功更新 {updated_count} 个知识点的依赖关系")
        print("=" * 80)

        # 验证更新结果
        print("\n🔍 验证更新结果：")
        print("-" * 80)

        all_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.is_published == True
        ).all()

        for point in all_points:
            if point.key_points:
                try:
                    kp_data = json.loads(point.key_points)
                    prereqs = kp_data.get('prerequisites', [])
                    print(f"   {point.id}. {point.title[:20]} - 依赖: {prereqs}")
                except:
                    print(f"   {point.id}. {point.title[:20]} - 格式错误")

    except Exception as e:
        print(f"\n❌ 更新失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    add_prerequisites_to_existing_data()
