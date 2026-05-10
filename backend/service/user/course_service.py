from sqlalchemy.orm import Session
from models.db_models import (
    Course, CourseResource, UserResourceProgress,
    UserCourseProgress, UserKnowledgeMastery, UserProfile
)
from models.schemas import ResourceProgressUpdate
from fastapi import HTTPException
from datetime import datetime


class UserCourseService:
    """
    用户端课程学习业务逻辑
    """

    def get_course_list(self, db: Session, page: int = 1, size: int = 10,
                       category_id: int = None, difficulty: str = None, title: str = None):
        """
        获取用户可见的课程列表（仅已发布）
        """
        query = db.query(Course).filter(Course.is_published == True, Course.is_public == True)

        # 筛选条件
        if category_id:
            query = query.filter(Course.category_id == category_id)
        if difficulty:
            query = query.filter(Course.difficulty == difficulty)
        if title:
            query = query.filter(Course.title.like(f"%{title}%"))

        # 按观看次数排序
        query = query.order_by(Course.view_count.desc())

        # 分页
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return {
            "total": total,
            "items": items,
            "page": page,
            "size": size
        }

    def get_course_detail(self, db: Session, user_id: int, course_id: int):
        """
        获取课程详情及用户学习进度
        """
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.is_published == True
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="课程不存在或未发布")

        # 增加观看次数
        course.view_count += 1
        db.commit()

        # 获取用户课程进度
        user_progress = db.query(UserCourseProgress).filter(
            UserCourseProgress.user_id == user_id,
            UserCourseProgress.course_id == course_id
        ).first()

        # 获取课程资源
        resources = db.query(CourseResource).filter(
            CourseResource.course_id == course_id,
            CourseResource.is_published == True
        ).order_by(CourseResource.sort_order).all()

        # 补充每个资源的用户进度
        for resource in resources:
            resource.user_progress = db.query(UserResourceProgress).filter(
                UserResourceProgress.user_id == user_id,
                UserResourceProgress.resource_id == resource.id
            ).first()

        return {
            "course": course,
            "user_progress": user_progress,
            "resources": resources
        }

    def get_resource_detail(self, db: Session, user_id: int, resource_id: int):
        """
        获取资源详情及用户学习进度
        """
        resource = db.query(CourseResource).filter(
            CourseResource.id == resource_id,
            CourseResource.is_published == True
        ).first()

        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在或未发布")

        # 获取用户进度
        progress = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.resource_id == resource_id
        ).first()

        if not progress:
            progress = UserResourceProgress(user_id=user_id, resource_id=resource_id)
            db.add(progress)
            db.commit()
            db.refresh(progress)

        return {
            "resource": resource,
            "user_progress": progress
        }

    def update_video_progress(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        更新视频学习进度（用户端调用）
        """
        # 调用管理员端服务的通用方法（避免代码重复）
        from backend.service.admin.course_service import admin_course_service
        return admin_course_service.update_video_progress(db, user_id, resource_id, data)

    def update_document_progress(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        更新文档学习进度（用户端调用）
        """
        from backend.service.admin.course_service import admin_course_service
        return admin_course_service.update_document_progress(db, user_id, resource_id, data)

    def submit_exercise(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        提交习题答案并更新进度（用户端调用）
        """
        from backend.service.admin.course_service import admin_course_service
        return admin_course_service.update_exercise_result(db, user_id, resource_id, data)

    def get_user_learning_progress(self, db: Session, user_id: int):
        """
        获取用户整体学习进度
        """
        # 获取用户所有课程进度
        course_progresses = db.query(UserCourseProgress).filter(
            UserCourseProgress.user_id == user_id
        ).all()

        # 获取用户所有资源进度
        resource_progresses = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id
        ).all()

        # 获取用户知识点掌握情况
        mastery_stats = db.query(
            UserKnowledgeMastery.level,
            db.func.count(UserKnowledgeMastery.id).label("count")
        ).filter(
            UserKnowledgeMastery.user_id == user_id
        ).group_by(UserKnowledgeMastery.level).all()

        # 统计掌握度分布
        mastery_distribution = {
            "未掌握": 0,
            "基本掌握": 0,
            "已掌握": 0
        }
        for level, count in mastery_stats:
            mastery_distribution[level] = count

        return {
            "total_courses": len(course_progresses),
            "finished_courses": sum(1 for p in course_progresses if p.is_finished),
            "total_resources": len(resource_progresses),
            "finished_resources": sum(1 for p in resource_progresses if p.is_finished),
            "mastery_distribution": mastery_distribution,
            "total_study_duration": sum(p.total_study_duration for p in resource_progresses)
        }


# 全局单例
user_course_service = UserCourseService()