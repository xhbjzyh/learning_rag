
from sqlalchemy.orm import Session
from models.db_models import (
    # 课程核心
    Course, CourseResource,
    # 双知识点体系
    KnowledgePoint, CourseKnowledgePoint,
    # 进度与掌握度
    UserResourceProgress, UserKnowledgeMastery, UserCourseKnowledgeMastery,
    UserProfile,
    # 问答
    KnowledgeQaRecord,
    UserExerciseRecord, Exercise,ExerciseOption
)
from models.schemas import (
    # 课程管理
    AdminCourseCreateRequest, AdminCourseUpdateRequest,
    # 资源管理
    CourseResourceCreate, CourseResourceUpdate, ResourceProgressUpdate,
    CourseResourceFileUpload,
    # 课程知识点
    CourseKnowledgePointCreate, CourseKnowledgePointUpdate,
    # 问答
    KnowledgeQaCreate, KnowledgeQaFeedbackUpdate, ExerciseCreate, ExerciseUpdate
)
from fastapi import HTTPException, UploadFile
from datetime import datetime
import os
from uuid import uuid4
from typing import List, Optional
from utils.logger import logger  # 🔥 新增：导入 logger


# ==================== 工具类导入（修复依赖 + 避免循环导入） ====================
# 延迟导入用户画像服务，解决循环依赖
def get_user_profile_engine():
    from service.user.user_profile_service import user_profile_engine
    return user_profile_engine


# ==================== 全局常量配置 ====================
DEFAULT_RESOURCE_URL = "/static/resources/default.pdf"
UPLOAD_BASE_DIR = "static/resources"


class AdminCourseService:
    """
    管理员课程管理业务逻辑（优化版：双知识点支持 + 全功能完善）
    """

    # ==================== 原有课程管理（优化校验 + 规范代码） ====================
    def get_course_list(self, db: Session, page: int = 1, size: int = 10, title: str = None, category_id: int = None, difficulty: str = None):
        """获取课程列表（分页 + 搜索）"""
        query = db.query(Course)

        # 标题搜索
        if title:
            query = query.filter(Course.title.like(f"%{title}%"))

        # 分类筛选
        if category_id is not None:
            query = query.filter(Course.category_id == category_id)

        # 难度筛选
        if difficulty:
            query = query.filter(Course.difficulty == difficulty)

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return {"total": total, "items": items, "page": page, "size": size}

    def create_course(self, db: Session, data: AdminCourseCreateRequest):
        """创建课程（重名校验 + 自动同步知识点）"""
        if db.query(Course).filter(Course.title == data.title).first():
            raise HTTPException(status_code=400, detail="课程标题已存在")

        course = Course(**data.model_dump())
        db.add(course)
        db.flush()  # 🔥 获取course.id

        # 🔥 如果有关联的课程知识点，创建它们
        if hasattr(data, 'knowledge_points') and data.knowledge_points:
            from models.db_models import CourseKnowledgePoint

            for kp_data in data.knowledge_points:
                course_kp = CourseKnowledgePoint(
                    course_id=course.id,
                    title=kp_data.title,
                    content=kp_data.content,
                    key_points=kp_data.key_points if hasattr(kp_data, 'key_points') else None,
                    difficulty=kp_data.difficulty if hasattr(kp_data, 'difficulty') else "中等",
                    sort_order=kp_data.sort_order if hasattr(kp_data, 'sort_order') else 0
                )
                db.add(course_kp)

        db.commit()
        db.refresh(course)

        # 🔥 自动同步课程知识点到公共知识库
        try:
            from service.admin.knowledge_sync_service import knowledge_sync_service
            sync_result = knowledge_sync_service.sync_course_to_public(db, course.id)

            logger.info(f"✅ 课程 {course.id} 知识点同步完成: {sync_result}")

            # 将同步结果附加到返回数据
            course.sync_result = sync_result
        except Exception as e:
            logger.error(f"⚠️ 课程知识点同步失败: {e}")
            # 同步失败不影响课程创建
            course.sync_result = {"error": str(e)}

        return course

    def update_course(self, db: Session, course_id: int, data: AdminCourseUpdateRequest):
        """更新课程"""
        course = db.query(Course).get(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(course, k, v)

        db.commit()
        db.refresh(course)
        return course

    def delete_course(self, db: Session, course_id: int):
        """删除课程（级联清理资源/知识点）"""
        course = db.query(Course).get(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        db.delete(course)
        db.commit()
        return True

    # ==================== 🔥 课程专属知识点管理（新增全套功能） ====================
    def create_course_knowledge(self, db: Session, data: CourseKnowledgePointCreate):
        """创建课程专属知识点"""
        if not db.query(Course).get(data.course_id):
            raise HTTPException(status_code=404, detail="课程不存在")

        knowledge = CourseKnowledgePoint(**data.model_dump())
        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)
        return knowledge

    def update_course_knowledge(self, db: Session, knowledge_id: int, data: CourseKnowledgePointUpdate):
        """更新课程专属知识点"""
        knowledge = db.query(CourseKnowledgePoint).get(knowledge_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="课程知识点不存在")

        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(knowledge, k, v)

        db.commit()
        db.refresh(knowledge)
        return knowledge

    def delete_course_knowledge(self, db: Session, knowledge_id: int):
        """删除课程专属知识点"""
        knowledge = db.query(CourseKnowledgePoint).get(knowledge_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="课程知识点不存在")

        db.delete(knowledge)
        db.commit()
        return True

    def get_course_knowledge_list(self, db: Session, course_id: int):
        """获取课程下所有专属知识点"""
        if not db.query(Course).get(course_id):
            raise HTTPException(status_code=404, detail="课程不存在")
        return db.query(CourseKnowledgePoint).filter(
            CourseKnowledgePoint.course_id == course_id
        ).order_by(CourseKnowledgePoint.sort_order).all()

    # ==================== 🔥 课程资源管理（优化：双知识点关联 + 自动填充） ====================
    def get_course_resources(self, db: Session, course_id: int, resource_type: str = None):
        """获取课程资源（支持类型筛选 + 双知识点ID返回）"""
        if not db.query(Course).get(course_id):
            raise HTTPException(status_code=404, detail="课程不存在")

        query = db.query(CourseResource).filter(CourseResource.course_id == course_id)
        if resource_type:
            query = query.filter(CourseResource.type == resource_type)

        resources = query.order_by(CourseResource.sort_order).all()
        # 补充双知识点ID列表
        for res in resources:
            res.knowledge_ids = [kp.id for kp in res.knowledge_points]
            res.course_knowledge_ids = [kp.id for kp in res.course_knowledge_points]
        return resources

    # 1. 修复创建资源（支持多知识点，过滤无效ID）
    def create_resource(self, db: Session, course_id: int, data: CourseResourceCreate):
        if not db.query(Course).get(course_id):
            raise HTTPException(status_code=404, detail="课程不存在")

        resource_data = data.model_dump(
            exclude={"knowledge_ids", "course_knowledge_ids", "videos", "document", "exercise"}
        )

        resource_data.setdefault("url", DEFAULT_RESOURCE_URL)
        resource_data.setdefault("file_type",
                                 resource_data["url"].split(".")[-1].lower() if "." in resource_data["url"] else "pdf")
        resource_data.setdefault("file_size", 0)
        resource_data.setdefault("duration", 0)

        db_resource = CourseResource(course_id=course_id, **resource_data)
        db.add(db_resource)
        db.flush()

        # 🔥 核心修复：过滤无效ID（空/0/非数字），支持多知识点
        db_resource.knowledge_points = []
        valid_ids = [kid for kid in data.course_knowledge_ids if isinstance(kid, int) and kid > 0]
        if valid_ids:
            db_resource.course_knowledge_points = db.query(CourseKnowledgePoint).filter(
                CourseKnowledgePoint.id.in_(valid_ids)
            ).all()

        db.commit()
        db.refresh(db_resource)
        db_resource.course_knowledge_ids = [kp.id for kp in db_resource.course_knowledge_points]
        return db_resource

    # 2. 修复更新资源（🔥 关键：不传参=不修改，防覆盖为空！支持多ID）
    def update_resource(self, db: Session, resource_id: int, data: CourseResourceUpdate):
        db_resource = db.query(CourseResource).get(resource_id)
        if not db_resource:
            raise HTTPException(status_code=404, detail="课程资源不存在")

        update_data = data.model_dump(exclude_unset=True, exclude={"knowledge_ids", "course_knowledge_ids"})
        for k, v in update_data.items():
            setattr(db_resource, k, v)

        # 🔥 核心修复：只有【主动传参】才更新，不传=保留原有关联！
        db_resource.knowledge_points = []
        if data.course_knowledge_ids is not None:
            # 过滤无效ID，支持多个
            valid_ids = [kid for kid in data.course_knowledge_ids if isinstance(kid, int) and kid > 0]
            db_resource.course_knowledge_points = db.query(CourseKnowledgePoint).filter(
                CourseKnowledgePoint.id.in_(valid_ids)
            ).all()

        db.commit()
        db.refresh(db_resource)
        db_resource.course_knowledge_ids = [kp.id for kp in db_resource.course_knowledge_points]
        return db_resource

    def delete_resource(self, db: Session, resource_id: int):
        """删除课程资源（级联清理学习进度）"""
        db_resource = db.query(CourseResource).get(resource_id)
        if not db_resource:
            raise HTTPException(status_code=404, detail="课程资源不存在")

        db.delete(db_resource)
        db.commit()
        return True

    # ==================== 🔥 习题管理（新增） ====================
    def get_exercise_list(self, db: Session, course_id: int):
        """获取课程下所有习题"""
        from models.db_models import Exercise, ExerciseOption

        # 验证课程是否存在
        if not db.query(Course).get(course_id):
            raise HTTPException(status_code=404, detail="课程不存在")

        # 查询习题列表 - 🔥 按ID升序排序
        exercises = db.query(Exercise).filter(
            Exercise.course_id == course_id
        ).order_by(Exercise.id.asc()).all()

        # 补充选项和知识点信息
        result = []
        for exercise in exercises:
            exercise_dict = {
                "id": exercise.id,
                "title": exercise.title,
                "type": exercise.type,
                "difficulty": exercise.difficulty,
                "analysis": exercise.analysis,
                "score": exercise.score,
                "create_time": exercise.create_time,
                # 关联的知识点ID列表
                "knowledge_ids": [],
                "course_knowledge_ids": [kp.id for kp in exercise.course_knowledge_points],
                # 选项列表
                "options": [
                    {
                        "id": opt.id,
                        "option_label": opt.option_label,
                        "option_content": opt.option_content,
                        "is_correct": opt.is_correct,
                        "order": opt.order
                    }
                    for opt in sorted(exercise.options, key=lambda x: x.order)
                ]
            }
            result.append(exercise_dict)

        return result

    def create_exercise(self, db: Session, course_id: int, data):
        """创建课程习题"""
        from models.db_models import Exercise, ExerciseOption
        
        # 验证课程存在
        if not db.query(Course).get(course_id):
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 🔥 关键修复：确保 answer 字段存储的是字母格式（A/B/C/D）
        answer = data.answer
        if answer:
            # 如果传入的是数字索引，转换为字母（0->A, 1->B, 2->C, 3->D）
            try:
                num = int(answer)
                if 0 <= num <= 5:
                    answer = chr(ord('A') + num)
            except (ValueError, TypeError):
                # 如果不是数字，保持原样（假设已经是字母）
                answer = answer.strip().upper()
        
        if not answer and data.options:
            # 对于选择题，从选项中提取正确答案并转换为字母
            correct_options = [opt for opt in data.options if opt.is_correct]
            if correct_options:
                # 取第一个正确选项的索引，转换为字母
                first_correct = correct_options[0]
                order = first_correct.order if hasattr(first_correct, 'order') else 0
                answer = chr(ord('A') + order)
            else:
                answer = "暂无标准答案"
        elif not answer:
            answer = "暂无标准答案"
        
        exercise = Exercise(
            course_id=course_id,
            title=data.title,
            type=data.type.value if hasattr(data.type, 'value') else data.type,
            difficulty=data.difficulty,
            answer=answer,  # 🔥 确保存储的是字母格式
            analysis=data.analysis,
            score=10.0  # 默认分值
        )
        db.add(exercise)
        db.flush()
        
        # 关联知识点
        if data.course_knowledge_ids:
            valid_ids = [kid for kid in data.course_knowledge_ids if isinstance(kid, int) and kid > 0]
            if valid_ids:
                exercise.course_knowledge_points = db.query(CourseKnowledgePoint).filter(
                    CourseKnowledgePoint.id.in_(valid_ids)
                ).all()
        
        # 创建选项
        if data.options:
            for opt_data in data.options:
                option = ExerciseOption(
                    exercise_id=exercise.id,
                    content=opt_data.option_content,  # 🔥 使用 content 字段
                    is_correct=opt_data.is_correct,
                    order=opt_data.order if hasattr(opt_data, 'order') else 0
                )
                db.add(option)
        
        db.commit()
        db.refresh(exercise)
        return exercise
    
    def update_exercise(self, db: Session, exercise_id: int, data):
        """更新课程习题"""
        from models.db_models import Exercise, ExerciseOption
        
        # 查询习题
        exercise = db.query(Exercise).get(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="习题不存在")
        
        # 更新基本字段
        if data.title is not None:
            exercise.title = data.title
        if data.type is not None:
            exercise.type = data.type.value if hasattr(data.type, 'value') else data.type
        if data.difficulty is not None:
            exercise.difficulty = data.difficulty
        if data.analysis is not None:
            exercise.analysis = data.analysis
        
        # 🔥 关键修复：更新答案时也转换为字母格式
        if data.answer is not None:
            answer = data.answer
            try:
                num = int(answer)
                if 0 <= num <= 5:
                    answer = chr(ord('A') + num)
            except (ValueError, TypeError):
                answer = answer.strip().upper()
            exercise.answer = answer
        
        # 更新知识点关联
        if data.course_knowledge_ids is not None:
            exercise.course_knowledge_points = []
            valid_ids = [kid for kid in data.course_knowledge_ids if isinstance(kid, int) and kid > 0]
            if valid_ids:
                exercise.course_knowledge_points = db.query(CourseKnowledgePoint).filter(
                    CourseKnowledgePoint.id.in_(valid_ids)
                ).all()
        
        # 更新选项（先删除旧选项，再创建新选项）
        if data.options is not None:
            # 删除旧选项
            db.query(ExerciseOption).filter(ExerciseOption.exercise_id == exercise_id).delete()
            
            # 如果有新选项且没有显式提供答案，从选项中提取
            if data.options and data.answer is None:
                correct_options = [opt for opt in data.options if opt.is_correct]
                if correct_options:
                    first_correct = correct_options[0]
                    order = first_correct.order if hasattr(first_correct, 'order') else 0
                    exercise.answer = chr(ord('A') + order)
            
            # 创建新选项
            for opt_data in data.options:
                option = ExerciseOption(
                    exercise_id=exercise_id,
                    content=opt_data.option_content,  # 🔥 使用 content 字段
                    is_correct=opt_data.is_correct,
                    order=opt_data.order if hasattr(opt_data, 'order') else 0
                )
                db.add(option)
        
        db.commit()
        db.refresh(exercise)
        return exercise

    def delete_exercise(self, db: Session, exercise_id: int):
        """删除课程习题"""
        from models.db_models import Exercise

        exercise = db.query(Exercise).get(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="习题不存在")

        db.delete(exercise)
        db.commit()
        return True

    # ==================== 🔥 文件上传（优化：规范路径 + 类型校验） ====================
    def create_resource_with_file(
            self, db: Session, course_id: int,
            data: CourseResourceFileUpload, file: UploadFile
    ):
        """上传文件并创建资源（仅关联课程知识点）"""
        if not db.query(Course).get(course_id):
            raise HTTPException(status_code=404, detail="课程不存在")

        upload_dir = os.path.join(UPLOAD_BASE_DIR, str(course_id))
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
        file_name = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        resource = CourseResource(
            course_id=course_id,
            title=data.title,
            type=data.type,
            description=data.description or "",
            url=f"/{file_path}",
            file_size=os.path.getsize(file_path),
            file_type=file_ext,
            sort_order=data.sort_order,
            is_published=True,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(resource)
        db.flush()

        # ===================== 核心修复 =====================
        # 清空全局知识点
        resource.knowledge_points = []
        # 仅绑定课程知识点
        if hasattr(data, "course_knowledge_ids") and data.course_knowledge_ids:
            resource.course_knowledge_points = db.query(CourseKnowledgePoint).filter(
                CourseKnowledgePoint.id.in_(data.course_knowledge_ids)).all()

        db.commit()
        db.refresh(resource)
        return resource
    # ==================== 🔥 学习进度（优化：双知识点掌握度同步） ====================
    def update_resource_progress(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        统一进度更新入口（自动识别资源类型：视频/文档/习题）
        同步：知识库知识点 + 课程专属知识点 掌握度
        """
        resource = db.query(CourseResource).get(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")

        progress = self._get_or_create_resource_progress(db, user_id, resource_id)
        self._update_common_progress_fields(progress, data)

        # 按资源类型更新专属字段
        if resource.type == "videos":
            self._update_video_progress_fields(progress, data)
        elif resource.type == "document":
            self._update_document_progress_fields(progress, data)
        elif resource.type == "exercise":
            self._update_exercise_progress_fields(progress, data)

        # 🔥 核心：同步双知识点掌握度
        self._sync_progress_to_mastery(db, user_id, resource, progress)
        # 更新用户画像
        get_user_profile_engine().schedule_update(user_id)

        db.commit()
        db.refresh(progress)
        return progress

    # ==================== 🔥 掌握度计算（优化：双知识点支持） ====================
    def _sync_progress_to_mastery(self, db: Session, user_id: int, resource: CourseResource,
                                  progress: UserResourceProgress):
        """同步学习进度到 知识库知识点 + 课程知识点 掌握度"""
        # 1. 同步知识库知识点
        for kp in resource.knowledge_points:
            mastery = self._get_or_create_knowledge_mastery(db, user_id, kp.id)
            self._update_mastery_by_progress(mastery, resource.type, progress)
            self._recalculate_mastery_score(mastery)

        # 2. 同步课程专属知识点（新增核心）
        for ck in resource.course_knowledge_points:
            mastery = self._get_or_create_course_knowledge_mastery(db, user_id, ck.id)
            self._update_mastery_by_progress(mastery, resource.type, progress)
            self._recalculate_course_mastery_score(mastery)

    def _recalculate_mastery_score(self, mastery: UserKnowledgeMastery):
        """重新计算知识库知识点综合掌握度"""
        mastery.mastery_score = mastery.video_mastery * 0.3 + mastery.exercise_mastery * 0.5 + mastery.qa_mastery * 0.2
        mastery.level = "未掌握" if mastery.mastery_score < 40 else "基本掌握" if mastery.mastery_score < 70 else "已掌握"

    def _recalculate_course_mastery_score(self, mastery: UserCourseKnowledgeMastery):
        """重新计算课程知识点综合掌握度（同权重）"""
        mastery.mastery_score = mastery.video_mastery * 0.3 + mastery.exercise_mastery * 0.5 + mastery.qa_mastery * 0.2
        mastery.level = "未掌握" if mastery.mastery_score < 40 else "基本掌握" if mastery.mastery_score < 70 else "已掌握"

    # ==================== 私有工具方法（规范化 + 解耦） ====================
    def _get_or_create_resource_progress(self, db: Session, user_id: int, resource_id: int) -> UserResourceProgress:
        progress = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.resource_id == resource_id
        ).first()
        if not progress:
            progress = UserResourceProgress(user_id=user_id, resource_id=resource_id)
            db.add(progress)
        return progress

    def _get_or_create_knowledge_mastery(self, db: Session, user_id: int, point_id: int) -> UserKnowledgeMastery:
        mastery = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.knowledge_point_id == point_id
        ).first()
        if not mastery:
            mastery = UserKnowledgeMastery(user_id=user_id, knowledge_point_id=point_id)
            db.add(mastery)
        return mastery

    def _get_or_create_course_knowledge_mastery(self, db: Session, user_id: int,
                                                point_id: int) -> UserCourseKnowledgeMastery:
        """课程知识点掌握度（新增）"""
        mastery = db.query(UserCourseKnowledgeMastery).filter(
            UserCourseKnowledgeMastery.user_id == user_id,
            UserCourseKnowledgeMastery.course_knowledge_point_id == point_id
        ).first()
        if not mastery:
            mastery = UserCourseKnowledgeMastery(user_id=user_id, course_knowledge_point_id=point_id)
            db.add(mastery)
        return mastery

    def _update_common_progress_fields(self, progress: UserResourceProgress, data: ResourceProgressUpdate):
        if data.progress is not None:
            progress.progress = data.progress
        if data.is_finished is not None:
            progress.is_finished = data.is_finished

        # 🔥 关键修复：累加学习时长
        if hasattr(data, 'study_duration') and data.study_duration:
            # 累加本次学习时长
            progress.total_study_duration += int(data.study_duration)
        elif data.total_study_duration is not None:
            # 如果没有 study_duration，使用 total_study_duration（取最大值）
            progress.total_study_duration = max(progress.total_study_duration, data.total_study_duration)

        progress.study_count += 1
        progress.last_study_time = datetime.utcnow()

    def _update_video_progress_fields(self, progress: UserResourceProgress, data: ResourceProgressUpdate):
        # 🔥 调试日志：打印关键信息
        from utils.logger import logger
        logger.info(f"🔥 视频进度更新调试: watch_position={data.watch_position}, progress.watch_position={progress.watch_position}, resource={progress.resource}, duration={progress.resource.duration if progress.resource else 'N/A'}")

        # 🔥 关键修复：确保 watch_position 不为 None
        if data.watch_position is not None:
            progress.watch_position = data.watch_position

        # 🔥 防御性编程：处理所有可能的 None 值
        watch_pos = progress.watch_position or 0

        # 确保 resource 和 duration 存在
        duration = 1  # 默认值
        if hasattr(progress, 'resource') and progress.resource:
            duration = getattr(progress.resource, 'duration', None) or 1

        logger.info(f"🔥 计算参数: watch_pos={watch_pos}, duration={duration}")

        # 计算完成率（避免除以0和None）
        try:
            progress.completion_rate = min(watch_pos / duration, 1.0)
            progress.progress = progress.completion_rate * 100
            progress.is_finished = progress.completion_rate >= 0.95
            logger.info(f"✅ 计算成功: completion_rate={progress.completion_rate}, progress={progress.progress}")
        except (TypeError, ZeroDivisionError) as e:
            # 如果计算失败，使用安全默认值
            progress.completion_rate = 0.0
            progress.progress = 0.0
            progress.is_finished = False
            logger.error(f"❌ 计算失败，使用默认值: {str(e)}")

    def _update_document_progress_fields(self, progress: UserResourceProgress, data: ResourceProgressUpdate):
        if data.read_pages: progress.read_pages = data.read_pages
        if data.total_pages: progress.total_pages = data.total_pages
        if progress.total_pages > 0:
            progress.progress = (progress.read_pages / progress.total_pages) * 100
            progress.is_finished = progress.progress >= 95

    def _update_exercise_progress_fields(self, progress: UserResourceProgress, data: ResourceProgressUpdate):
        if data.exercise_score: progress.exercise_score = data.exercise_score
        if data.correct_count: progress.correct_count = data.correct_count
        if data.total_count: progress.total_count = data.total_count
        if progress.total_count > 0:
            progress.progress = (progress.correct_count / progress.total_count) * 100
            progress.is_finished = progress.progress >= 60

    def _update_mastery_by_progress(self, mastery, resource_type: str, progress: UserResourceProgress):
        """根据资源类型更新掌握度分值"""
        if resource_type in ["videos", "document"]:
            mastery.video_mastery = max(mastery.video_mastery, progress.progress)
            mastery.video_study_count += 1
        elif resource_type == "exercise":
            mastery.exercise_mastery = progress.exercise_score or 0
            mastery.exercise_attempt_count += 1

    def _get_recent_exercise_scores(self, db: Session, user_id: int, point_id: int, limit: int = 3):
        records = db.query(UserExerciseRecord).filter(
            UserExerciseRecord.user_id == user_id,
            UserExerciseRecord.exercise.has(knowledge_points=any(id=point_id))
        ).order_by(UserExerciseRecord.create_time.desc()).limit(limit).all()
        return [r.score for r in records]


# 全局单例
admin_course_service = AdminCourseService()


# ==================== 问答服务优化（修复循环依赖 + 兼容课程知识点） ====================
class AdminQaService:
    """知识点问答管理（优化版：无循环依赖 + 双知识点支持）"""

    def create_qa_record(self, db: Session, user_id: int, data: KnowledgeQaCreate):
        qa_record = KnowledgeQaRecord(
            user_id=user_id, **data.model_dump(), feedback_score=None
        )
        db.add(qa_record)
        db.flush()
        self._sync_qa_to_mastery(db, user_id, data.knowledge_point_id, qa_record)
        db.commit()
        db.refresh(qa_record)
        return qa_record

    def update_qa_feedback(self, db: Session, qa_id: int, data: KnowledgeQaFeedbackUpdate):
        qa_record = db.query(KnowledgeQaRecord).get(qa_id)
        if not qa_record: raise HTTPException(404, "问答记录不存在")

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(qa_record, k, v)

        self._sync_qa_to_mastery(db, qa_record.user_id, qa_record.knowledge_point_id, qa_record)
        db.commit()
        return qa_record

    @staticmethod
    def get_user_qa_history(db: Session, user_id: int, page: int = 1, size: int = 10):
        query = db.query(KnowledgeQaRecord).filter(KnowledgeQaRecord.user_id == user_id)
        return {
            "total": query.count(),
            "items": query.order_by(KnowledgeQaRecord.create_time.desc()).offset((page - 1) * size).limit(size).all(),
            "page": page, "size": size
        }

    def _sync_qa_to_mastery(self, db: Session, user_id: int, point_id: int, qa_record: KnowledgeQaRecord):
        # 同步知识库知识点掌握度
        mastery = admin_course_service._get_or_create_knowledge_mastery(db, user_id, point_id)
        mastery.qa_count += 1
        mastery.qa_mastery = self._calc_qa_score(qa_record)
        admin_course_service._recalculate_mastery_score(mastery)

    def _calc_qa_score(self, qa_record: KnowledgeQaRecord) -> float:
        score = 50 if qa_record.is_solved else 0
        score += (qa_record.feedback_score or 0) * 10
        score += max(0, (5 - qa_record.follow_up_count) * 10)
        return min(score, 100)


admin_qa_service = AdminQaService()