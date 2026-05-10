from sqlalchemy.orm import Session
from models.db_models import (
    Course, CourseResource, UserResourceProgress,
    UserKnowledgeMastery, UserProfile, KnowledgePoint,
    KnowledgeQaRecord,
)
from models.schemas import (
    AdminCourseCreateRequest, AdminCourseUpdateRequest,
    CourseResourceCreate, CourseResourceUpdate, ResourceProgressUpdate,
    KnowledgeQaCreate, KnowledgeQaFeedbackUpdate,CourseResourceFileUpload
)
from fastapi import HTTPException
from datetime import datetime
import json
# 1. 文件工具导入（修复缺失依赖）
from utils.file_utils import save_upload_file, get_file_path
import os
from uuid import uuid4
from fastapi import UploadFile


class AdminCourseService:
    """
    管理员课程管理业务逻辑
    """

    # ==================== 原有课程管理方法（完全保留） ====================
    def get_course_list(self, db: Session, page: int = 1, size: int = 10, title: str = None):
        """
        获取课程列表（分页 + 搜索）
        """
        query = db.query(Course)

        # 按课程标题搜索
        if title:
            query = query.filter(Course.title.like(f"%{title}%"))

        # 分页计算
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return {
            "total": total,
            "items": items,
            "page": page,
            "size": size
        }

    def create_course(self, db: Session, data: AdminCourseCreateRequest):
        """
        创建课程（校验重名）
        """
        # 校验课程名称是否重复
        exist_course = db.query(Course).filter(Course.title == data.title).first()
        if exist_course:
            raise HTTPException(status_code=400, detail="课程标题已存在")

        # 创建课程对象
        course = Course(**data.model_dump())
        db.add(course)
        db.commit()
        db.refresh(course)

        return course

    def update_course(self, db: Session, course_id: int, data: AdminCourseUpdateRequest):
        """
        更新课程
        """
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 只更新传入的字段
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)

        db.commit()
        db.refresh(course)
        return course

    def delete_course(self, db: Session, course_id: int):
        """
        删除课程
        """
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        db.delete(course)
        db.commit()
        return True

    # ==================== 🔥 新增：课程资料CRUD方法 ====================
    def get_course_resources(self, db: Session, course_id: int, resource_type: str = None):
        """
        获取课程所有资料（支持按类型筛选）
        """
        # 校验课程是否存在
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 查询资料
        query = db.query(CourseResource).filter(CourseResource.course_id == course_id)
        if resource_type:
            query = query.filter(CourseResource.type == resource_type)

        # 按排序字段升序排列
        resources = query.order_by(CourseResource.sort_order).all()

        # 补充关联的知识点ID列表
        for resource in resources:
            resource.knowledge_ids = [kp.id for kp in resource.knowledge_points]

        return resources

    # 🔥 只替换这个方法，其余代码不动！
    def create_resource(self, db: Session, course_id: int, data: CourseResourceCreate):
        """
        创建课程资料并关联知识点
        """
        # 校验课程是否存在
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 创建资料主记录
        resource_data = data.model_dump(exclude={"knowledge_ids", "video", "document", "exercise"})

        # ==================== 🔥 终极自动填充（解决所有NULL/非空报错） ====================
        # 1. 强制填充URL（解决数据库非空约束）
        if not resource_data.get("url"):
            resource_data["url"] = "/static/resources/default.pdf"
        # 2. 自动填充文件类型
        if not resource_data.get("file_type"):
            if "." in resource_data["url"]:
                resource_data["file_type"] = resource_data["url"].split(".")[-1].lower()
            else:
                resource_data["file_type"] = "pdf"
        # 3. 自动填充文件大小（默认0）
        if not resource_data.get("file_size"):
            resource_data["file_size"] = 0
        # 4. 自动填充时长（默认0）
        if not resource_data.get("duration"):
            resource_data["duration"] = 0

        db_resource = CourseResource(course_id=course_id, **resource_data)
        db.add(db_resource)
        db.flush()  # 获取resource_id

        # 关联知识点
        if data.knowledge_ids:
            knowledges = db.query(KnowledgePoint).filter(
                KnowledgePoint.id.in_(data.knowledge_ids)
            ).all()
            db_resource.knowledge_points = knowledges

        db.commit()
        db.refresh(db_resource)

        # 补充知识点ID列表
        db_resource.knowledge_ids = [kp.id for kp in db_resource.knowledge_points]
        return db_resource

    def update_resource(self, db: Session, resource_id: int, data: CourseResourceUpdate):
        """
        更新课程资料及关联知识点
        """
        # 校验资源是否存在
        db_resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
        if not db_resource:
            raise HTTPException(status_code=404, detail="课程资料不存在")

        # 更新主表字段
        update_data = data.model_dump(exclude_unset=True, exclude={"knowledge_ids"})
        for key, value in update_data.items():
            setattr(db_resource, key, value)

        # 更新知识点关联
        if data.knowledge_ids is not None:
            knowledges = db.query(KnowledgePoint).filter(
                KnowledgePoint.id.in_(data.knowledge_ids)
            ).all()
            db_resource.knowledge_points = knowledges

        db.commit()
        db.refresh(db_resource)

        # 补充知识点ID列表
        db_resource.knowledge_ids = [kp.id for kp in db_resource.knowledge_points]
        return db_resource

    def delete_resource(self, db: Session, resource_id: int):
        """
        删除课程资料（级联删除学习进度记录）
        """
        db_resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
        if not db_resource:
            raise HTTPException(status_code=404, detail="课程资料不存在")

        db.delete(db_resource)
        db.commit()
        return True

    # ==================== 🔥 核心修复：文件上传方法（放入类内！） ====================
    def create_resource_with_file(self, db: Session, course_id: int, data, file: UploadFile):
        """
        上传文件并创建课程资源（解决后端缺失方法报错）
        自动生成URL，彻底解决数据库非空约束问题
        """
        # 校验课程
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 1. 创建文件保存目录
        upload_dir = f"static/resources/{course_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # 2. 生成唯一文件名
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
        file_name = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)

        # 3. 保存文件
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # 4. 写入数据库（自动填充URL，无空值！）
        resource = CourseResource(
            course_id=course_id,
            title=data.title,
            type=data.type,
            description=data.description if hasattr(data, 'description') else "",
            url=f"/{file_path}",  # 🔥 必传URL，解决数据库报错
            file_size=os.path.getsize(file_path),
            file_type=file_ext,
            sort_order=0,
            is_published=True,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(resource)
        db.flush()

        # 关联知识点
        if hasattr(data, 'knowledge_ids') and data.knowledge_ids:
            knowledges = db.query(KnowledgePoint).filter(
                KnowledgePoint.id.in_(data.knowledge_ids)
            ).all()
            resource.knowledge_points = knowledges

        db.commit()
        db.refresh(resource)
        return resource

    # ==================== 🔥 新增：资源下载方法 ====================
    def download_resource(self, db: Session, resource_id: int):
        resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
        if not resource:
            raise HTTPException(404, "资源不存在")
        file_path = get_file_path(resource.url)
        return file_path, resource.title

    # ==================== 🔥 新增：学习进度更新方法 ====================
    def update_video_progress(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        更新视频学习进度，自动同步到知识点掌握度
        """
        # 获取或创建进度记录
        progress = self._get_or_create_resource_progress(db, user_id, resource_id)

        # 更新视频专属字段
        if data.watch_position is not None:
            progress.watch_position = data.watch_position
        if data.pause_count is not None:
            progress.pause_count = data.pause_count
        if data.fast_forward_count is not None:
            progress.fast_forward_count = data.fast_forward_count
        if data.rewind_count is not None:
            progress.rewind_count = data.rewind_count

        # 计算完成率和整体进度
        resource = db.query(CourseResource).get(resource_id)
        if resource and resource.duration and resource.duration > 0:
            progress.completion_rate = min(progress.watch_position / resource.duration, 1.0)
            progress.progress = progress.completion_rate * 100

            if progress.completion_rate >= 0.95:
                progress.is_finished = True

        # 更新通用字段
        self._update_common_progress_fields(progress, data)

        # 同步更新关联知识点的视频掌握度
        for point in resource.knowledge_points:
            mastery = self._get_or_create_knowledge_mastery(db, user_id, point.id)
            mastery.video_study_count += 1
            # 取最高完成率作为视频掌握度
            mastery.video_mastery = max(mastery.video_mastery, progress.completion_rate * 100)
            # 重新计算综合掌握度
            self._recalculate_mastery_score(mastery)

        # 更新用户整体画像
        self._update_user_profile(db, user_id)

        db.commit()
        return progress

    def update_exercise_result(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        更新习题答题结果，自动同步到知识点掌握度
        """
        # 获取或创建进度记录
        progress = self._get_or_create_resource_progress(db, user_id, resource_id)

        # 更新习题专属字段
        if data.exercise_score is not None:
            progress.exercise_score = data.exercise_score
        if data.correct_count is not None:
            progress.correct_count = data.correct_count
        if data.total_count is not None:
            progress.total_count = data.total_count
        if data.wrong_question_ids is not None:
            progress.wrong_question_ids = data.wrong_question_ids
        if data.average_answer_time is not None:
            progress.average_answer_time = data.average_answer_time

        # 计算整体进度
        if progress.total_count > 0:
            progress.progress = (progress.correct_count / progress.total_count) * 100
            if progress.progress >= 60:
                progress.is_finished = True

        # 更新通用字段
        self._update_common_progress_fields(progress, data)

        # 同步更新关联知识点的习题掌握度
        resource = db.query(CourseResource).get(resource_id)
        for point in resource.knowledge_points:
            mastery = self._get_or_create_knowledge_mastery(db, user_id, point.id)
            mastery.exercise_attempt_count += 1
            mastery.total_questions += progress.total_count
            mastery.correct_questions += progress.correct_count
            # 取最近3次练习的平均正确率
            recent_scores = self._get_recent_exercise_scores(db, user_id, point.id, limit=3)
            if progress.exercise_score is not None:
                recent_scores.append(progress.exercise_score)
            mastery.exercise_mastery = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            # 重新计算综合掌握度
            self._recalculate_mastery_score(mastery)

        # 更新用户整体画像
        self._update_user_profile(db, user_id)

        db.commit()
        return progress

    def update_document_progress(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        更新文档学习进度，自动同步到知识点掌握度
        """
        # 获取或创建进度记录
        progress = self._get_or_create_resource_progress(db, user_id, resource_id)

        # 更新文档专属字段
        if data.read_pages is not None:
            progress.read_pages = data.read_pages
        if data.total_pages is not None:
            progress.total_pages = data.total_pages
        if data.highlight_count is not None:
            progress.highlight_count = data.highlight_count
        if data.note_count is not None:
            progress.note_count = data.note_count

        # 计算整体进度
        if progress.total_pages > 0:
            progress.progress = (progress.read_pages / progress.total_pages) * 100
            if progress.progress >= 95:
                progress.is_finished = True

        # 更新通用字段
        self._update_common_progress_fields(progress, data)

        # 同步更新关联知识点的视频掌握度（文档学习归为视频类掌握度）
        resource = db.query(CourseResource).get(resource_id)
        for point in resource.knowledge_points:
            mastery = self._get_or_create_knowledge_mastery(db, user_id, point.id)
            mastery.video_study_count += 1
            # 取最高完成率作为掌握度
            mastery.video_mastery = max(mastery.video_mastery, progress.progress)
            # 重新计算综合掌握度
            self._recalculate_mastery_score(mastery)

        # 更新用户整体画像
        self._update_user_profile(db, user_id)

        db.commit()
        return progress

    # ==================== 🔥 新增：知识点掌握度自动计算方法 ====================
    def _recalculate_mastery_score(self, mastery: UserKnowledgeMastery):
        """
        重新计算知识点综合掌握度和等级
        权重：视频学习30% + 习题练习50% + 知识点问答20%
        """
        # 加权计算综合得分
        mastery.mastery_score = (
                mastery.video_mastery * 0.3 +
                mastery.exercise_mastery * 0.5 +
                mastery.qa_mastery * 0.2
        )

        # 根据得分确定掌握等级
        if mastery.mastery_score < 40:
            mastery.level = "未掌握"
        elif mastery.mastery_score < 70:
            mastery.level = "基本掌握"
        else:
            mastery.level = "已掌握"

    # ==================== 🔥 新增：用户画像自动更新方法 ====================
    def _update_user_profile(self, db: Session, user_id: int):
        """
        自动更新用户整体画像数据
        """
        from service.user.user_profile_service import user_profile_engine
        user_profile_engine.schedule_update(user_id)

    # ==================== 私有工具方法 ====================
    def _get_or_create_resource_progress(self, db: Session, user_id: int, resource_id: int):
        """获取或创建用户资源学习进度记录"""
        progress = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.resource_id == resource_id
        ).first()

        if not progress:
            progress = UserResourceProgress(user_id=user_id, resource_id=resource_id)
            db.add(progress)

        return progress

    def _get_or_create_knowledge_mastery(self, db: Session, user_id: int, point_id: int):
        """获取或创建用户知识点掌握度记录"""
        mastery = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.knowledge_point_id == point_id
        ).first()

        if not mastery:
            mastery = UserKnowledgeMastery(user_id=user_id, knowledge_point_id=point_id)
            db.add(mastery)

        return mastery

    def _update_common_progress_fields(self, progress: UserResourceProgress, data: ResourceProgressUpdate):
        """更新通用进度字段"""
        if data.progress is not None:
            progress.progress = data.progress
        if data.is_finished is not None:
            progress.is_finished = data.is_finished
        if data.total_study_duration is not None:
            progress.total_study_duration = max(progress.total_study_duration, data.total_study_duration)

        progress.study_count += 1
        progress.last_study_time = datetime.utcnow()

    def _get_recent_exercise_scores(self, db: Session, user_id: int, point_id: int, limit: int = 3):
        """获取用户最近的习题得分"""
        from models.db_models import UserExerciseRecord
        records = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id,
            UserExerciseRecord.exercise.has(knowledge_points=lambda q: q.filter(id=point_id))
        ).order_by(UserExerciseRecord.create_time.desc()).limit(limit).all()

        return [r.score for r in records]


# 全局单例
admin_course_service = AdminCourseService()


# ==================== 修复后的AdminQaService ====================
class AdminQaService:
    """
    知识点问答管理业务逻辑
    """

    def create_qa_record(self, db: Session, user_id: int, data: KnowledgeQaCreate):
        """
        创建知识点问答记录（大模型回答后调用此方法保存）
        """
        # 创建问答记录
        qa_record = KnowledgeQaRecord(
            user_id=user_id,
            knowledge_point_id=data.knowledge_point_id,
            query=data.query,
            answer=data.answer,
            related_resource_ids=data.related_resource_ids,
            difficulty=data.difficulty,
            is_solved=data.is_solved,
            follow_up_count=data.follow_up_count,
            feedback_score=None
        )
        db.add(qa_record)
        db.flush()

        # 同步更新知识点的问答掌握度
        self._sync_qa_to_mastery(db, user_id, data.knowledge_point_id, qa_record)

        db.commit()
        db.refresh(qa_record)
        return qa_record

    def update_qa_feedback(self, db: Session, qa_id: int, data: KnowledgeQaFeedbackUpdate):
        """
        更新问答反馈（用户评分、是否解决、追问次数）
        """
        qa_record = db.query(KnowledgeQaRecord).filter(KnowledgeQaRecord.id == qa_id).first()
        if not qa_record:
            raise HTTPException(status_code=404, detail="问答记录不存在")

        # 更新反馈字段
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(qa_record, key, value)

        # 重新同步到知识点掌握度
        self._sync_qa_to_mastery(db, qa_record.user_id, qa_record.knowledge_point_id, qa_record)

        db.commit()
        db.refresh(qa_record)
        return qa_record

    @staticmethod
    def get_user_qa_history(db: Session, user_id: int, page: int = 1, size: int = 10):
        """
        获取用户问答历史记录
        """
        query = db.query(KnowledgeQaRecord).filter(KnowledgeQaRecord.user_id == user_id)
        total = query.count()
        records = query.order_by(KnowledgeQaRecord.create_time.desc()).offset((page - 1) * size).limit(size).all()

        return {
            "total": total,
            "items": records,
            "page": page,
            "size": size
        }

    def _sync_qa_to_mastery(self, db: Session, user_id: int, point_id: int, qa_record: KnowledgeQaRecord):
        """
        将问答结果同步到知识点掌握度
        """
        mastery = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.knowledge_point_id == point_id
        ).first()

        if not mastery:
            mastery = UserKnowledgeMastery(user_id=user_id, knowledge_point_id=point_id)
            db.add(mastery)

        mastery.qa_count += 1

        qa_score = 0.0
        if qa_record.is_solved:
            qa_score += 50
        if qa_record.feedback_score is not None:
            qa_score += qa_record.feedback_score * 10
        qa_score += max(0, (5 - qa_record.follow_up_count) * 10)
        qa_score = min(qa_score, 100)

        recent_qa_scores = self._get_recent_qa_scores(db, user_id, point_id, limit=4)
        recent_qa_scores.append(qa_score)
        mastery.qa_mastery = sum(recent_qa_scores) / len(recent_qa_scores)

        from .course_service import admin_course_service
        admin_course_service._recalculate_mastery_score(mastery)

    def _get_recent_qa_scores(self, db: Session, user_id: int, point_id: int, limit: int = 5):
        """获取用户最近的问答得分"""
        records = db.query(KnowledgeQaRecord).filter(
            KnowledgeQaRecord.user_id == user_id,
            KnowledgeQaRecord.knowledge_point_id == point_id
        ).order_by(KnowledgeQaRecord.create_time.desc()).limit(limit).all()

        scores = []
        for r in records:
            score = 0.0
            if r.is_solved:
                score += 50
            if r.feedback_score is not None:
                score += r.feedback_score * 10
            score += max(0, (5 - r.follow_up_count) * 10)
            scores.append(min(score, 100))

        return scores


# 全局单例
admin_qa_service = AdminQaService()