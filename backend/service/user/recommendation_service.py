
"""
个性化推荐服务
基于用户问题和用户画像，推荐相关课程和学习资源
"""
from sqlalchemy.orm import Session
from typing import List, Dict
from models.db_models import Course, CourseCategory, SysUser, UserProfile
from utils.logger import logger


class RecommendationService:
    """推荐服务类"""

    # 学习相关的关键词映射
    LEARNING_KEYWORDS = {
        "入门": ["入门", "基础", "初学者", "新手", "开始", "从零"],
        "进阶": ["进阶", "提高", "深入", "高级", "精通", "提升"],
        "算法": ["算法", "数据结构", "排序", "查找", "图论", "动态规划"],
        "编程": ["编程", "代码", "开发", "程序设计", "软件工程"],
        "机器学习": ["机器学习", "深度学习", "AI", "人工智能", "神经网络"],
        "数据库": ["数据库", "SQL", "MySQL", "PostgreSQL", "数据存储"],
        "前端": ["前端", "HTML", "CSS", "JavaScript", "Vue", "React"],
        "后端": ["后端", "服务器", "API", "微服务", "Spring", "Django"],
    }

    def detect_learning_intent(self, query: str) -> Dict:
        """
        检测用户是否有学习意图，并识别学习方向
        :param query: 用户问题
        :return: {"is_learning": bool, "topics": list, "level": str}
        """
        query_lower = query.lower()

        # 学习意图关键词
        learning_indicators = [
            "怎么学", "如何学", "学习", "教程", "课程", "建议",
            "推荐", "路线", "路径", "从哪开始", "应该学"
        ]

        is_learning = any(keyword in query_lower for keyword in learning_indicators)

        if not is_learning:
            return {"is_learning": False, "topics": [], "level": None}

        # 识别主题
        topics = []
        for topic, keywords in self.LEARNING_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)

        # 识别难度级别
        level = None
        if any(kw in query_lower for kw in ["入门", "基础", "初学者", "新手"]):
            level = "简单"
        elif any(kw in query_lower for kw in ["进阶", "高级", "深入"]):
            level = "困难"
        else:
            level = "中等"

        return {
            "is_learning": True,
            "topics": topics if topics else ["通用"],
            "level": level
        }

    def search_courses_by_keywords(
            self,
            db: Session,
            keywords: List[str],
            difficulty: str = None,
            limit: int = 3
    ) -> List[Dict]:
        """
        根据关键词搜索相关课程
        :param db: 数据库会话
        :param keywords: 搜索关键词列表
        :param difficulty: 难度过滤
        :param limit: 返回数量限制
        :return: 课程列表
        """
        if not keywords or keywords == ["通用"]:
            # 如果没有特定主题，返回热门课程
            query = db.query(Course).filter(
                Course.is_published == True
            ).order_by(Course.view_count.desc())
        else:
            # 构建模糊查询条件
            conditions = []
            for keyword in keywords:
                conditions.append(Course.title.like(f"%{keyword}%"))
                conditions.append(Course.description.like(f"%{keyword}%"))

            from sqlalchemy import or_
            query = db.query(Course).filter(
                Course.is_published == True,
                or_(*conditions)
            )

        # 难度过滤
        if difficulty:
            query = query.filter(Course.difficulty == difficulty)

        courses = query.limit(limit).all()

        # 格式化返回结果
        result = []
        for course in courses:
            # 获取分类名称
            category = db.query(CourseCategory).filter(
                CourseCategory.id == course.category_id
            ).first()

            result.append({
                "id": course.id,
                "title": course.title,
                "description": course.description[:100] if course.description else "",
                "cover_url": course.cover_url,
                "lecturer": course.lecturer,
                "difficulty": course.difficulty,
                "category_name": category.name if category else "未分类",
                "view_count": course.view_count,
                "reason": self._generate_recommend_reason(course, keywords)
            })

        return result

    def _generate_recommend_reason(self, course: Course, keywords: List[str]) -> str:
        """生成推荐理由"""
        if keywords == ["通用"]:
            return "热门课程，适合系统学习"

        matched_keywords = [
            kw for kw in keywords
            if kw in course.title or (course.description and kw in course.description)
        ]

        if matched_keywords:
            return f"与你关注的「{'、'.join(matched_keywords)}」相关"
        else:
            return "可能对你有帮助的相关课程"

    def get_personalized_recommendations(
            self,
            db: Session,
            user_id: int,
            query: str,
            limit: int = 3
    ) -> List[Dict]:
        """
        获取个性化课程推荐
        :param db: 数据库会话
        :param user_id: 用户ID
        :param query: 用户问题
        :param limit: 推荐数量
        :return: 推荐课程列表
        """
        try:
            # 1. 检测学习意图
            intent = self.detect_learning_intent(query)

            if not intent["is_learning"]:
                return []

            logger.info(f"检测到学习意图 - 主题: {intent['topics']}, 难度: {intent['level']}")

            # 2. 基于关键词搜索课程
            recommendations = self.search_courses_by_keywords(
                db=db,
                keywords=intent["topics"],
                difficulty=intent["level"],
                limit=limit
            )

            # 3. 如果结果不足，补充热门推荐
            if len(recommendations) < limit:
                additional = self.search_courses_by_keywords(
                    db=db,
                    keywords=["通用"],
                    difficulty=None,
                    limit=limit - len(recommendations)
                )
                recommendations.extend(additional)

            logger.info(f"为用户 {user_id} 推荐了 {len(recommendations)} 门课程")
            return recommendations

        except Exception as e:
            logger.error(f"获取个性化推荐失败: {str(e)}")
            return []


# 全局单例
recommendation_service = RecommendationService()
