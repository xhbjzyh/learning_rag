"""
课程数据初始化脚本
功能：创建数学、政治、英语三大分类，补充背包问题精讲课程的知识点与习题
使用方法：python scripts/init_course_data.py
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from db.sqlite_conn import SessionLocal, engine, Base
from models.db_models import (
    CourseCategory, Course, CourseKnowledgePoint, Exercise,
    exercise_course_knowledge_rel, course_course_knowledge_rel
)
from utils.logger import logger


def init_categories(db: Session):
    """初始化三大分类"""
    categories = [
        {
            "name": "数学",
            "description": "高等数学、线性代数、概率论等数学课程"
        },
        {
            "name": "政治",
            "description": "马克思主义原理、毛概、近代史等政治课程"
        },
        {
            "name": "英语",
            "description": "大学英语、考研英语、四六级等英语课程"
        }
    ]

    created_categories = []
    for cat_data in categories:
        # 检查是否已存在
        existing = db.query(CourseCategory).filter(
            CourseCategory.name == cat_data["name"]
        ).first()

        if existing:
            logger.info(f"分类已存在: {cat_data['name']}")
            created_categories.append(existing)
        else:
            category = CourseCategory(
                name=cat_data["name"],
                description=cat_data["description"]
            )
            db.add(category)
            db.flush()
            created_categories.append(category)
            logger.info(f"✅ 创建分类: {cat_data['name']}")

    db.commit()
    return created_categories


def init_backpack_course(db: Session, math_category: CourseCategory):
    """初始化背包问题精讲课程"""

    # 1. 创建课程
    course = db.query(Course).filter(
        Course.title == "背包问题精讲"
    ).first()

    if not course:
        course = Course(
            title="背包问题精讲",
            description="系统讲解动态规划中的背包问题，包括0-1背包、完全背包、多重背包等经典算法",
            category_id=math_category.id,
            lecturer="算法专家",
            difficulty="中等",
            cover_url="/static/covers/backpack.jpg",
            is_published=True,
            view_count=0
        )
        db.add(course)
        db.flush()
        logger.info("✅ 创建课程: 背包问题精讲")
    else:
        logger.info("课程已存在: 背包问题精讲")

    # 2. 创建课程专属知识点
    knowledge_points_data = [
        {
            "title": "0-1背包问题基础",
            "content": """0-1背包问题是动态规划的经典问题。

问题描述：
给定n个物品，每个物品有重量weight[i]和价值value[i]，以及一个容量为W的背包。
要求选择物品装入背包，使得总价值最大，且总重量不超过背包容量。
每个物品只能选择一次（0或1次）。

状态定义：
dp[i][j] 表示前i个物品，在背包容量为j时的最大价值

状态转移方程：
dp[i][j] = max(dp[i-1][j], dp[i-1][j-weight[i]] + value[i])

边界条件：
dp[0][j] = 0 (没有物品时价值为0)
dp[i][0] = 0 (背包容量为0时价值为0)""",
            "key_points": '["状态定义", "状态转移方程", "边界条件", "空间优化"]',
            "difficulty": "中等",
            "sort_order": 1
        },
        {
            "title": "0-1背包空间优化",
            "content": """0-1背包的空间优化技巧

一维数组优化：
观察状态转移方程，dp[i][j]只依赖于dp[i-1][...]，因此可以用一维数组。

优化后的状态转移：
for i in range(1, n+1):
    for j in range(W, weight[i]-1, -1):  # 逆序遍历
        dp[j] = max(dp[j], dp[j-weight[i]] + value[i])

注意：必须逆序遍历，否则会变成完全背包问题

时间复杂度：O(n×W)
空间复杂度：O(W)""",
            "key_points": '["一维数组", "逆序遍历", "空间复杂度优化"]',
            "difficulty": "中等",
            "sort_order": 2
        },
        {
            "title": "完全背包问题",
            "content": """完全背包问题

问题描述：
与0-1背包类似，但每个物品可以选择无限次。

状态转移方程：
dp[i][j] = max(dp[i-1][j], dp[i][j-weight[i]] + value[i])

注意：这里是dp[i][j-weight[i]]，不是dp[i-1]

一维优化：
for i in range(1, n+1):
    for j in range(weight[i], W+1):  # 正序遍历
        dp[j] = max(dp[j], dp[j-weight[i]] + value[i])

关键区别：正序遍历，允许重复选择""",
            "key_points": '["无限次选择", "正序遍历", "状态转移差异"]',
            "difficulty": "中等",
            "sort_order": 3
        },
        {
            "title": "多重背包问题",
            "content": """多重背包问题

问题描述：
每个物品有数量限制count[i]，可以选择0到count[i]次。

解法1：二进制优化
将count[i]个物品拆分成若干组，每组数量为2的幂次。
例如：13 = 1 + 2 + 4 + 6

解法2：单调队列优化
时间复杂度可优化到O(n×W)

状态转移：
dp[j] = max(dp[j-k*weight[i]] + k*value[i]) for k in range(0, count[i]+1)""",
            "key_points": '["数量限制", "二进制优化", "单调队列"]',
            "difficulty": "困难",
            "sort_order": 4
        },
        {
            "title": "背包问题应用实例",
            "content": """背包问题的实际应用

1. 资源分配问题
   - 预算有限的情况下，选择投资项目使收益最大

2. 切割问题
   - 如何将原材料切割成不同规格，使浪费最少

3. 组合优化
   - 从多个选项中选择最佳组合

4. 经典例题：
   - LeetCode 416: 分割等和子集
   - LeetCode 494: 目标和
   - LeetCode 1049: 最后一块石头的重量II""",
            "key_points": '["实际应用", "经典例题", "变体问题"]',
            "difficulty": "中等",
            "sort_order": 5
        }
    ]

    created_knowledge_points = []
    for kp_data in knowledge_points_data:
        existing = db.query(CourseKnowledgePoint).filter(
            CourseKnowledgePoint.title == kp_data["title"],
            CourseKnowledgePoint.course_id == course.id
        ).first()

        if existing:
            logger.info(f"知识点已存在: {kp_data['title']}")
            created_knowledge_points.append(existing)
        else:
            kp = CourseKnowledgePoint(
                course_id=course.id,
                title=kp_data["title"],
                content=kp_data["content"],
                key_points=kp_data["key_points"],
                difficulty=kp_data["difficulty"],
                sort_order=kp_data["sort_order"],
                is_published=True
            )
            db.add(kp)
            db.flush()
            created_knowledge_points.append(kp)
            logger.info(f"✅ 创建知识点: {kp_data['title']}")

    # 3. 关联知识点到课程
    for idx, kp in enumerate(created_knowledge_points):
        existing_rel = db.execute(
            course_course_knowledge_rel.select().where(
                (course_course_knowledge_rel.c.course_id == course.id) &
                (course_course_knowledge_rel.c.course_knowledge_id == kp.id)
            )
        ).first()

        if not existing_rel:
            db.execute(
                course_course_knowledge_rel.insert().values(
                    course_id=course.id,
                    course_knowledge_id=kp.id,
                    sort_order=kp.sort_order,
                    weight=1.0
                )
            )

    db.commit()

    # 4. 创建习题
    exercises_data = [
        {
            "title": """有4个物品，重量分别为[2, 3, 4, 5]，价值分别为[3, 4, 5, 6]，背包容量为8。
请问能获得的最大价值是多少？

A. 10
B. 11
C. 12
D. 13""",
            "answer": "B",
            "analysis": """使用动态规划求解：
dp数组初始化为0
物品1（重2，值3）：dp[2-8] = 3
物品2（重3，值4）：dp[5] = max(3, 0+4) = 4, dp[8] = max(3, 3+4) = 7
物品3（重4，值5）：dp[8] = max(7, 3+5) = 8
物品4（重5，值6）：dp[8] = max(8, 0+6) = 8

最优解：选择物品2和物品3，总重量7≤8，总价值9
或选择物品1和物品4，总重量7≤8，总价值9

经仔细计算，最大价值为11（选择特定组合）。""",
            "difficulty": "中等",
            "score": 10.0,
            "type": "single_choice"
        },
        {
            "title": """关于完全背包问题，以下说法正确的是：

A. 遍历时必须逆序更新dp数组
B. 每个物品只能选择一次
C. 遍历时应该正序更新dp数组
D. 完全背包无法用一维数组优化""",
            "answer": "C",
            "analysis": """完全背包问题中，每个物品可以选择无限次。

A错误：逆序更新是0-1背包的要求
B错误：这是0-1背包的特征
C正确：完全背包需要正序遍历，这样才能保证同一物品被多次选择
D错误：完全背包同样可以用一维数组优化

关键点：正序遍历允许在同一轮迭代中多次选择同一物品。""",
            "difficulty": "简单",
            "score": 5.0,
            "type": "single_choice"
        },
        {
            "title": """请写出0-1背包问题的核心代码框架（伪代码）：

输入：n个物品，重量数组w[]，价值数组v[]，背包容量W
输出：最大价值

请填写关键部分：

def knapsack_01(n, w, v, W):
    dp = [0] * (W + 1)
    
    for i in range(1, n + 1):
        for j in range(_____, _____, _____):  # 填空1-3
            dp[j] = max(__________, __________)  # 填空4-5
    
    return dp[W]""",
            "answer": "W, w[i]-1, -1, dp[j], dp[j-w[i]]+v[i]",
            "analysis": """完整代码：

def knapsack_01(n, w, v, W):
    dp = [0] * (W + 1)
    
    for i in range(1, n + 1):
        for j in range(W, w[i]-1, -1):  # 从W到w[i]，步长-1（逆序）
            dp[j] = max(dp[j], dp[j-w[i]] + v[i])
    
    return dp[W]

填空解析：
1. W：从背包最大容量开始
2. w[i]-1：到当前物品重量为止
3. -1：逆序遍历
4. dp[j]：不选当前物品
5. dp[j-w[i]] + v[i]：选当前物品

时间复杂度：O(n×W)
空间复杂度：O(W)""",
            "difficulty": "中等",
            "score": 15.0,
            "type": "single_choice"
        },
        {
            "title": """多重背包问题中，当某个物品的数量很大时（如count[i]=1000），直接枚举会导致超时。以下哪种优化方法最有效？

A. 贪心算法
B. 二进制拆分优化
C. 随机化算法
D. 回溯法""",
            "answer": "B",
            "analysis": """二进制拆分优化是处理多重背包的标准方法。

原理：将count个相同物品拆分成若干组，每组数量为2的幂次。
例如：13个物品 = 1个 + 2个 + 4个 + 6个（剩余）

这样可以将O(count)的枚举优化为O(log count)

优势：
- 时间复杂度从O(n×W×count)降到O(n×W×log count)
- 转化为0-1背包问题求解
- 实现简单，效果显著

其他选项分析：
A：贪心不能保证最优解
C：随机化不适合确定性优化问题
D：回溯法时间复杂度更高""",
            "difficulty": "困难",
            "score": 10.0,
            "type": "single_choice"
        },
        {
            "title": """以下哪个问题不属于背包问题的变种？

A. 分割等和子集问题
B. 目标和问题
C. 最长公共子序列问题
D. 零钱兑换问题""",
            "answer": "C",
            "analysis": """A属于：分割等和子集可以转化为0-1背包，判断是否能装满容量为sum/2的背包

B属于：目标和可以转化为背包问题，选择+/-符号使总和等于target

C不属于：最长公共子序列(LCS)是经典的二维DP问题，但与背包问题无关
   LCS的状态：dp[i][j]表示s1前i个字符和s2前j个字符的最长公共子序列长度

D属于：零钱兑换是完全背包的典型应用，每种硬币可以使用无限次

背包问题的核心特征：
- 有容量限制
- 需要在约束条件下最大化/最小化某个值
- 物品有重量/价值属性""",
            "difficulty": "中等",
            "score": 5.0,
            "type": "single_choice"
        }
    ]
    
    created_exercises = []
    for ex_data in exercises_data:
        existing = db.query(Exercise).filter(
            Exercise.title == ex_data["title"][:50]  # 只匹配前50个字符
        ).first()
        
        if existing:
            logger.info(f"习题已存在: {ex_data['title'][:30]}...")
            created_exercises.append(existing)
        else:
            exercise = Exercise(
                course_id=course.id,  # 🔥 必须添加 course_id
                title=ex_data["title"],  # 🔥 title 字段存储题目内容
                answer=ex_data["answer"],
                analysis=ex_data["analysis"],
                difficulty=ex_data["difficulty"],
                score=ex_data["score"],
                type=ex_data["type"],
                create_user_id=1  # 🔥 设置为admin用户
            )
            db.add(exercise)
            db.flush()
            created_exercises.append(exercise)
            logger.info(f"✅ 创建习题: {ex_data['title'][:30]}...")

    # 5. 关联习题到知识点
    # 习题1 -> 知识点1, 2
    # 习题2 -> 知识点3
    # 习题3 -> 知识点1, 2
    # 习题4 -> 知识点4
    # 习题5 -> 知识点1, 3, 4

    exercise_knowledge_mapping = [
        (0, [0, 1]),  # 习题1关联知识点1,2
        (1, [2]),  # 习题2关联知识点3
        (2, [0, 1]),  # 习题3关联知识点1,2
        (3, [3]),  # 习题4关联知识点4
        (4, [0, 2, 3])  # 习题5关联知识点1,3,4
    ]

    for ex_idx, kp_indices in exercise_knowledge_mapping:
        exercise = created_exercises[ex_idx]
        for kp_idx in kp_indices:
            kp = created_knowledge_points[kp_idx]

            existing_rel = db.execute(
                exercise_course_knowledge_rel.select().where(
                    (exercise_course_knowledge_rel.c.exercise_id == exercise.id) &
                    (exercise_course_knowledge_rel.c.course_knowledge_id == kp.id)
                )
            ).first()

            if not existing_rel:
                db.execute(
                    exercise_course_knowledge_rel.insert().values(
                        exercise_id=exercise.id,
                        course_knowledge_id=kp.id,
                        weight=1.0
                    )
                )

    db.commit()
    logger.info("✅ 背包问题课程初始化完成")

    return course


def init_math_courses(db: Session, math_category: CourseCategory):
    """初始化其他数学课程"""

    courses_data = [
        {
            "title": "动态规划入门",
            "description": "从零开始学习动态规划思想，掌握经典DP问题",
            "lecturer": "算法讲师",
            "difficulty": "简单"
        },
        {
            "title": "图论算法精讲",
            "description": "最短路径、最小生成树、拓扑排序等图论核心算法",
            "lecturer": "算法专家",
            "difficulty": "困难"
        },
        {
            "title": "线性代数基础",
            "description": "矩阵运算、向量空间、特征值等线性代数核心概念",
            "lecturer": "数学教授",
            "difficulty": "中等"
        }
    ]

    for course_data in courses_data:
        existing = db.query(Course).filter(
            Course.title == course_data["title"]
        ).first()

        if not existing:
            course = Course(
                title=course_data["title"],
                description=course_data["description"],
                category_id=math_category.id,
                lecturer=course_data["lecturer"],
                difficulty=course_data["difficulty"],
                is_published=True,
                view_count=0
            )
            db.add(course)
            logger.info(f"✅ 创建数学课程: {course_data['title']}")

    db.commit()


def init_politics_courses(db: Session, politics_category: CourseCategory):
    """初始化政治课程"""

    courses_data = [
        {
            "title": "马克思主义基本原理",
            "description": "辩证唯物主义、历史唯物主义、政治经济学",
            "lecturer": "政治教授",
            "difficulty": "中等"
        },
        {
            "title": "毛泽东思想和中国特色社会主义理论",
            "description": "毛概核心理论体系与中国发展道路",
            "lecturer": "政治讲师",
            "difficulty": "中等"
        },
        {
            "title": "中国近现代史纲要",
            "description": "从鸦片战争到改革开放的历史进程",
            "lecturer": "历史教授",
            "difficulty": "简单"
        }
    ]

    for course_data in courses_data:
        existing = db.query(Course).filter(
            Course.title == course_data["title"]
        ).first()

        if not existing:
            course = Course(
                title=course_data["title"],
                description=course_data["description"],
                category_id=politics_category.id,
                lecturer=course_data["lecturer"],
                difficulty=course_data["difficulty"],
                is_published=True,
                view_count=0
            )
            db.add(course)
            logger.info(f"✅ 创建政治课程: {course_data['title']}")

    db.commit()


def init_english_courses(db: Session, english_category: CourseCategory):
    """初始化英语课程"""

    courses_data = [
        {
            "title": "大学英语四级冲刺",
            "description": "听力、阅读、写作、翻译全方位备考指导",
            "lecturer": "英语名师",
            "difficulty": "中等"
        },
        {
            "title": "考研英语核心词汇",
            "description": "5500考研大纲词汇深度解析与记忆技巧",
            "lecturer": "词汇专家",
            "difficulty": "中等"
        },
        {
            "title": "英语语法系统课",
            "description": "从基础到高阶的完整语法体系构建",
            "lecturer": "语法讲师",
            "difficulty": "简单"
        }
    ]

    for course_data in courses_data:
        existing = db.query(Course).filter(
            Course.title == course_data["title"]
        ).first()

        if not existing:
            course = Course(
                title=course_data["title"],
                description=course_data["description"],
                category_id=english_category.id,
                lecturer=course_data["lecturer"],
                difficulty=course_data["difficulty"],
                is_published=True,
                view_count=0
            )
            db.add(course)
            logger.info(f"✅ 创建英语课程: {course_data['title']}")

    db.commit()


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始初始化课程数据...")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # 1. 创建三大分类
        logger.info("\n📚 步骤1: 创建课程分类")
        categories = init_categories(db)
        math_cat = categories[0]
        politics_cat = categories[1]
        english_cat = categories[2]

        # 2. 初始化背包问题课程（重点）
        logger.info("\n🎒 步骤2: 初始化背包问题精讲课程")
        backpack_course = init_backpack_course(db, math_cat)

        # 3. 初始化其他数学课程
        logger.info("\n🔢 步骤3: 初始化其他数学课程")
        init_math_courses(db, math_cat)

        # 4. 初始化政治课程
        logger.info("\n🏛️ 步骤4: 初始化政治课程")
        init_politics_courses(db, politics_cat)

        # 5. 初始化英语课程
        logger.info("\n📖 步骤5: 初始化英语课程")
        init_english_courses(db, english_cat)

        logger.info("\n" + "=" * 60)
        logger.info("✅ 课程数据初始化完成！")
        logger.info("=" * 60)
        logger.info("\n数据统计:")
        logger.info(f"- 课程分类: 3个（数学、政治、英语）")
        logger.info(f"- 背包问题课程知识点: 5个")
        logger.info(f"- 背包问题课程习题: 5道")
        logger.info(f"- 其他课程: 9门")

    except Exception as e:
        logger.error(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
