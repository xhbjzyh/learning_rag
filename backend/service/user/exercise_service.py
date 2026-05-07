"""
习题模块业务服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete

from models.db_models import Exercise, ExerciseOption, KnowledgePoint
from models.schemas import ExerciseCreate, ExerciseUpdate
from utils.logger import logger
from utils.response import BusinessException, BusinessErrorCode


class ExerciseService:

    def get_list(self, db: Session, page: int = 1, size: int = 10, keyword: Optional[str] = None):
        """习题分页列表"""
        q = db.query(Exercise)
        if keyword:
            q = q.filter(Exercise.title.like(f"%{keyword}%"))
        total = q.count()
        rows = q.order_by(Exercise.create_time.desc()).offset((page-1)*size).limit(size).all()
        return {"total": total, "list": rows, "page": page, "size": size}

    def get_detail(self, db: Session, exercise_id: int):
        """习题详情（带选项）"""
        ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not ex:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")
        return ex

    def create_exercise(self, db: Session, data: ExerciseCreate, create_user_id: int):
        """新增习题 + 选项 + 关联知识点"""
        # 🔥 修复1：先计算正确答案，再创建习题
        correct_answer = ""
        for index, opt in enumerate(data.options):
            if opt.is_correct:
                if len(opt.option_label) == 1 and opt.option_label.isalpha():
                    correct_answer += opt.option_label.upper()
                else:
                    correct_answer += chr(ord('A') + index)

        # 🔥 修复2：创建习题时直接传入answer，不再是None
        new_ex = Exercise(
            title=data.title,
            type=data.exercise_type.value,
            difficulty=data.difficulty,
            analysis=data.analysis,
            create_user_id=create_user_id,
            answer=correct_answer  # 🔥 这里直接赋值
        )
        db.add(new_ex)
        db.flush()  # 现在flush时answer有值了，不会报错

        # 批量新增选项
        for index, opt in enumerate(data.options):
            order = index + 1
            if len(opt.option_label) == 1 and opt.option_label.isalpha():
                label = opt.option_label.upper()
            else:
                label = chr(ord('A') + index)

            db.add(ExerciseOption(
                exercise_id=new_ex.id,
                content=opt.option_content,
                is_correct=opt.is_correct,
                order=order
            ))

        # 绑定知识点
        for kid in data.knowledge_ids:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kid).first()
            if kp:
                new_ex.knowledge_points.append(kp)

        db.commit()
        logger.info(f"新增习题成功 id:{new_ex.id}, 创建人:{create_user_id}")
        return new_ex.id

    def update_exercise(self, db: Session, data: ExerciseUpdate):
        """编辑习题：删旧选项、旧关联，重新新增"""
        ex = db.query(Exercise).filter(Exercise.id == data.id).first()
        if not ex:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")

        # 🔥 修复：先计算新的正确答案
        correct_answer = ""
        for index, opt in enumerate(data.options):
            if opt.is_correct:
                if len(opt.option_label) == 1 and opt.option_label.isalpha():
                    correct_answer += opt.option_label.upper()
                else:
                    correct_answer += chr(ord('A') + index)

        # 更新主表
        ex.title = data.title
        ex.type = data.exercise_type.value
        ex.difficulty = data.difficulty
        ex.analysis = data.analysis
        ex.answer = correct_answer  # 🔥 更新answer

        # 删除旧选项
        db.execute(delete(ExerciseOption).where(ExerciseOption.exercise_id == data.id))

        # 清空旧知识点关联
        ex.knowledge_points.clear()

        # 新增新选项
        for index, opt in enumerate(data.options):
            order = index + 1
            if len(opt.option_label) == 1 and opt.option_label.isalpha():
                label = opt.option_label.upper()
            else:
                label = chr(ord('A') + index)

            db.add(ExerciseOption(
                exercise_id=data.id,
                content=opt.option_content,
                is_correct=opt.is_correct,
                order=order
            ))

        # 新增知识点关联
        for kid in data.knowledge_ids:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kid).first()
            if kp:
                ex.knowledge_points.append(kp)

        db.commit()
        logger.info(f"编辑习题成功 id:{data.id}")
        return True

    def delete_exercise(self, db: Session, exercise_id: int):
        """删除习题级联删选项、关联"""
        ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not ex:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")

        db.execute(delete(ExerciseOption).where(ExerciseOption.exercise_id == exercise_id))
        db.delete(ex)
        db.commit()
        logger.info(f"删除习题成功 id:{exercise_id}")
        return True


exercise_service = ExerciseService()
"""
习题模块业务服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete

from models.db_models import (
    Exercise, ExerciseOption, KnowledgePoint,
    UserExerciseRecord, UserKnowledgeMastery
)
from models.schemas import ExerciseCreate, ExerciseUpdate
from utils.logger import logger
from utils.response import BusinessException, BusinessErrorCode


class ExerciseService:

    def get_list(self, db: Session, page: int = 1, size: int = 10, keyword: Optional[str] = None):
        q = db.query(Exercise)
        if keyword:
            q = q.filter(Exercise.title.like(f"%{keyword}%"))
        total = q.count()
        rows = q.order_by(Exercise.create_time.desc()).offset((page - 1) * size).limit(size).all()
        return {"total": total, "list": rows, "page": page, "size": size}

    def get_detail(self, db: Session, exercise_id: int):
        ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not ex:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")
        return ex

    def create_exercise(self, db: Session, data: ExerciseCreate, create_user_id: int):
        correct_answer = ""
        for index, opt in enumerate(data.options):
            if opt.is_correct:
                if len(opt.option_label) == 1 and opt.option_label.isalpha():
                    correct_answer += opt.option_label.upper()
                else:
                    correct_answer += chr(ord('A') + index)

        new_ex = Exercise(
            title=data.title,
            type=data.exercise_type.value,
            difficulty=data.difficulty,
            analysis=data.analysis,
            create_user_id=create_user_id,
            answer=correct_answer
        )
        db.add(new_ex)
        db.flush()

        for index, opt in enumerate(data.options):
            order = index + 1
            if len(opt.option_label) == 1 and opt.option_label.isalpha():
                label = opt.option_label.upper()
            else:
                label = chr(ord('A') + index)

            db.add(ExerciseOption(
                exercise_id=new_ex.id,
                content=opt.option_content,
                is_correct=opt.is_correct,
                order=order
            ))

        for kid in data.knowledge_ids:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kid).first()
            if kp:
                new_ex.knowledge_points.append(kp)

        db.commit()
        logger.info(f"新增习题成功 id:{new_ex.id}, 创建人:{create_user_id}")
        return new_ex.id

    def update_exercise(self, db: Session, data: ExerciseUpdate):
        ex = db.query(Exercise).filter(Exercise.id == data.id).first()
        if not ex:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")

        correct_answer = ""
        for index, opt in enumerate(data.options):
            if opt.is_correct:
                if len(opt.option_label) == 1 and opt.option_label.isalpha():
                    correct_answer += opt.option_label.upper()
                else:
                    correct_answer += chr(ord('A') + index)

        ex.title = data.title
        ex.type = data.exercise_type.value
        ex.difficulty = data.difficulty
        ex.analysis = data.analysis
        ex.answer = correct_answer

        db.execute(delete(ExerciseOption).where(ExerciseOption.exercise_id == data.id))
        ex.knowledge_points.clear()

        for index, opt in enumerate(data.options):
            order = index + 1
            if len(opt.option_label) == 1 and opt.option_label.isalpha():
                label = opt.option_label.upper()
            else:
                label = chr(ord('A') + index)

            db.add(ExerciseOption(
                exercise_id=data.id,
                content=opt.option_content,
                is_correct=opt.is_correct,
                order=order
            ))

        for kid in data.knowledge_ids:
            kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kid).first()
            if kp:
                ex.knowledge_points.append(kp)

        db.commit()
        logger.info(f"编辑习题成功 id:{data.id}")
        return True

    def delete_exercise(self, db: Session, exercise_id: int):
        ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not ex:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")

        db.execute(delete(ExerciseOption).where(ExerciseOption.exercise_id == exercise_id))
        db.delete(ex)
        db.commit()
        logger.info(f"删除习题成功 id:{exercise_id}")
        return True

    # ==============================================
    # 🔥 新增：提交答题 + 更新掌握度
    # ==============================================
    def submit_answer(
            self,
            db: Session,
            exercise_id: int,
            user_answer: str,
            user_id: int,
            answer_time: int = None
    ):
        """
        提交答题并更新知识点掌握度
        :param db: 数据库会话
        :param exercise_id: 习题ID
        :param user_answer: 用户答案
        :param user_id: 用户ID
        :param answer_time: 答题时长（秒）
        :return: 答题结果
        """
        # 1. 获取习题
        exercise = self.get_detail(db, exercise_id)

        # 2. 判断是否正确
        is_correct = (user_answer.strip().upper() == exercise.answer.strip().upper())
        score = exercise.score if is_correct else 0.0

        # 3. 保存答题记录
        record = UserExerciseRecord(
            user_id=user_id,
            exercise_id=exercise_id,
            user_answer=user_answer,
            score=score,
            is_correct=is_correct,
            answer_time=answer_time
        )
        db.add(record)

        # 4. 更新关联知识点的掌握度
        for kp in exercise.knowledge_points:
            self._update_mastery(db, user_id, kp.id, is_correct)

        db.commit()
        logger.info(f"用户 {user_id} 提交答题: 习题{exercise_id}, 结果: {'正确' if is_correct else '错误'}")

        return {
            "is_correct": is_correct,
            "score": score,
            "correct_answer": exercise.answer,
            "analysis": exercise.analysis
        }

    def _update_mastery(self, db: Session, user_id: int, point_id: int, is_correct: bool):
        """更新知识点掌握度"""
        # 1. 获取或创建掌握度记录
        mastery = db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.knowledge_point_id == point_id
        ).first()

        if not mastery:
            mastery = UserKnowledgeMastery(
                user_id=user_id,
                knowledge_point_id=point_id,
                mastery_score=0.0,
                level="未掌握",
                total_questions=0,
                correct_questions=0
            )
            db.add(mastery)

        # 2. 更新统计
        mastery.total_questions += 1
        if is_correct:
            mastery.correct_questions += 1

        # 3. 计算掌握度得分
        mastery.mastery_score = (mastery.correct_questions / mastery.total_questions) * 100

        # 4. 更新等级
        if mastery.mastery_score >= 90:
            mastery.level = "精通"
        elif mastery.mastery_score >= 70:
            mastery.level = "熟练掌握"
        elif mastery.mastery_score >= 40:
            mastery.level = "初步掌握"
        else:
            mastery.level = "未掌握"

        logger.info(f"更新掌握度: 用户{user_id} 知识点{point_id} 得分{mastery.mastery_score:.1f} 等级{mastery.level}")


exercise_service = ExerciseService()