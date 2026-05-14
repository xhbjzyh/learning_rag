
"""
检查并修复课程知识点同步
运行方式：python scripts/check_and_sync_knowledge.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.sqlite_conn import SessionLocal
from models.db_models import CourseKnowledgePoint, KnowledgePoint
from service.admin.knowledge_sync_service import knowledge_sync_service
from service.user.rag_service import rag_service


def check_and_sync():
    """检查并同步所有课程的知识点"""
    print("🔍 开始检查课程知识点同步状态...")

    db = SessionLocal()
    try:
        # 1. 统计课程知识点数量
        course_kps_count = db.query(CourseKnowledgePoint).count()
        print(f"\n📊 课程知识点总数: {course_kps_count}")

        # 2. 统计已同步到公共知识库的数量
        synced_kps = db.query(KnowledgePoint).filter(
            KnowledgePoint.source_type == "course"
        ).all()
        print(f"✅ 已同步到公共知识库: {len(synced_kps)}")

        if len(synced_kps) > 0:
            print("\n📋 已同步的知识点列表:")
            for kp in synced_kps[:10]:  # 只显示前10个
                print(f"  - ID={kp.id}, 标题={kp.title[:30]}, source_id={kp.source_id}")

        # 3. 如果未同步，执行同步
        if course_kps_count > 0 and len(synced_kps) == 0:
            print("\n⚠️ 检测到课程知识点未同步，开始同步...")

            from models.db_models import Course
            courses = db.query(Course).all()

            for course in courses:
                print(f"\n🔄 同步课程: {course.title} (ID={course.id})")
                result = knowledge_sync_service.sync_course_to_public(db, course.id)
                print(f"   结果: {result}")

        # 4. 检查向量库状态
        print("\n\n🔍 检查向量库状态...")
        from utils.vector_store import get_global_vector_store

        global_vs = get_global_vector_store()
        print(f"📦 全局向量库 (user_0) 中的向量数量: {global_vs.index.ntotal if global_vs.index else 0}")
        print(f"📦 文档映射数量: {len(global_vs.doc_map)}")

        # 5. 如果向量库为空，重新同步所有知识点
        if global_vs.index.ntotal == 0 and len(synced_kps) > 0:
            print("\n⚠️ 向量库为空，开始同步所有知识点到向量库...")

            success_count = 0
            for kp in synced_kps:
                try:
                    success = rag_service.sync_point_to_vector(db, kp.id)
                    if success:
                        success_count += 1
                        print(f"  ✅ 同步成功: {kp.title[:30]}")
                    else:
                        print(f"  ❌ 同步失败: {kp.title[:30]}")
                except Exception as e:
                    print(f"  ❌ 同步异常: {kp.title[:30]}, 错误: {e}")

            print(f"\n🎉 向量库同步完成！成功: {success_count}/{len(synced_kps)}")

            # 再次检查向量库
            print(f"📦 同步后向量库中的向量数量: {global_vs.index.ntotal}")

        print("\n✅ 检查和同步完成！")

    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_and_sync()
