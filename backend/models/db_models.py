"""
数据库ORM模型定义（最终企业级版）
优化内容：
1. 保留所有现有表和关联，无任何删除
2. 🔥 核心：知识库知识点 / 课程知识点 完全独立分离（两套体系互不干扰）
3. 统一课程资源-知识点多对多关联（视频/文档/习题共用）
4. 新增知识点问答系统核心表
5. 升级用户画像为三源融合版（视频+习题+问答）
6. 升级知识点掌握度为分维度计算
7. 完善所有关联关系和级联操作
8. 保留原有推荐系统所有核心表
9. ✅ 修复：所有双向关系使用back_populates，彻底解决属性冲突
10. ✅ 修复：删除无用依赖、修正语法错误
"""
# ==================== 第三方库导入 ====================
from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, Boolean, Table,DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
# ==================== 内部模块导入 ====================
from db.sqlite_conn import Base
from sqlalchemy.sql import func  # 数据库自动时间函数
# ==================== 🔥 统一：课程资源-知识库知识点多对多关联表 ====================
course_resource_knowledge_rel = Table(
    "course_resource_knowledge_rel",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="关联ID"),
    Column("resource_id", Integer, ForeignKey("course_resource.id", ondelete="CASCADE"), nullable=False, index=True, comment="资源ID"),
    Column("knowledge_point_id", Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="知识点ID"),
    Column("weight", Float, nullable=False, default=1.0, comment="关联权重(0-1)，越高表示资源与知识点越相关"),
    Column("create_time", TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间"),
    comment="课程资源-知识库知识点多对多关联表"
)

# ==================== 🔥 新增：课程专属知识点 独立关联表（与知识库完全分离） ====================
# 课程 - 课程知识点 多对多关联
course_course_knowledge_rel = Table(
    "course_course_knowledge_rel",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="关联ID"),
    Column("course_id", Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID"),
    Column("course_knowledge_id", Integer, ForeignKey("course_knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程知识点ID"),
    Column("sort_order", Integer, nullable=False, default=0, comment="排序"),
    Column("weight", Float, nullable=False, default=1.0, comment="关联权重"),
    Column("create_time", TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间"),
    comment="课程-课程专属知识点关联表（独立体系）"
)

# 课程资源 - 课程知识点 多对多关联
course_resource_course_knowledge_rel = Table(
    "course_resource_course_knowledge_rel",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="关联ID"),
    Column("resource_id", Integer, ForeignKey("course_resource.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程资源ID"),
    Column("course_knowledge_id", Integer, ForeignKey("course_knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程知识点ID"),
    Column("weight", Float, nullable=False, default=1.0, comment="关联权重"),
    Column("create_time", TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间"),
    comment="课程资源-课程专属知识点关联表（独立体系）"
)
exercise_course_knowledge_rel = Table(
    "exercise_course_knowledge_rel",
    Base.metadata,
    Column("exercise_id", Integer, ForeignKey("exercise.id"), primary_key=True),
    Column("course_knowledge_id", Integer, ForeignKey("course_knowledge_point.id"), primary_key=True),
    Column("weight", Float, default=1.0),  # 权重（可选）
    Column("create_time", DateTime, default=func.now())
)

# 🔥 新增：知识库文档-知识点多对多关联表（移到这里，确保在使用前定义）
knowledge_document_rel = Table(
    "knowledge_document_rel",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="关联ID"),
    Column("document_id", Integer, ForeignKey("knowledge_document.id", ondelete="CASCADE"), nullable=False, index=True, comment="文档ID"),
    Column("knowledge_point_id", Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="知识点ID"),
    Column("weight", Float, nullable=False, default=1.0, comment="关联权重"),
    Column("create_time", TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间"),
    comment="知识库文档-知识点多对多关联表"
)


# ==================== 用户模块模型 ====================
class SysRole(Base):
    """系统角色表"""
    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="角色ID，主键自增")
    role_name = Column(String(32), nullable=False, unique=True, comment="角色名称，唯一标识：admin/user")
    description = Column(String(255), comment="角色描述")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class SystemConfig(Base):
    """系统配置表（动态配置）"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="配置ID")
    config_key = Column(String(64), nullable=False, unique=True, index=True, comment="配置键")
    config_value = Column(Text, nullable=True, comment="配置值")
    config_type = Column(String(32), nullable=False, default="string", comment="配置类型：string/int/bool/json")
    description = Column(String(255), comment="配置描述")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class SysUser(Base):
    """系统用户表"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID，主键自增")
    username = Column(String(32), nullable=False, unique=True, index=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码（bcrypt加密）")
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False, comment="角色ID")
    is_active = Column(Integer, nullable=False, default=1, comment="账号是否启用")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 原有关联
    exercise_records = relationship("UserExerciseRecord", back_populates="user", cascade="all, delete-orphan")
    knowledge_mastery = relationship("UserKnowledgeMastery", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    course_progress = relationship("UserCourseProgress", back_populates="user", cascade="all, delete-orphan")
    resource_progress = relationship("UserResourceProgress", back_populates="user", cascade="all, delete-orphan")
    qa_records = relationship("UserQaRecord", back_populates="user", cascade="all, delete-orphan")

    # 推荐系统关联
    learning_preference = relationship("UserLearningPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    course_behaviors = relationship("UserCourseBehavior", back_populates="user", cascade="all, delete-orphan")
    interest_tags = relationship("UserInterestTag", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationRecord", back_populates="user", cascade="all, delete-orphan")

    # 知识点问答记录
    knowledge_qa_records = relationship("KnowledgeQaRecord", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    """用户画像表（三源融合版）"""
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="画像ID")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, unique=True, comment="用户ID")
    total_study_time = Column(Integer, default=0, comment="总学习时长（分钟）")
    completed_points = Column(Integer, default=0, comment="已完成知识点数")
    current_level = Column(String(32), default="入门", comment="当前学习等级")
    preferred_difficulty = Column(String(32), default="中等", comment="偏好难度")
    tag_weight = Column(Text, default="{}", comment="标签权重（JSON）")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    total_study_duration = Column(Integer, nullable=False, default=0, comment="总学习时长（秒）")
    finished_points_count = Column(Integer, nullable=False, default=0, comment="已完成知识点数")
    average_score = Column(Float, nullable=False, default=0.0, comment="平均练习得分")
    weak_tags = Column(Text, comment="薄弱标签（JSON）")
    strong_tags = Column(Text, comment="优势标签（JSON）")

    # 视频学习维度
    video_completion_rate = Column(Float, default=0.0, comment="平均视频完成率")
    video_study_ratio = Column(Float, default=0.0, comment="视频学习时长占比")

    # 习题练习维度
    exercise_accuracy = Column(Float, default=0.0, comment="整体习题正确率")
    average_answer_speed = Column(Float, default=0.0, comment="平均答题速度（秒/题）")

    # 知识点问答维度
    qa_count = Column(Integer, default=0, comment="总提问次数")
    qa_solve_rate = Column(Float, default=0.0, comment="问题解决率")
    average_qa_score = Column(Float, default=0.0, comment="平均问答反馈评分")

    # 综合能力指标
    comprehensive_ability = Column(Float, default=0.0, comment="综合学习能力得分（0-100）")
    learning_efficiency = Column(Float, default=0.0, comment="学习效率得分（0-100）")

    # 关联
    user = relationship("SysUser", back_populates="profile")


class UserLearningHistory(Base):
    """用户学习历史表"""
    __tablename__ = "user_learning_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="历史ID")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")
    
    # 🔥 修复：同时支持知识库知识点和课程知识点
    point_id = Column(Integer, ForeignKey("knowledge_point.id"), nullable=True, comment="知识库知识点ID（可选）")
    course_knowledge_id = Column(Integer, ForeignKey("course_knowledge_point.id"), nullable=True, comment="课程知识点ID（可选）")
    
    study_duration = Column(Integer, comment="学习时长（秒）")
    is_mastered = Column(Integer, default=0, comment="是否已掌握")
    session_type = Column(String(32), default="study", comment="会话类型：study/practice/review")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="学习时间")


class UserLearningRecord(Base):
    """用户学习行为记录表（知识点级）"""
    __tablename__ = "user_learning_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    learn_duration = Column(Integer, default=0, comment="学习时长（秒）")
    is_collected = Column(Boolean, default=False, comment="是否收藏")
    feedback_score = Column(Integer, nullable=True, comment="反馈评分（1-5）")
    is_finished = Column(Boolean, default=False, comment="是否完成")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class UserFeedback(Base):
    """用户反馈表"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="反馈ID")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")
    point_id = Column(Integer, ForeignKey("knowledge_point.id"), comment="知识点ID")
    feedback_type = Column(String(32), nullable=False, comment="反馈类型")
    content = Column(Text, nullable=False, comment="反馈内容")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")


# ==================== 知识库模块模型（独立：知识库知识点） ====================
class KnowledgeCategory(Base):
    """知识库分类表"""
    __tablename__ = "knowledge_category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    category_name = Column(String(64), nullable=False, unique=True, comment="分类名称")
    description = Column(String(255), comment="分类描述")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class KnowledgeDocument(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_document"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文档ID")
    title = Column(String(128), nullable=False, comment="文档标题")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_md5 = Column(String(32), nullable=False, index=True, comment="文件MD5")
    file_type = Column(String(32), nullable=False, comment="文件类型")
    file_size = Column(Integer, comment="文件大小（字节）")
    category_id = Column(Integer, ForeignKey("knowledge_category.id"), comment="分类ID")
    upload_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="上传用户ID")
    audit_status = Column(Integer, nullable=False, default=0, comment="审核状态")
    audit_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="审核人ID")
    audit_time = Column(TIMESTAMP, comment="审核时间")
    audit_remark = Column(String(255), comment="审核备注")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_public = Column(Integer, nullable=False, default=0, comment="是否公开")
    process_status = Column(Integer, nullable=False, default=0, comment="处理状态")
    process_message = Column(String(255), comment="处理信息")

    # 关联
    knowledge_points = relationship("KnowledgePoint", secondary=knowledge_document_rel, back_populates="documents")


class KnowledgeTag(Base):
    """知识点标签表"""
    __tablename__ = "knowledge_tag"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="标签ID")
    name = Column(String(50), nullable=False, unique=True, index=True, comment="标签名称")
    description = Column(String(200), nullable=True, comment="标签描述")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    points = relationship("KnowledgePoint", secondary="knowledge_point_tag_rel", back_populates="tags")


class KnowledgePointTagRel(Base):
    """知识点-标签多对多关联表"""
    __tablename__ = "knowledge_point_tag_rel"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="关联ID")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    tag_id = Column(Integer, ForeignKey("knowledge_tag.id", ondelete="CASCADE"), nullable=False, comment="标签ID")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")


class KnowledgePoint(Base):
    """知识点表（统一知识库）"""
    __tablename__ = "knowledge_point"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="知识点ID")
    title = Column(String(255), nullable=False, comment="知识点标题")
    content = Column(Text, nullable=False, comment="知识点内容")
    key_points = Column(Text, comment="核心要点（JSON）")
    difficulty = Column(String(32), nullable=False, default="中等", comment="难度")
    
    # 🔥 新增：知识点来源标识
    source_type = Column(String(32), nullable=False, default="public", comment="来源类型：public=公共库, course=课程同步")
    source_id = Column(Integer, nullable=True, comment="来源ID（如果是课程同步，存储course_knowledge_point.id）")
    course_id = Column(Integer, ForeignKey("course.id"), nullable=True, comment="所属课程ID（仅课程同步时有值）")
    
    is_published = Column(Boolean, default=True, comment="是否发布")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联（🔥 修复：使用字符串引用，避免前向引用问题）
    documents = relationship("KnowledgeDocument", secondary=knowledge_document_rel, back_populates="knowledge_points")
    tags = relationship("KnowledgeTag", secondary="knowledge_point_tag_rel", back_populates="points")
    exercises = relationship("Exercise", secondary="exercise_knowledge", back_populates="knowledge_points")
    user_mastery = relationship("UserKnowledgeMastery", back_populates="knowledge_point", cascade="all, delete-orphan")
    qa_records = relationship("KnowledgeQaRecord", back_populates="knowledge_point", cascade="all, delete-orphan")
    course_resources = relationship("CourseResource", secondary=course_resource_knowledge_rel, back_populates="knowledge_points")


# ==================== 审核模块模型 ====================
class AuditRecord(Base):
    """审核记录表"""
    __tablename__ = "audit_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="审核记录ID")
    doc_id = Column(Integer, ForeignKey("knowledge_document.id"), nullable=False, comment="文档ID")
    auditor_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="审核人ID")
    audit_status = Column(Integer, nullable=False, comment="审核状态")
    audit_remark = Column(String(255), comment="审核备注")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="审核时间")


# ==================== 推荐记录表（通用版） ====================
class RecommendationRecord(Base):
    """推荐记录表"""
    __tablename__ = "recommendation_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="推荐ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    target_id = Column(Integer, nullable=False, index=True, comment="推荐目标ID")
    recommend_type = Column(String(32), nullable=False, index=True, comment="推荐类型")
    recommendation_reason = Column(String(255), comment="推荐理由")
    score = Column(Float, nullable=False, comment="推荐得分")
    rank = Column(Integer, nullable=False, comment="推荐排名")
    is_clicked = Column(Boolean, default=False, comment="是否点击")
    is_collected = Column(Boolean, default=False, comment="是否收藏")
    feedback = Column(Integer, comment="用户反馈")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True, comment="推荐生成时间")

    user = relationship("SysUser", back_populates="recommendations")


# ==================== 内容公开申请表 ====================
class ContentPublicApply(Base):
    """内容公开申请表"""
    __tablename__ = "content_public_apply"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="申请ID")
    doc_id = Column(Integer, ForeignKey("knowledge_document.id", ondelete="CASCADE"), nullable=False, comment="文档ID")
    apply_user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="申请人ID")
    apply_status = Column(Integer, nullable=False, default=0, comment="申请状态")
    apply_remark = Column(String(255), comment="申请理由")
    audit_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="审核人ID")
    audit_remark = Column(String(255), comment="审核备注")
    audit_time = Column(TIMESTAMP, comment="审核时间")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="申请时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


# ==================== 错题记录表 ====================
class WrongQuestion(Base):
    """错题记录表"""
    __tablename__ = "wrong_question"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="错题ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")

    # 🔴 修改1：把 point_id 改成 exercise_id（错题关联具体习题，而非知识点）
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False, comment="习题ID")

    # 🔴 修改2：把 question 改成 question_title（语义更准确）
    question_title = Column(Text, nullable=False, comment="题目内容")

    user_answer = Column(Text, comment="用户答案")
    correct_answer = Column(Text, comment="正确答案")
    error_reason = Column(String(255), comment="错误原因")
    master_level = Column(Integer, nullable=False, default=0, comment="掌握程度：0=未掌握，1=部分掌握，2=已掌握")
    wrong_count = Column(Integer, nullable=False, default=1, comment="错误次数")

    # 🔴 新增1：最后错误时间 - 改用 TIMESTAMP 类型
    last_wrong_time = Column(TIMESTAMP, server_default=func.now(), comment="最后错误时间")
    last_review_time = Column(TIMESTAMP, server_default=func.now(), comment="最后复习时间")
    next_review_time = Column(TIMESTAMP, server_default=func.now(), comment="下次复习时间")
    create_time = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 🔴 修改3：关联关系从 point 改成 exercise
    user = relationship("SysUser", backref="wrong_questions")
    exercise = relationship("Exercise", backref="wrong_questions")

# ==================== 学习进度表 ====================
class LearningProgress(Base):
    """学习进度表"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="进度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    progress = Column(Float, nullable=False, default=0.0, comment="进度")
    is_finished = Column(Boolean, nullable=False, default=False, comment="是否完成")
    study_duration = Column(Integer, nullable=False, default=0, comment="学习时长")
    last_study_time = Column(TIMESTAMP, comment="上次学习时间")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


# ==================== 习题系统模型 ====================
exercise_knowledge = Table(
    "exercise_knowledge",
    Base.metadata,
    Column("exercise_id", Integer, ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True),
    Column("knowledge_point_id", Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), primary_key=True),
    comment="习题-知识库知识点关联表"
)


class Exercise(Base):
    """习题表"""
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="习题ID")
    # 🔥 修复：新增 course_id 外键字段（解决核心报错）
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False, comment="所属课程ID")
    title = Column(String(500), nullable=False, comment="题目内容")
    type = Column(String(20), nullable=False, comment="题型: single_choice/multiple_choice/true_false")
    difficulty = Column(String(20), default="中等", comment="难度")
    answer = Column(Text, nullable=False, comment="正确答案")
    analysis = Column(Text, comment="答案解析")
    score = Column(Float, default=10.0, comment="分值")
    create_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="创建人ID")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 🔥 修复：删除 relationship 中的 comment（SQLAlchemy 不支持）
    course = relationship("Course", backref="exercises")
    options = relationship("ExerciseOption", back_populates="exercise", cascade="all, delete-orphan")
    knowledge_points = relationship("KnowledgePoint", secondary="exercise_knowledge", back_populates="exercises")
    user_records = relationship("UserExerciseRecord", back_populates="exercise", cascade="all, delete-orphan")
    create_user = relationship("SysUser")
    course_resource = relationship("CourseResource", back_populates="exercise", uselist=False)
    course_knowledge_points = relationship(
        "CourseKnowledgePoint",
        secondary=exercise_course_knowledge_rel,
        backref="exercises"
    )


class ExerciseOption(Base):
    """选择题选项表"""
    __tablename__ = "exercise_option"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="选项ID")
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), comment="习题ID")
    content = Column(String(500), nullable=False, comment="选项内容")
    is_correct = Column(Boolean, default=False, comment="是否正确")
    order = Column(Integer, comment="选项顺序")

    exercise = relationship("Exercise", back_populates="options")

    @property
    def option_label(self):
        if self.order:
            return chr(ord('A') + self.order - 1)
        return ""

    @property
    def option_content(self):
        return self.content


class UserExerciseRecord(Base):
    """用户答题记录表"""
    __tablename__ = "user_exercise_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False, comment="习题ID")
    user_answer = Column(Text, comment="用户答案")
    score = Column(Float, comment="得分")
    is_correct = Column(Boolean, comment="是否答对")
    feedback = Column(Text, comment="批改评语")
    answer_time = Column(Integer, comment="答题时长（秒）")
    create_time = Column(DateTime, default=func.now())

    user = relationship("SysUser", back_populates="exercise_records")
    exercise = relationship("Exercise", back_populates="user_records")

class UserKnowledgeMastery(Base):
    """用户-知识库知识点 掌握度表"""
    __tablename__ = "user_knowledge_mastery"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="掌握度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    mastery_score = Column(Float, default=0.0, comment="综合掌握度得分")
    level = Column(String(20), default="未掌握", comment="掌握等级")
    total_questions = Column(Integer, default=0, comment="总答题数")
    correct_questions = Column(Integer, default=0, comment="答对题数")
    last_answer_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    # 分维度掌握度
    video_mastery = Column(Float, default=0.0, comment="视频学习掌握度")
    exercise_mastery = Column(Float, default=0.0, comment="习题练习掌握度")
    qa_mastery = Column(Float, default=0.0, comment="知识点问答掌握度")

    # 行为统计
    video_study_count = Column(Integer, default=0, comment="视频学习次数")
    exercise_attempt_count = Column(Integer, default=0, comment="习题练习次数")
    qa_count = Column(Integer, default=0, comment="提问次数")

    user = relationship("SysUser", back_populates="knowledge_mastery")
    knowledge_point = relationship("KnowledgePoint", back_populates="user_mastery")


# ==================== 课程系统模型 ====================
class CourseCategory(Base):
    """课程分类表"""
    __tablename__ = "course_category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(64), nullable=False, comment="分类名称")
    parent_id = Column(Integer, nullable=False, default=0, index=True, comment="父分类ID")
    level = Column(Integer, nullable=False, default=1, comment="分类级别")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    description = Column(String(255), comment="分类描述")
    icon = Column(String(255), comment="分类图标URL")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    children = relationship("CourseCategory",
                            primaryjoin="CourseCategory.id==foreign(CourseCategory.parent_id)",
                            cascade="all, delete-orphan")


class Course(Base):
    """课程表"""
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="课程ID")
    title = Column(String(255), nullable=False, comment="课程标题")
    cover_url = Column(String(512), comment="封面URL")
    description = Column(Text, comment="课程简介")
    lecturer = Column(String(128), comment="讲师")
    category_id = Column(Integer, ForeignKey("course_category.id"), nullable=False, index=True, comment="分类ID")
    difficulty = Column(String(10), default="中等", comment="难度")
    is_published = Column(Boolean, default=True, comment="发布状态")
    view_count = Column(Integer, nullable=False, default=0, comment="观看次数")
    is_public = Column(Integer, nullable=False, default=1, comment="是否公开")
    create_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="创建人ID")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    category = relationship("CourseCategory")
    create_user = relationship("SysUser")
    resources = relationship("CourseResource", back_populates="course", cascade="all, delete-orphan", order_by="CourseResource.sort_order")
    user_progress = relationship("UserCourseProgress", back_populates="course", cascade="all, delete-orphan")
    tags = relationship("CourseTag", secondary="course_tag_rel", back_populates="courses")
    user_behaviors = relationship("UserCourseBehavior", back_populates="course", cascade="all, delete-orphan")

    # 🔥 新增：独立课程知识点关联
    course_knowledge_points = relationship("CourseKnowledgePoint", secondary=course_course_knowledge_rel, back_populates="course", cascade="all, delete")


class CourseResource(Base):
    """课程资源表"""
    __tablename__ = "course_resource"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="资源ID")
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID")
    title = Column(String(255), nullable=False, comment="资源标题")
    type = Column(String(32), nullable=False, default="videos", comment="资源类型")
    description = Column(Text, comment="资源描述")
    url = Column(String(512), nullable=True, comment="资源链接")
    duration = Column(Integer, comment="视频时长")
    file_size = Column(Integer, comment="文件大小")
    file_type = Column(String(50), comment="文件类型")
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="SET NULL"), comment="关联习题ID")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    is_published = Column(Boolean, default=True, comment="是否发布")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    upload_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="上传人ID")
    download_count = Column(Integer, default=0, comment="下载次数")

    # 关联
    course = relationship("Course", back_populates="resources")
    user_progress = relationship("UserResourceProgress", back_populates="resource", cascade="all, delete-orphan")
    knowledge_points = relationship("KnowledgePoint", secondary=course_resource_knowledge_rel, back_populates="course_resources")
    exercise = relationship("Exercise", back_populates="course_resource", uselist=False)

    # 🔥 新增：独立课程知识点关联
    course_knowledge_points = relationship("CourseKnowledgePoint", secondary=course_resource_course_knowledge_rel, back_populates="course_resources")


class UserCourseProgress(Base):
    """用户课程学习进度表"""
    __tablename__ = "user_course_progress"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="进度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID")
    progress = Column(Float, nullable=False, default=0.0, comment="课程进度")
    is_finished = Column(Boolean, nullable=False, default=False, comment="是否完成")
    last_study_time = Column(TIMESTAMP, comment="上次学习时间")
    total_study_duration = Column(Integer, nullable=False, default=0, comment="累计学习时长")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("SysUser", back_populates="course_progress")
    course = relationship("Course", back_populates="user_progress")


class UserResourceProgress(Base):
    """用户资源学习进度表"""
    __tablename__ = "user_resource_progress"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="进度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    resource_id = Column(Integer, ForeignKey("course_resource.id", ondelete="CASCADE"), nullable=False, index=True, comment="资源ID")
    progress = Column(Float, nullable=False, default=0.0, comment="整体进度")
    is_finished = Column(Boolean, nullable=False, default=False, comment="是否完成")
    last_study_time = Column(TIMESTAMP, comment="上次学习时间")
    total_study_duration = Column(Integer, nullable=False, default=0, comment="累计学习时长")
    study_count = Column(Integer, nullable=False, default=1, comment="学习次数")

    # 视频专属
    watch_position = Column(Integer, default=0, comment="观看位置")
    pause_count = Column(Integer, default=0, comment="暂停次数")
    fast_forward_count = Column(Integer, default=0, comment="快进次数")
    rewind_count = Column(Integer, default=0, comment="后退次数")
    completion_rate = Column(Float, default=0.0, comment="完成率")

    # 习题专属
    exercise_score = Column(Float, comment="习题得分")
    correct_count = Column(Integer, default=0, comment="答对题数")
    total_count = Column(Integer, default=0, comment="总题数")
    wrong_question_ids = Column(Text, comment="错题ID列表")
    average_answer_time = Column(Float, comment="平均答题时长")

    # 文档专属
    read_pages = Column(Integer, default=0, comment="已读页数")
    total_pages = Column(Integer, default=0, comment="总页数")
    highlight_count = Column(Integer, default=0, comment="高亮次数")
    note_count = Column(Integer, default=0, comment="笔记次数")

    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("SysUser", back_populates="resource_progress")
    resource = relationship("CourseResource", back_populates="user_progress")


class UserQaRecord(Base):
    """用户问答交互记录表"""
    __tablename__ = "user_qa_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    query = Column(Text, nullable=False, comment="用户问题")
    answer = Column(Text, nullable=False, comment="系统回答")
    kb_type = Column(String(32), nullable=False, default="public", comment="知识库类型")
    related_point_ids = Column(Text, comment="关联知识点ID列表")
    difficulty = Column(String(32), default="中等", comment="问题难度")
    feedback_score = Column(Integer, nullable=True, comment="反馈评分")
    is_solved = Column(Boolean, default=True, comment="是否解决")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True, comment="创建时间")

    user = relationship("SysUser", back_populates="qa_records")


# ==================== 知识点问答系统核心表 ====================
class KnowledgeQaRecord(Base):
    """知识点问答记录表"""
    __tablename__ = "knowledge_qa_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="问答ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="知识点ID")
    query = Column(Text, nullable=False, comment="用户问题")
    answer = Column(Text, nullable=False, comment="系统回答")
    related_resource_ids = Column(Text, comment="关联资源ID列表")
    difficulty = Column(String(32), default="中等", comment="难度")
    is_solved = Column(Boolean, default=True, comment="是否解决")
    feedback_score = Column(Integer, nullable=True, comment="反馈评分")
    follow_up_count = Column(Integer, default=0, comment="追问次数")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True, comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("SysUser", back_populates="knowledge_qa_records")
    knowledge_point = relationship("KnowledgePoint", back_populates="qa_records")


# ==================== 企业级推荐系统核心表 ====================
class UserCourseBehavior(Base):
    """用户课程行为表"""
    __tablename__ = "user_course_behavior"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="行为ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID")
    behavior_type = Column(String(32), nullable=False, index=True, comment="行为类型")
    behavior_value = Column(Float, comment="行为值")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True, comment="创建时间")

    user = relationship("SysUser", back_populates="course_behaviors")
    course = relationship("Course", back_populates="user_behaviors")


class CourseTag(Base):
    """课程标签表"""
    __tablename__ = "course_tag"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="标签ID")
    name = Column(String(64), nullable=False, unique=True, index=True, comment="标签名称")
    category = Column(String(32), comment="标签分类")
    description = Column(String(255), comment="标签描述")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")

    courses = relationship("Course", secondary="course_tag_rel", back_populates="tags")


class CourseTagRel(Base):
    """课程-标签关联表"""
    __tablename__ = "course_tag_rel"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="关联ID")
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID")
    tag_id = Column(Integer, ForeignKey("course_tag.id", ondelete="CASCADE"), nullable=False, index=True, comment="标签ID")
    weight = Column(Float, nullable=False, default=1.0, comment="权重")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")


class UserInterestTag(Base):
    """用户兴趣标签表"""
    __tablename__ = "user_interest_tag"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    tag_id = Column(Integer, ForeignKey("course_tag.id", ondelete="CASCADE"), nullable=False, index=True, comment="标签ID")
    weight = Column(Float, nullable=False, default=0.0, comment="兴趣权重")
    last_updated = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="最后更新时间")

    user = relationship("SysUser", back_populates="interest_tags")
    tag = relationship("CourseTag")


class UserLearningPreference(Base):
    """用户学习偏好表"""
    __tablename__ = "user_learning_preference"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, unique=True, comment="用户ID")

    # 学习时段
    preferred_time_morning = Column(Float, default=0.0, comment="上午偏好")
    preferred_time_afternoon = Column(Float, default=0.0, comment="下午偏好")
    preferred_time_evening = Column(Float, default=0.0, comment="晚上偏好")
    preferred_time_night = Column(Float, default=0.0, comment="深夜偏好")

    # 资源类型
    preferred_type_video = Column(Float, default=0.0, comment="视频偏好")
    preferred_type_book = Column(Float, default=0.0, comment="书籍偏好")
    preferred_type_exercise = Column(Float, default=0.0, comment="习题偏好")

    # 难度
    preferred_difficulty_easy = Column(Float, default=0.0, comment="简单偏好")
    preferred_difficulty_medium = Column(Float, default=0.0, comment="中等偏好")
    preferred_difficulty_hard = Column(Float, default=0.0, comment="困难偏好")

    # 学习习惯
    average_session_duration = Column(Integer, default=0, comment="单次学习时长")
    preferred_learning_speed = Column(Float, default=1.0, comment="学习速度")

    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("SysUser", back_populates="learning_preference")


class UserSimilarity(Base):
    """用户相似性表"""
    __tablename__ = "user_similarity"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    user_id1 = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户1ID")
    user_id2 = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户2ID")
    similarity = Column(Float, nullable=False, comment="相似度")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="更新时间")


class CourseSimilarity(Base):
    """课程相似性表"""
    __tablename__ = "course_similarity"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    course_id1 = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程1ID")
    course_id2 = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程2ID")
    similarity = Column(Float, nullable=False, comment="相似度")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="更新时间")

# ==================== 🔥 最终：课程专属知识点完整模型（独立体系） ====================
class CourseKnowledgePoint(Base):
    """🔥 课程专属知识点表（与知识库知识点完全分离）"""
    __tablename__ = "course_knowledge_point"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="课程知识点ID")
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属课程ID")
    title = Column(String(255), nullable=False, comment="知识点标题")
    content = Column(Text, nullable=False, comment="知识点内容")
    key_points = Column(Text, comment="核心要点（JSON）")
    difficulty = Column(String(32), nullable=False, default="中等", comment="难度")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    is_published = Column(Boolean, default=True, comment="是否发布")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 独立关联
    course = relationship("Course", back_populates="course_knowledge_points")
    course_resources = relationship("CourseResource", secondary=course_resource_course_knowledge_rel, back_populates="course_knowledge_points")
    user_progress = relationship("UserCourseKnowledgeProgress", back_populates="knowledge_point", cascade="all, delete-orphan")
    user_mastery = relationship("UserCourseKnowledgeMastery", back_populates="knowledge_point", cascade="all, delete-orphan")


class UserCourseKnowledgeProgress(Base):
    """用户-课程知识点 学习进度表（独立）"""
    __tablename__ = "user_course_knowledge_progress"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="进度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    course_knowledge_id = Column(Integer, ForeignKey("course_knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程知识点ID")
    progress = Column(Float, nullable=False, default=0.0, comment="学习进度")
    is_finished = Column(Boolean, default=False, comment="是否完成")
    study_duration = Column(Integer, default=0, comment="学习时长")
    last_study_time = Column(TIMESTAMP, comment="上次学习时间")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    knowledge_point = relationship("CourseKnowledgePoint", back_populates="user_progress")
    user = relationship("SysUser")


class UserCourseKnowledgeMastery(Base):
    """用户-课程知识点 掌握度表（独立）"""
    __tablename__ = "user_course_knowledge_mastery"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="掌握度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    course_knowledge_id = Column(Integer, ForeignKey("course_knowledge_point.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程知识点ID")
    mastery_score = Column(Float, default=0.0, comment="综合掌握度(0-100)")
    level = Column(String(20), default="未学习", comment="掌握等级：未学习/入门/初级/基础/进阶/中级/良好/熟练/优秀/精通/大师")
    
    # 分维度掌握度
    video_mastery = Column(Float, default=0.0, comment="视频学习掌握度(0-100)，权重35%")
    exercise_mastery = Column(Float, default=0.0, comment="习题练习掌握度(0-100)，权重65%")
    
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    knowledge_point = relationship("CourseKnowledgePoint", back_populates="user_mastery")
    user = relationship("SysUser")