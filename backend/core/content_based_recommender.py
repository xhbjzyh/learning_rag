
"""
基于内容的推荐引擎
通过课程特征（标签、分类、难度等）计算相似度
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from collections import defaultdict

from models.db_models import (
    Course, CourseTag, CourseTagRel, CourseCategory,
    CourseSimilarity, KnowledgePoint, CourseResource
)
from utils.logger import logger


class ContentBasedRecommender:
    """基于内容的推荐引擎"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_course_similarities(self):
        """计算所有课程的相似度矩阵"""
        logger.info("开始计算课程相似度...")

        courses = self.db.query(Course).filter(
            Course.is_published == True
        ).all()

        if len(courses) < 2:
            logger.warning("课程数量不足，无法计算相似度")
            return

        # 两两计算相似度
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                course1 = courses[i]
                course2 = courses[j]

                similarity = self._calculate_course_similarity(course1, course2)

                # 只保存相似度 > 0.2 的课程对
                if similarity < 0.2:
                    continue

                # 保存或更新
                self._save_course_similarity(
                    course1.id, course2.id, similarity
                )

        logger.info(f"课程相似度计算完成，共 {len(courses)} 个课程")

    def _calculate_course_similarity(self, course1: Course, course2: Course) -> float:
        """
        计算两个课程的相似度
        综合考虑：标签相似度、分类相似度、难度相似度
        """
        # 1. 标签相似度（权重 0.5）
        tag_similarity = self._calculate_tag_similarity(course1, course2)

        # 2. 分类相似度（权重 0.3）
        category_similarity = self._calculate_category_similarity(course1, course2)

        # 3. 难度相似度（权重 0.2）
        difficulty_similarity = self._calculate_difficulty_similarity(course1, course2)

        # 综合相似度
        total_similarity = (
                0.5 * tag_similarity +
                0.3 * category_similarity +
                0.2 * difficulty_similarity
        )

        return round(total_similarity, 4)

    def _calculate_tag_similarity(self, course1: Course, course2: Course) -> float:
        """计算标签相似度（Jaccard相似系数）"""
        tags1 = set(tag.id for tag in course1.tags)
        tags2 = set(tag.id for tag in course2.tags)

        if not tags1 or not tags2:
            return 0.0

        intersection = tags1 & tags2
        union = tags1 | tags2

        return len(intersection) / len(union)

    def _calculate_category_similarity(self, course1: Course, course2: Course) -> float:
        """计算分类相似度"""
        if course1.category_id == course2.category_id:
            return 1.0

        # 检查是否有父子关系
        cat1 = self.db.query(CourseCategory).filter(
            CourseCategory.id == course1.category_id
        ).first()

        cat2 = self.db.query(CourseCategory).filter(
            CourseCategory.id == course2.category_id
        ).first()

        if not cat1 or not cat2:
            return 0.0

        # 同一父分类
        if cat1.parent_id == cat2.parent_id and cat1.parent_id != 0:
            return 0.7

        # 一级分类相同
        if cat1.level == 1 and cat2.level == 1:
            return 0.3

        return 0.0

    def _calculate_difficulty_similarity(self, course1: Course, course2: Course) -> float:
        """计算难度相似度"""
        difficulty_levels = {
            '简单': 1,
            '中等': 2,
            '困难': 3
        }

        level1 = difficulty_levels.get(course1.difficulty, 2)
        level2 = difficulty_levels.get(course2.difficulty, 2)

        # 难度差值越小，相似度越高
        diff = abs(level1 - level2)

        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.6
        else:
            return 0.2

    def _save_course_similarity(self, course_id1: int, course_id2: int, similarity: float):
        """保存课程相似度到数据库"""
        from datetime import datetime

        # 检查是否已存在
        existing = self.db.query(CourseSimilarity).filter(
            ((CourseSimilarity.course_id1 == course_id1) &
             (CourseSimilarity.course_id2 == course_id2)) |
            ((CourseSimilarity.course_id1 == course_id2) &
             (CourseSimilarity.course_id2 == course_id1))
        ).first()

        if existing:
            existing.similarity = similarity
            existing.update_time = datetime.now()
        else:
            new_similarity = CourseSimilarity(
                course_id1=course_id1,
                course_id2=course_id2,
                similarity=similarity
            )
            self.db.add(new_similarity)

        self.db.commit()

    def recommend_similar_courses(
            self,
            course_id: int,
            user_id: int,
            limit: int = 5
    ) -> List[Dict]:
        """
        推荐与指定课程相似的课程
        排除用户已学习的课程
        """
        # 1. 获取相似课程
        similarities = self.db.query(CourseSimilarity).filter(
            (CourseSimilarity.course_id1 == course_id) |
            (CourseSimilarity.course_id2 == course_id)
        ).order_by(
            CourseSimilarity.similarity.desc()
        ).limit(limit * 2).all()

        # 2. 获取用户已学习的课程
        user_courses = set(
            row[0] for row in self.db.query(CourseSimilarity.course_id1).join(
                Course, Course.id == CourseSimilarity.course_id1
            ).filter(
                CourseSimilarity.course_id1 == course_id
            ).all()
        )

        # 3. 过滤并返回推荐
        recommendations = []
        for sim in similarities:
            other_course_id = (
                sim.course_id2
                if sim.course_id1 == course_id
                else sim.course_id1
            )

            # 排除已学习的课程
            if other_course_id in user_courses:
                continue

            course = self.db.query(Course).filter(
                Course.id == other_course_id
            ).first()

            if course:
                recommendations.append({
                    'course_id': other_course_id,
                    'course_title': course.title,
                    'similarity': sim.similarity,
                    'reason': f'与您正在学习的课程内容相似',
                    'recommend_type': 'content_based'
                })

            if len(recommendations) >= limit:
                break

        return recommendations

    def recommend_by_user_profile(
            self,
            user_id: int,
            limit: int = 10
    ) -> List[Dict]:
        """
        基于用户画像的推荐
        根据用户的学习偏好推荐课程
        """
        from models.db_models import UserLearningPreference, UserInterestTag

        # 1. 获取用户学习偏好
        preference = self.db.query(UserLearningPreference).filter(
            UserLearningPreference.user_id == user_id
        ).first()

        if not preference:
            return self._get_popular_courses(limit)

        # 2. 获取用户兴趣标签
        interest_tags = self.db.query(UserInterestTag).filter(
            UserInterestTag.user_id == user_id
        ).order_by(
            UserInterestTag.weight.desc()
        ).limit(10).all()

        if not interest_tags:
            return self._get_popular_courses(limit)

        # 3. 基于兴趣标签推荐课程
        tag_ids = [t.tag_id for t in interest_tags]

        courses_with_tags = self.db.query(Course).join(
            CourseTagRel, Course.id == CourseTagRel.course_id
        ).filter(
            CourseTagRel.tag_id.in_(tag_ids),
            Course.is_published == True
        ).distinct().limit(limit * 2).all()

        # 4. 排除已学习的课程
        user_courses = set(
            row[0] for row in self.db.query(Course.id).join(
                Course, Course.id == Course.id
            ).all()
        )

        recommendations = []
        for course in courses_with_tags:
            if course.id not in user_courses:
                recommendations.append({
                    'course_id': course.id,
                    'course_title': course.title,
                    'score': 0.7,
                    'reason': f'根据您的学习兴趣推荐',
                    'recommend_type': 'profile_based'
                })

            if len(recommendations) >= limit:
                break

        return recommendations if recommendations else self._get_popular_courses(limit)

    def _get_popular_courses(self, limit: int) -> List[Dict]:
        """获取热门课程（兜底推荐）"""
        courses = self.db.query(Course).filter(
            Course.is_published == True
        ).order_by(
            Course.view_count.desc()
        ).limit(limit).all()

        return [
            {
                'course_id': course.id,
                'course_title': course.title,
                'score': 0.5,
                'reason': '热门课程推荐',
                'recommend_type': 'popular'
            }
            for course in courses
        ]
