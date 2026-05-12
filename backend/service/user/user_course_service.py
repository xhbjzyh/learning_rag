"""
用户端课程学习综合服务（合并版）
整合：资源观看、习题练习、错题本、大模型专项练习、个性化推荐
替代原：course_service.py / exercise_service.py / wrong_question_service.py / recommendation_service.py
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, text, true, false
from datetime import datetime, timedelta

from models.db_models import (
    Course, CourseResource, UserResourceProgress,
    UserCourseProgress, UserKnowledgeMastery, UserProfile,
    Exercise, UserExerciseRecord, WrongQuestion,
    KnowledgePoint, UserLearningPreference, UserInterestTag,
    CourseTag, CourseTagRel, UserCourseKnowledgeMastery,
    exercise_knowledge, CourseKnowledgePoint,
    exercise_course_knowledge_rel  # 新增：导入 exercise_knowledge 和 CourseKnowledgePoint
)
from models.schemas import ResourceProgressUpdate, ExerciseSubmit
from utils.response import BusinessException, BusinessErrorCode
from utils.logger import logger
from core.llm import llm


class UserCourseService:
    """
    用户端课程学习核心服务（全功能合一）
    """

    # ==============================================
    # 🔹 1. 课程与资源管理
    # ==============================================
    def get_course_list(self, db: Session, page: int = 1, size: int = 10,
                        category_id: int = None, difficulty: str = None, title: str = None):
        """获取用户可见的课程列表（仅已发布）"""
        query = db.query(Course).filter(Course.is_published == True, Course.is_public == True)

        if category_id:
            query = query.filter(Course.category_id == category_id)
        if difficulty:
            query = query.filter(Course.difficulty == difficulty)
        if title:
            query = query.filter(Course.title.like(f"%{title}%"))

        query = query.order_by(Course.view_count.desc())
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return {"total": total, "items": items, "page": page, "size": size}

    def get_course_detail(self, db: Session, user_id: int, course_id: int):
        """获取课程详情及用户学习进度"""
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.is_published == True
        ).first()

        if not course:
            raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "课程不存在或未发布")

        course.view_count += 1

        user_progress = db.query(UserCourseProgress).filter(
            UserCourseProgress.user_id == user_id,
            UserCourseProgress.course_id == course_id
        ).first()

        if not user_progress:
            user_progress = UserCourseProgress(user_id=user_id, course_id=course_id)
            db.add(user_progress)

        resources = db.query(CourseResource).filter(
            CourseResource.course_id == course_id,
            CourseResource.is_published == True
        ).order_by(CourseResource.sort_order).all()

        resource_list = []
        for resource in resources:
            progress = db.query(UserResourceProgress).filter(
                UserResourceProgress.user_id == user_id,
                UserResourceProgress.resource_id == resource.id
            ).first()

            resource_data = {
                "id": resource.id,
                "course_id": resource.course_id,
                "title": resource.title,
                "type": resource.type,
                "description": resource.description,
                "url": resource.url,
                "duration": resource.duration,
                "file_size": resource.file_size,
                "file_type": resource.file_type,
                "exercise_id": resource.exercise_id,
                "sort_order": resource.sort_order,
                "is_published": resource.is_published,
                "create_time": resource.create_time,
                "update_time": resource.update_time
            }

            if progress:
                resource_data["user_progress"] = {
                    "id": progress.id,
                    "user_id": progress.user_id,
                    "resource_id": progress.resource_id,
                    "progress": progress.progress,
                    "is_finished": progress.is_finished,
                    "last_study_time": progress.last_study_time,
                    "total_study_duration": progress.total_study_duration
                }
            else:
                resource_data["user_progress"] = None

            resource_list.append(resource_data)

        db.commit()
        db.refresh(user_progress)

        return {
            "course": course,
            "user_progress": user_progress,
            "resources": resource_list
        }

    def get_course_resources(self, db: Session, course_id: int, resource_type: str = None, user_id: int = None):
        query = db.query(CourseResource).filter(
            CourseResource.course_id == course_id,
            CourseResource.is_published == True
        )

        if resource_type:
            query = query.filter(CourseResource.type == resource_type)

        resources = query.order_by(CourseResource.sort_order).all()
        resource_list = []

        for resource in resources:
            progress = None
            if user_id:
                progress = db.query(UserResourceProgress).filter(
                    UserResourceProgress.user_id == user_id,
                    UserResourceProgress.resource_id == resource.id
                ).first()

            resource_data = {
                "id": resource.id,
                "course_id": resource.course_id,
                "title": resource.title,
                "type": resource.type,
                "description": resource.description,
                "url": resource.url,
                "duration": resource.duration,
                "file_size": resource.file_size,
                "file_type": resource.file_type,
                "sort_order": resource.sort_order,
                "user_progress": {
                    "progress": progress.progress if progress else 0,
                    "is_finished": progress.is_finished if progress else False
                }
            }
            resource_list.append(resource_data)

        return resource_list

    def update_resource_progress(self, db: Session, user_id: int, resource_id: int, data: ResourceProgressUpdate):
        """
        更新资源学习进度（视频/文档通用）
        同时同步到 LearningProgress 表用于统计
        """
        from models.db_models import LearningProgress, CourseResource
        
        # 1. 获取资源信息
        resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
        if not resource:
            raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "资源不存在")
        
        # 2. 更新 UserResourceProgress
        progress = self._get_or_create_resource_progress(db, user_id, resource_id)
        
        # 更新通用字段
        if data.progress is not None:
            progress.progress = data.progress
        if data.is_finished is not None:
            progress.is_finished = data.is_finished
        if data.total_study_duration is not None:
            progress.total_study_duration = max(progress.total_study_duration, data.total_study_duration)
        
        # 🔥 关键修复：累加学习时长（如果没有传 total_study_duration，使用 study_duration）
        logger.info(f"🔥 学习时长调试: study_duration={getattr(data, 'study_duration', None)}, total_study_duration={data.total_study_duration}, 当前total={progress.total_study_duration}")
        
        # 🔥 修复：检查参数是否存在（而不是是否为真值），允许0值
        if hasattr(data, 'study_duration') and data.study_duration is not None:
            duration_value = int(data.study_duration)
            if duration_value > 0:
                logger.info(f"✅ 累加学习时长: {duration_value}秒")
                progress.total_study_duration += duration_value
            else:
                logger.warning(f"⚠️ study_duration为0或负数，跳过累加: {duration_value}")
        else:
            logger.warning(f"⚠️ 未收到 study_duration 参数，无法累加")

        progress.study_count += 1
        progress.last_study_time = func.now()
        
        # 更新视频专属字段
        if resource.type == "video":
            # 🔥 关键修复：确保 watch_position 不为 None
            if data.watch_position is not None:
                progress.watch_position = data.watch_position
            
            # 🔥 防御性编程：处理 None 值
            watch_pos = progress.watch_position or 0
            duration = resource.duration or 1
            
            # 计算完成率（避免除以0和None）
            try:
                progress.completion_rate = min(watch_pos / duration, 1.0)
                progress.progress = progress.completion_rate * 100
                progress.is_finished = progress.completion_rate >= 0.95
            except (TypeError, ZeroDivisionError) as e:
                logger.warning(f"计算视频完成率失败: watch_pos={watch_pos}, duration={duration}, error={str(e)}")
                progress.completion_rate = 0.0
                progress.progress = 0.0
                progress.is_finished = False

        db.add(progress)
        db.flush()
        
        # 3. 🔥 核心修复：同步到 LearningProgress 表（用于统计）
        if resource.course_knowledge_points:
            # 取第一个关联的知识点作为代表
            first_point = resource.course_knowledge_points[0]
            
            learning_progress = db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.point_id == first_point.id
            ).first()
            
            if not learning_progress:
                learning_progress = LearningProgress(
                    user_id=user_id,
                    point_id=first_point.id,
                    progress=0.0,
                    study_duration=0,
                    is_finished=False
                )
                db.add(learning_progress)
            
            # 更新学习进度
            learning_progress.progress = max(learning_progress.progress, progress.progress)
            
            # 🔥 关键：累加学习时长
            if hasattr(data, 'study_duration') and data.study_duration is not None:
                duration_value = int(data.study_duration)
                if duration_value > 0:
                    learning_progress.study_duration += duration_value
            elif data.total_study_duration:
                learning_progress.study_duration = max(learning_progress.study_duration, data.total_study_duration)

            learning_progress.is_finished = progress.is_finished
            learning_progress.last_study_time = func.now()
            
            db.add(learning_progress)
            db.flush()
        
        # 4. 如果是视频资源，同步更新知识点掌握度
        if resource.type == "video":
            try:
                self.update_video_mastery(db, user_id, resource_id, data.progress)
            except Exception as e:
                logger.warning(f"更新视频掌握度失败: {str(e)}")
        
        # 5. 提交事务
        db.commit()
        db.refresh(progress)
        
        return progress
    
    def _get_or_create_resource_progress(self, db: Session, user_id: int, resource_id: int):
        """获取或创建资源进度记录"""
        from models.db_models import UserResourceProgress
        
        progress = db.query(UserResourceProgress).filter(
            UserResourceProgress.user_id == user_id,
            UserResourceProgress.resource_id == resource_id
        ).first()
        
        if not progress:
            progress = UserResourceProgress(
                user_id=user_id,
                resource_id=resource_id,
                progress=0.0,
                is_finished=False,
                total_study_duration=0,
                study_count=0
            )
            db.add(progress)
        
        return progress

    # ==============================================
    # 🔹 2. 习题练习与批改
    # ==============================================
    def get_exercise_list(self, db: Session, course_id: int = None, page: int = 1, size: int = 10):
        query = db.query(Exercise)

        if course_id:
            query = query.filter(Exercise.course_id == course_id)

        total = query.count()
        exercises = query.offset((page - 1) * size).limit(size).all()

        result = []
        for exercise in exercises:
            # 获取知识库知识点
            kb_knowledge_points = [
                {
                    "id": kp.id,
                    "title": kp.title,
                    "type": "knowledge_base"  # 标记为知识库知识点
                } for kp in exercise.knowledge_points
            ]
            
            # 获取课程专属知识点
            course_knowledge_points = [
                {
                    "id": kp.id,
                    "title": kp.title,
                    "type": "course"  # 标记为课程知识点
                } for kp in exercise.course_knowledge_points
            ]
            
            # 合并两种知识点
            all_knowledge_points = kb_knowledge_points + course_knowledge_points

            exercise_data = {
                "id": exercise.id,
                "title": exercise.title,
                "type": exercise.type,
                "difficulty": exercise.difficulty,
                "score": exercise.score,
                "course_id": exercise.course_id,
                "knowledge_points": all_knowledge_points,  # 新增：知识点列表
                "options": [
                    {
                        "id": opt.id,
                        "option_label": opt.option_label,
                        "option_content": opt.option_content
                    } for opt in exercise.options
                ]
            }
            result.append(exercise_data)

        return {"total": total, "items": result, "page": page, "size": size}

    def get_exercise_detail(self, db: Session, exercise_id: int):
        exercise = db.query(Exercise).get(exercise_id)

        if not exercise:
            raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "习题不存在")

        return {
            "id": exercise.id,
            "title": exercise.title,
            "type": exercise.type,
            "difficulty": exercise.difficulty,
            "course_id": exercise.course_id,
            "options": [
                {
                    "id": opt.id,
                    "option_label": opt.option_label,
                    "option_content": opt.option_content
                } for opt in exercise.options
            ]
        }

    def submit_exercise_answer(self, db: Session, user_id: int, data: ExerciseSubmit):
        # 1. 查询习题
        exercise = db.query(Exercise).filter(Exercise.id == data.exercise_id).first()
        if not exercise:
            raise BusinessException("习题不存在")

        # 2. 判断答案是否正确
        is_correct = (data.user_answer == exercise.answer)
        final_score = exercise.score if is_correct else 0

        # ===================== 【1】保存答题记录 =====================
        record = UserExerciseRecord(
            user_id=user_id,
            exercise_id=data.exercise_id,
            user_answer=data.user_answer,
            is_correct=is_correct,
            score=final_score,
            answer_time=data.answer_time if hasattr(data, 'answer_time') else None
        )
        db.add(record)

        # ===================== 【2】保存错题记录（答错才存） =====================
        if not is_correct:
            wrong = WrongQuestion(
                user_id=user_id,
                exercise_id=exercise.id,
                question_title=exercise.title,
                user_answer=data.user_answer,
                correct_answer=exercise.answer,
                wrong_count=1,
                master_level=0
            )
            db.add(wrong)

        # ===================== 【3】恢复：更新知识点掌握度 =====================
        self._update_knowledge_mastery(db, user_id, exercise, is_correct)

        # 提交所有数据库变更
        db.commit()

        # 返回结果
        return {
            "is_correct": is_correct,
            "user_answer": data.user_answer,
            "correct_answer": exercise.answer,
            "score": final_score,
            "analysis": exercise.analysis
        }

    # ✅【终极修复】完全匹配你数据库UserKnowledgeMastery真实字段！！！
    # ✅ 最终修复：解决 None 值运算报错 + 100%匹配数据库字段
    def _update_knowledge_mastery(self, db: Session, user_id: int, exercise: Exercise, is_correct: bool):
        """
        更新用户知识点掌握度（课程专属知识点）
        采用双源融合评分：视频学习(35%) + 习题练习(65%) = 100分
        """
        # ===================== 更新【课程专属知识点】掌握度 =====================
        for course_point in exercise.course_knowledge_points:
            # 查询用户是否已有该课程知识点的掌握记录
            course_mastery = db.query(UserCourseKnowledgeMastery).filter(
                UserCourseKnowledgeMastery.user_id == user_id,
                UserCourseKnowledgeMastery.course_knowledge_id == course_point.id
            ).first()

            if not course_mastery:
                course_mastery = UserCourseKnowledgeMastery(
                    user_id=user_id,
                    course_knowledge_id=course_point.id,
                    mastery_score=0.0,
                    level="未学习",
                    video_mastery=0.0,
                    exercise_mastery=0.0
                )
                db.add(course_mastery)

            # 🔥 关键修复：确保 video_mastery 不为 None
            video_mastery = getattr(course_mastery, 'video_mastery', 0.0)
            if video_mastery is None:
                video_mastery = 0.0
            
            # 更新习题维度掌握度（正确率，占65%）
            # 获取该知识点下所有习题的答题记录
            from models.db_models import UserExerciseRecord
            exercise_records = db.query(UserExerciseRecord).join(
                Exercise
            ).join(
                exercise_course_knowledge_rel
            ).filter(
                exercise_course_knowledge_rel.c.course_knowledge_id == course_point.id,
                UserExerciseRecord.user_id == user_id
            ).all()
            
            total_exercises = len(exercise_records)
            correct_exercises = sum(1 for r in exercise_records if r.is_correct)
            
            exercise_mastery = (correct_exercises / total_exercises * 100) if total_exercises > 0 else 0.0
            
            # 🔥 关键修复：确保两个值都不是 None 再进行计算
            comprehensive_score = (video_mastery or 0.0) * 0.35 + (exercise_mastery or 0.0) * 0.65
            course_mastery.mastery_score = min(100.0, comprehensive_score)
            
            # 同时更新 exercise_mastery 字段
            course_mastery.exercise_mastery = exercise_mastery
            
            # 设置掌握等级（10个等级）
            level_num = int(course_mastery.mastery_score // 10)
            level_names = [
                "未学习", "入门", "初级", "基础", 
                "进阶", "中级", "良好", "熟练", 
                "优秀", "精通", "大师"
            ]
            course_mastery.level = level_names[min(level_num, 10)]

            # 刷新更新时间
            course_mastery.update_time = func.now()

        # 统一提交数据库变更
        db.flush()

    def update_video_mastery(self, db: Session, user_id: int, resource_id: int, progress: float):
        """
        更新视频学习对应的知识点掌握度
        Args:
            db: 数据库会话
            user_id: 用户ID
            resource_id: 视频资源ID
            progress: 学习进度（0-100）
        """
        # 获取视频资源关联的课程知识点
        resource = db.query(CourseResource).filter(CourseResource.id == resource_id).first()
        if not resource:
            return
        
        # 遍历关联的课程知识点
        for course_point in resource.course_knowledge_points:
            mastery = db.query(UserCourseKnowledgeMastery).filter(
                UserCourseKnowledgeMastery.user_id == user_id,
                UserCourseKnowledgeMastery.course_knowledge_id == course_point.id
            ).first()
            
            if not mastery:
                mastery = UserCourseKnowledgeMastery(
                    user_id=user_id,
                    course_knowledge_id=course_point.id,
                    mastery_score=0.0,
                    level="未学习",
                    video_mastery=0.0,
                    exercise_mastery=0.0
                )
                db.add(mastery)
            
            # 🔥 关键修复：确保 video_mastery 不为 None
            current_video_mastery = getattr(mastery, 'video_mastery', 0.0)
            if current_video_mastery is None:
                current_video_mastery = 0.0
            
            # 更新视频掌握度（取最高进度）
            new_video_mastery = max(current_video_mastery, progress)
            mastery.video_mastery = new_video_mastery
            
            # 获取习题掌握度
            from models.db_models import UserExerciseRecord
            exercise_records = db.query(UserExerciseRecord).join(
                Exercise
            ).join(
                exercise_course_knowledge_rel
            ).filter(
                exercise_course_knowledge_rel.c.course_knowledge_id == course_point.id,
                UserExerciseRecord.user_id == user_id
            ).all()
            
            total_exercises = len(exercise_records)
            correct_exercises = sum(1 for r in exercise_records if r.is_correct)
            exercise_mastery = (correct_exercises / total_exercises * 100) if total_exercises > 0 else 0.0
            
            # 🔥 关键修复：确保两个值都不是 None 再进行计算
            mastery.exercise_mastery = exercise_mastery
            comprehensive_score = (new_video_mastery or 0.0) * 0.35 + (exercise_mastery or 0.0) * 0.65
            mastery.mastery_score = min(100.0, comprehensive_score)
            
            # 设置掌握等级（10个等级）
            level_num = int(mastery.mastery_score // 10)
            level_names = [
                "未学习", "入门", "初级", "基础", 
                "进阶", "中级", "良好", "熟练", 
                "优秀", "精通", "大师"
            ]
            mastery.level = level_names[min(level_num, 10)]
            
            mastery.update_time = func.now()
        
        db.commit()

    def get_course_learning_path(self, db: Session, user_id: int, course_id: int):
        """
        基于用户画像和课程知识点，生成个性化学习路径推荐
        注意：这里只处理课程专属知识点（CourseKnowledgePoint）
        """
        # 1. 获取课程的所有课程知识点
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return {"learning_path": []}
        
        # 获取课程的专属知识点
        course_points = db.query(CourseKnowledgePoint).filter(
            CourseKnowledgePoint.course_id == course_id
        ).order_by(CourseKnowledgePoint.sort_order).all()
        
        # 2. 获取用户对这些知识点的掌握情况
        learning_path = []
        
        for point in course_points:
            mastery = db.query(UserCourseKnowledgeMastery).filter(
                UserCourseKnowledgeMastery.user_id == user_id,
                UserCourseKnowledgeMastery.course_knowledge_id == point.id
            ).first()
            
            mastery_score = mastery.mastery_score if mastery else 0.0
            video_mastery = getattr(mastery, 'video_mastery', 0.0) if mastery and hasattr(mastery, 'video_mastery') else 0.0
            exercise_mastery = getattr(mastery, 'exercise_mastery', 0.0) if mastery and hasattr(mastery, 'exercise_mastery') else 0.0
            
            # 只推荐未完全掌握的知识点（< 90分）
            if mastery_score < 90:
                # 生成个性化推荐理由
                reason = self._generate_learning_reason(mastery_score, video_mastery, exercise_mastery, point.difficulty)
                
                learning_path.append({
                    "knowledge_id": point.id,
                    "knowledge_title": point.title,
                    "difficulty": point.difficulty,
                    "mastery_score": round(mastery_score, 2),
                    "video_mastery": round(video_mastery, 2),
                    "exercise_mastery": round(exercise_mastery, 2),
                    "reason": reason,
                    "type": "course",
                    "level": mastery.level if mastery else "未学习"
                })
        
        # 3. 按掌握度排序（低的优先）
        learning_path.sort(key=lambda x: x["mastery_score"])
        
        # 4. 限制返回数量（最多10个）
        learning_path = learning_path[:10]
        
        return {"learning_path": learning_path}
    
    def _generate_learning_reason(self, mastery_score: float, video_mastery: float, exercise_mastery: float, difficulty: str) -> str:
        """
        生成个性化学习推荐理由
        """
        reasons = []
        
        # 根据掌握程度
        if mastery_score == 0:
            reasons.append("尚未开始学习")
        elif mastery_score < 30:
            reasons.append("基础薄弱，需要系统学习")
        elif mastery_score < 60:
            reasons.append("已有一定基础，但还需加强")
        elif mastery_score < 90:
            reasons.append("掌握较好，继续巩固提升")
        
        # 根据视频学习情况
        if video_mastery < 30:
            reasons.append("建议先观看教学视频")
        elif video_mastery >= 80 and exercise_mastery < 60:
            reasons.append("视频学习充分，应加强习题练习")
        
        # 根据习题情况
        if exercise_mastery < 40:
            reasons.append("习题正确率较低，需多做练习")
        elif exercise_mastery >= 70 and video_mastery < 50:
            reasons.append("习题表现不错，可回顾视频加深理解")
        
        # 根据难度
        if difficulty == "困难" and mastery_score < 50:
            reasons.append("该知识点难度较高，建议循序渐进")
        
        # 组合推荐理由
        if len(reasons) >= 2:
            return f"{'；'.join(reasons[:2])}"
        return reasons[0] if reasons else "建议继续学习以提升掌握度"

    def get_course_knowledge_mastery(self, db: Session, user_id: int, course_id: int):
        """
        获取用户对课程知识点的掌握情况统计
        注意：这里只处理课程专属知识点（CourseKnowledgePoint）
        """
        # 1. 获取课程的所有课程知识点
        course_points = db.query(CourseKnowledgePoint).filter(
            CourseKnowledgePoint.course_id == course_id
        ).order_by(CourseKnowledgePoint.sort_order).all()
        
        mastery_list = []
        
        # 处理课程专属知识点
        for point in course_points:
            mastery = db.query(UserCourseKnowledgeMastery).filter(
                UserCourseKnowledgeMastery.user_id == user_id,
                UserCourseKnowledgeMastery.course_knowledge_id == point.id
            ).first()
            
            mastery_score = mastery.mastery_score if mastery else 0.0
            video_mastery = getattr(mastery, 'video_mastery', 0.0) if mastery and hasattr(mastery, 'video_mastery') else 0.0
            exercise_mastery = getattr(mastery, 'exercise_mastery', 0.0) if mastery and hasattr(mastery, 'exercise_mastery') else 0.0
            
            # 确定掌握等级（10个等级）
            if mastery:
                level = mastery.level
            else:
                level_num = int(mastery_score // 10)
                level_names = [
                    "未学习", "入门", "初级", "基础", 
                    "进阶", "中级", "良好", "熟练", 
                    "优秀", "精通", "大师"
                ]
                level = level_names[min(level_num, 10)]
            
            mastery_list.append({
                "knowledge_id": point.id,
                "knowledge_title": point.title,
                "mastery_score": round(mastery_score, 2),
                "mastery_level": level,
                "video_mastery": round(video_mastery, 2),
                "exercise_mastery": round(exercise_mastery, 2),
                "practice_count": 0,
                "accuracy": round(exercise_mastery, 2),
                "type": "course"
            })
        
        return {"mastery_list": mastery_list}

    def generate_exercise(self, db: Session, user_id: int, knowledge_point_id: int, difficulty: str = "medium"):
        """生成练习题"""
        try:
            # 1. 获取知识点
            knowledge_point = db.query(KnowledgePoint).filter(
                KnowledgePoint.id == knowledge_point_id
            ).first()
            
            if not knowledge_point:
                raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "知识点不存在")
            
            # 2. 获取该知识点下的所有习题
            exercises = db.query(Exercise).filter(
                Exercise.knowledge_points.any(id=knowledge_point_id),
                Exercise.difficulty == difficulty
            ).all()
            
            if not exercises:
                raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "该知识点下没有习题")
            
            # 3. 随机选择一个习题
            import random
            selected_exercise = random.choice(exercises)
            
            # 4. 返回习题信息
            return {
                "id": selected_exercise.id,
                "title": selected_exercise.title,
                "type": selected_exercise.type,
                "difficulty": selected_exercise.difficulty,
                "score": selected_exercise.score,
                "course_id": selected_exercise.course_id,
                "options": [
                    {
                        "id": opt.id,
                        "option_label": opt.option_label,
                        "option_content": opt.option_content
                    } for opt in selected_exercise.options
                ]
            }
        except Exception as e:
            logger.error(f"生成练习题失败: {str(e)}")
            raise BusinessException(code=500, msg=f"生成练习题失败: {str(e)}")

    def get_wrong_question_list(self, db: Session, user_id: int, page: int = 1, size: int = 10):
        """获取用户错题本列表"""
        try:
            query = db.query(WrongQuestion).filter(
                WrongQuestion.user_id == user_id
            ).order_by(WrongQuestion.last_wrong_time.desc().nullslast())
            
            total = query.count()
            
            # 如果总数为0，直接返回
            if total == 0:
                return {
                    "code": 0,
                    "msg": "获取错题列表成功",
                    "data": {
                        "total": 0,
                        "items": [],
                        "page": page,
                        "size": size
                    }
                }
            
            items = query.offset((page - 1) * size).limit(size).all()
            
            wrong_list = []
            for item in items:
                # 获取习题信息
                exercise = db.query(Exercise).filter(Exercise.id == item.exercise_id).first()
                course = None
                
                if exercise:
                    # Exercise 有 course_id 字段，直接获取课程
                    course = db.query(Course).filter(Course.id == exercise.course_id).first()
                
                # 获取习题选项（从 ExerciseOption 表）
                options_data = []
                if exercise and exercise.options:
                    for opt in exercise.options:
                        options_data.append({
                            "id": opt.option_label,
                            "option_label": opt.option_label,
                            "option_content": opt.option_content,
                            "is_correct": opt.is_correct
                        })
                
                # 安全转换时间字段
                def safe_isoformat(dt_value):
                    if dt_value is None:
                        return None
                    if isinstance(dt_value, str):
                        return dt_value
                    try:
                        return dt_value.isoformat()
                    except Exception:
                        return None
                
                wrong_data = {
                    "id": item.id,
                    "exercise_id": item.exercise_id,
                    "exercise_title": exercise.title if exercise else "未知习题",
                    "course_title": course.title if course else "未知课程",
                    "question_content": item.question_title or (exercise.title if exercise else ""),
                    "user_answer": item.user_answer,
                    "correct_answer": item.correct_answer,
                    "difficulty": exercise.difficulty if exercise else "medium",
                    "type": exercise.type if exercise else "short_answer",
                    "options": options_data,
                    "explanation": exercise.analysis if exercise else "",
                    "error_reason": item.error_reason,
                    "wrong_count": item.wrong_count,
                    "master_level": item.master_level,
                    "practice_count": item.wrong_count,
                    "is_mastered": item.master_level >= 3 if item.master_level else False,
                    "create_time": safe_isoformat(item.create_time),
                    "last_wrong_time": safe_isoformat(item.last_wrong_time)
                }
                wrong_list.append(wrong_data)
            
            return {
                "code": 0,
                "msg": "获取错题列表成功",
                "data": {
                    "total": total,
                    "items": wrong_list,
                    "page": page,
                    "size": size
                }
            }
        except TypeError as e:
            logger.warning(f"时间字段格式错误，返回空列表: {str(e)}")
            return {
                "code": 0,
                "msg": "暂无错题数据",
                "data": {
                    "total": 0,
                    "items": [],
                    "page": page,
                    "size": size
                }
            }
        except Exception as e:
            logger.error(f"获取错题列表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "code": 500,
                "msg": f"获取错题列表失败",
                "data": {
                    "total": 0,
                    "items": [],
                    "page": page,
                    "size": size
                }
            }

    def mark_wrong_mastered(self, db: Session, user_id: int, wrong_id: int):
        """标记错题为已掌握"""
        from datetime import datetime, timedelta
        
        # 使用原生 SQL 查询，避免 ORM 时间转换问题
        result = db.execute(
            text("SELECT id, user_id FROM wrong_question WHERE id = :wrong_id AND user_id = :user_id"),
            {"wrong_id": wrong_id, "user_id": user_id}
        ).first()
        
        if not result:
            raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "错题不存在")
        
        # 直接执行更新 SQL
        next_review = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            text("UPDATE wrong_question SET master_level = 3, next_review_time = :next_review, update_time = CURRENT_TIMESTAMP WHERE id = :wrong_id"),
            {"next_review": next_review, "wrong_id": wrong_id}
        )
        
        db.commit()
        return {"code": 0, "msg": "标记成功", "data": {"id": wrong_id}}

    def remove_wrong_question(self, db: Session, user_id: int, wrong_id: int):
        """从错题本移除题目"""
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_id,
            WrongQuestion.user_id == user_id
        ).first()
        
        if not wrong:
            raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "错题不存在")
        
        db.delete(wrong)
        db.commit()
        return {"code": 0, "msg": "移除成功", "data": {"id": wrong_id}}

    async def generate_special_practice(self, db: Session, user_id: int, wrong_id: int = None, point_id: int = None):
        """
        基于错题或知识点生成专项练习题（使用大模型）
        :param db: 数据库会话
        :param user_id: 用户ID
        :param wrong_id: 错题ID（可选）
        :param point_id: 知识点ID（可选）
        :return: 生成的练习题
        """
        try:
            # 1. 确定练习目标（错题或知识点）
            target_content = ""
            target_type = ""
            
            if wrong_id:
                # 基于错题生成
                wrong = db.query(WrongQuestion).filter(
                    WrongQuestion.id == wrong_id,
                    WrongQuestion.user_id == user_id
                ).first()
                
                if not wrong:
                    raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "错题不存在")
                
                exercise = db.query(Exercise).filter(Exercise.id == wrong.exercise_id).first()
                if exercise:
                    target_content = f"错题题目：{exercise.title}\n错题内容：{wrong.question_title}\n用户答案：{wrong.user_answer}\n正确答案：{wrong.correct_answer}"
                    target_type = "wrong_exercise"
                else:
                    target_content = f"错题记录：{wrong.question_title}\n用户答案：{wrong.user_answer}\n正确答案：{wrong.correct_answer}"
                    target_type = "wrong_record"
                    
            elif point_id:
                # 基于知识点生成
                knowledge_point = db.query(KnowledgePoint).filter(
                    KnowledgePoint.id == point_id
                ).first()
                
                if not knowledge_point:
                    raise BusinessException(BusinessErrorCode.DOC_NOT_EXIST, "知识点不存在")
                
                target_content = f"知识点标题：{knowledge_point.title}\n知识点内容：{knowledge_point.content}"
                target_type = "knowledge_point"
            else:
                raise BusinessException(code=400, msg="请提供错题ID或知识点ID")
            
            # 2. 获取用户画像，了解用户水平
            user_profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            preferred_difficulty = "中等"
            if user_profile and user_profile.preferred_difficulty:
                preferred_difficulty = user_profile.preferred_difficulty
            
            # 3. 调用大模型生成练习题
            json_example = '''{
    "question": "这里写完整的题目描述，包括所有条件、场景、数据等详细信息。题目要具体明确，不能太简短。",
    "type": "single_choice",
    "difficulty": "中等",
    "options": [
        {"option_label": "A", "option_content": "选项A的完整详细描述", "is_correct": true},
        {"option_label": "B", "option_content": "选项B的完整详细描述", "is_correct": false},
        {"option_label": "C", "option_content": "选项C的完整详细描述", "is_correct": false},
        {"option_label": "D", "option_content": "选项D的完整详细描述", "is_correct": false}
    ],
    "correct_answer": "A",
    "analysis": "这里是详细的答案解析，至少100字，说明解题思路、知识点应用、为什么其他选项不对等"
}'''

            prompt = """
你是一个专业的教育AI助手。请根据以下内容为用户生成一道专项练习题：

【练习目标】
""" + target_content + """

【用户偏好难度】
""" + preferred_difficulty + """

【重要要求】
1. 必须生成一道完整的单选题或判断题
2. 题目描述要详细完整，包含所有必要的条件和信息
3. 题干长度不少于50个字，确保题目清晰明确
4. 提供4个选项（如果是单选题）或2个选项（如果是判断题）
5. 每个选项的内容也要完整详细
6. 明确指出正确答案
7. 提供详细的解析，说明为什么选这个答案

【输出格式】
请严格按照以下JSON格式输出，不要包含```

```
{
    "question": "这里写完整的题目描述，包括所有条件、场景、数据等详细信息。题目要具体明确，不能太简短。",
    "type": "single_choice",
    "difficulty": "{preferred_difficulty}",
    "options": [
        {{"option_label": "A", "option_content": "选项A的完整详细描述", "is_correct": true}},
        {{"option_label": "B", "option_content": "选项B的完整详细描述", "is_correct": false}},
        {{"option_label": "C", "option_content": "选项C的完整详细描述", "is_correct": false}},
        {{"option_label": "D", "option_content": "选项D的完整详细描述", "is_correct": false}}
    ],
    "correct_answer": "A",
    "analysis": "这里是详细的答案解析，至少100字，说明解题思路、知识点应用、为什么其他选项不对等"
}

【示例】
好的题目应该是这样的：
"在Python编程中，关于列表(list)和元组(tuple)的区别，下列说法正确的是：列表是可变序列，支持增删改操作；而元组是不可变序列，创建后不能修改。在实际应用中，如果需要存储一组不会改变的数据（如坐标点、配置项等），应该使用哪种数据结构？"

而不是这样（太简短）：
"列表和元组的区别是什么？"

请现在开始生成题目：
"""
            
            # 调用大模型
            response = await llm.chat(prompt, timeout=60)
            logger.info(f"大模型原始响应长度: {len(response)}")
            logger.info(f"大模型原始响应前500字符: {response[:500]}")

            # 4. 解析大模型返回的JSON
            import json
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    exercise_data = json.loads(json_match.group())
                    logger.info(f"解析成功，题目长度: {len(exercise_data.get('question', ''))}")
                    logger.info(f"题目内容: {exercise_data.get('question', '')[:200]}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    logger.error(f"原始响应: {response[:500]}")
                    exercise_data = None
            else:
                logger.warning("未找到JSON格式数据")
                logger.error(f"原始响应: {response[:500]}")
                exercise_data = None
            
            # 如果解析失败，使用默认数据
            if not exercise_data:
                exercise_data = {
                    "question": f"针对以下内容的练习题：\n{target_content[:300]}",
                    "type": "single_choice",
                    "difficulty": preferred_difficulty,
                    "options": [
                        {"option_label": "A", "option_content": "选项A", "is_correct": True},
                        {"option_label": "B", "option_content": "选项B", "is_correct": False},
                        {"option_label": "C", "option_content": "选项C", "is_correct": False},
                        {"option_label": "D", "option_content": "选项D", "is_correct": False}
                    ],
                    "correct_answer": "A",
                    "analysis": response[:500]
                }
            
            # 验证题目完整性
            question_text = exercise_data.get('question', '')
            if len(question_text) < 30:
                logger.warning(f"题目过短({len(question_text)}字符)，可能需要重新生成")
            
            # 5. 返回生成的练习题
            return {
                "target_type": target_type,
                "target_id": wrong_id or point_id,
                "exercise": exercise_data,
                "difficulty": preferred_difficulty
            }

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"生成专项练习失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise BusinessException(code=500, msg=f"生成练习题失败: {str(e)}")


user_course_service = UserCourseService()