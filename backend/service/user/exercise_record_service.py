"""
用户答题记录业务服务
功能：提交答题、自动判分、保存记录、更新掌握度、自动加入错题本
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.db_models import (
    Exercise, UserExerciseRecord, WrongQuestion,
    UserKnowledgeMastery, KnowledgePoint
)
from models.schemas import ExerciseSubmitRequest
from utils.logger import logger
from utils.response import BusinessException, BusinessErrorCode


class ExerciseRecordService:

    def submit_answer(self, db: Session, user_id: int, data: ExerciseSubmitRequest):
        """提交答题并处理结果"""
        # 1. 获取习题信息
        exercise = db.query(Exercise).filter(Exercise.id == data.exercise_id).first()
        if not exercise:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "习题不存在")

        # 2. 自动判分
        is_correct = self._check_answer(data.user_answer, exercise.answer)
        score = exercise.score if is_correct else 0.0

        # 3. 保存答题记录
        record = UserExerciseRecord(
            user_id=user_id,
            exercise_id=data.exercise_id,
            user_answer=data.user_answer,
            score=score,
            is_correct=is_correct,
            answer_time=data.answer_time
        )
        db.add(record)
        db.flush()

        # 4. 答错自动加入错题本
        if not is_correct:
            self._add_to_wrong_question(db, user_id, exercise, data.user_answer)

        # 5. 更新知识点掌握度
        self._update_knowledge_mastery(db, user_id, exercise, is_correct)

        db.commit()
        logger.info(f"用户 {user_id} 完成答题，习题ID: {data.exercise_id}, 结果: {'正确' if is_correct else '错误'}")

        # 🔥 新增：6. 更新用户画像（供大模型推荐系统使用）
        try:
            from service.user.user_profile_service import user_profile_service
            user_profile_service.update_profile_after_answer(user_id, db)
            logger.info(f"用户 {user_id} 画像已更新")
        except Exception as e:
            logger.warning(f"⚠️ 更新用户画像失败: {e}，不影响答题功能")

        # 7. 返回结果
        return {
            "exercise_id": data.exercise_id,
            "is_correct": is_correct,
            "user_answer": data.user_answer,
            "correct_answer": exercise.answer,
            "score": score,
            "analysis": exercise.analysis
        }

    def _check_answer(self, user_answer: str, correct_answer: str) -> bool:
        """校验答案（支持单选、多选、判断）"""
        if not user_answer or not correct_answer:
            return False

        # 统一转为大写并去重排序
        user = ''.join(sorted(set(user_answer.upper().strip())))
        correct = ''.join(sorted(set(correct_answer.upper().strip())))

        return user == correct

    def _add_to_wrong_question(self, db: Session, user_id: int, exercise: Exercise, user_answer: str):
        """自动加入错题本，已存在则更新错误次数和复习时间"""
        # 直接用SQL查询关联表，不依赖模型
        result = db.execute(
            text("SELECT knowledge_point_id FROM exercise_knowledge WHERE exercise_id = :eid"),
            {"eid": exercise.id}
        ).fetchone()

        if not result:
            logger.warning(f"⚠️ 习题 {exercise.id} 没有关联知识点，跳过加入错题本")
            return

        point_id = result[0]
        logger.info(f"习题 {exercise.id} 关联的知识点ID: {point_id}")

        # 检查是否已在错题本（按用户ID+知识点ID查询）
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == user_id,
            WrongQuestion.point_id == point_id
        ).first()

        if wrong:
            # 已存在：错误次数+1，更新复习时间
            wrong.wrong_count += 1
            wrong.master_level = 0
            wrong.user_answer = user_answer
            wrong.last_review_time = datetime.now()
            # 艾宾浩斯复习间隔：1天→3天→7天→14天→30天
            intervals = [1, 3, 7, 14, 30]
            interval = intervals[min(wrong.wrong_count - 1, len(intervals) - 1)]
            wrong.next_review_time = datetime.now() + timedelta(days=interval)
        else:
            # 新增错题
            wrong = WrongQuestion(
                user_id=user_id,
                point_id=point_id,
                question=exercise.title,
                user_answer=user_answer,
                correct_answer=exercise.answer,
                master_level=0,
                wrong_count=1,
                next_review_time=datetime.now() + timedelta(days=1)
            )
            db.add(wrong)

    def _update_knowledge_mastery(self, db: Session, user_id: int, exercise: Exercise, is_correct: bool):
        """更新用户对知识点的掌握度"""
        # 直接用SQL查询关联表，不依赖模型
        results = db.execute(
            text("SELECT knowledge_point_id FROM exercise_knowledge WHERE exercise_id = :eid"),
            {"eid": exercise.id}
        ).fetchall()

        for row in results:
            kp_id = row[0]

            # 查询现有掌握度记录
            mastery = db.query(UserKnowledgeMastery).filter(
                UserKnowledgeMastery.user_id == user_id,
                UserKnowledgeMastery.knowledge_point_id == kp_id
            ).first()

            if not mastery:
                # 新建掌握度记录
                mastery = UserKnowledgeMastery(
                    user_id=user_id,
                    knowledge_point_id=kp_id,
                    mastery_score=0.0,
                    level="未掌握",
                    total_questions=0,
                    correct_questions=0
                )
                db.add(mastery)

            # 更新统计
            mastery.total_questions += 1
            if is_correct:
                mastery.correct_questions += 1
                mastery.mastery_score = min(mastery.mastery_score + 10, 100)  # 答对+10分
            else:
                mastery.mastery_score = max(mastery.mastery_score - 5, 0)  # 答错-5分

            # 更新掌握等级
            if mastery.mastery_score >= 90:
                mastery.level = "精通"
            elif mastery.mastery_score >= 70:
                mastery.level = "熟练掌握"
            elif mastery.mastery_score >= 40:
                mastery.level = "初步掌握"
            else:
                mastery.level = "未掌握"

            mastery.last_answer_time = datetime.now()

    def get_user_records(self, db: Session, user_id: int, page: int = 1, size: int = 10):
        """获取用户答题记录"""
        query = db.query(UserExerciseRecord).filter(UserExerciseRecord.user_id == user_id)
        total = query.count()
        records = query.order_by(UserExerciseRecord.create_time.desc()).offset((page-1)*size).limit(size).all()

        # 修复：添加exercise_title字段，适配响应模型
        result_list = []
        for record in records:
            exercise = db.query(Exercise).filter(Exercise.id == record.exercise_id).first()
            result_list.append({
                "id": record.id,
                "exercise_id": record.exercise_id,
                "exercise_title": exercise.title if exercise else "习题已删除",
                "user_answer": record.user_answer,
                "correct_answer": exercise.answer if exercise else "",
                "is_correct": record.is_correct,
                "score": record.score,
                "answer_time": record.answer_time,
                "create_time": record.create_time
            })

        return {"total": total, "list": result_list, "page": page, "size": size}

    def get_wrong_questions(self, db: Session, user_id: int, page: int = 1, size: int = 10):
        """获取用户错题本"""
        query = db.query(WrongQuestion).filter(WrongQuestion.user_id == user_id)
        total = query.count()
        wrongs = query.order_by(WrongQuestion.create_time.desc()).offset((page-1)*size).limit(size).all()

        result_list = []
        for w in wrongs:
            result_list.append({
                "id": w.id,
                "exercise_id": 0,  # 错题表里没有exercise_id，填0
                "exercise_title": w.question,
                "user_answer": w.user_answer,
                "correct_answer": w.correct_answer,
                "error_reason": w.error_reason,
                "master_level": w.master_level,
                "wrong_count": w.wrong_count,
                "last_review_time": w.last_review_time,
                "next_review_time": w.next_review_time,
                "create_time": w.create_time
            })

        return {"total": total, "list": result_list, "page": page, "size": size}

    def mark_wrong_mastered(self, db: Session, user_id: int, wrong_id: int):
        """标记错题已掌握"""
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_id,
            WrongQuestion.user_id == user_id
        ).first()

        if not wrong:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "错题不存在")

        wrong.master_level = 2
        wrong.next_review_time = None
        db.commit()

    def remove_wrong_question(self, db: Session, user_id: int, wrong_id: int):
        """移除错题"""
        wrong = db.query(WrongQuestion).filter(
            WrongQuestion.id == wrong_id,
            WrongQuestion.user_id == user_id
        ).first()

        if not wrong:
            raise BusinessException(BusinessErrorCode.PARAM_ERROR, "错题不存在")

        db.delete(wrong)
        db.commit()


exercise_record_service = ExerciseRecordService()