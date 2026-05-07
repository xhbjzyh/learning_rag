"""
数据库ORM模型定义
定义所有数据库表结构，使用SQLAlchemy 2.0 Declarative Base
设计原则：
1. 所有表统一带 create_time/update_time 时间戳
2. 所有外键明确关联表名
3. 所有字段带 comment 注释，便于数据库管理
4. 索引仅加在高频查询字段（如 username、file_md5）
"""
# ==================== 第三方库导入 ====================
from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, Boolean, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# ==================== 内部模块导入 ====================
from db.sqlite_conn import Base


# ==================== 用户模块模型 ====================
class SysRole(Base):
    """系统角色表
    用于权限控制，目前预设两个角色：
    - admin：管理员，可审核文档、管理用户、查看统计
    - user：普通用户，可上传文档、检索知识、收藏、查看推荐
    """
    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="角色ID，主键自增")
    role_name = Column(String(32), nullable=False, unique=True, comment="角色名称，唯一标识：admin/user")
    description = Column(String(255), comment="角色描述，说明该角色的权限范围")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，插入时自动生成")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，更新时自动刷新")


class SysUser(Base):
    """系统用户表
    存储用户登录信息与基础状态
    密码设计：使用 bcrypt 加密存储，严禁明文保存
    """
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID，主键自增")
    username = Column(String(32), nullable=False, unique=True, index=True, comment="用户名，唯一，加索引用于登录查询")
    password = Column(String(255), nullable=False, comment="密码，bcrypt加密存储，长度预留足够")
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False, comment="角色ID，关联sys_role表")
    is_active = Column(Integer, nullable=False, default=1, comment="账号是否启用，1=启用，0=禁用，用于封禁用户")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，注册时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，信息修改时间")

    # 新增关联
    exercise_records = relationship("UserExerciseRecord", back_populates="user", cascade="all, delete-orphan")
    knowledge_mastery = relationship("UserKnowledgeMastery", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    """用户画像/学习进度表
    存储用户的学习数据与标签权重，用于个性化推荐
    设计说明：与sys_user一对一关联，每个用户只有一条画像记录
    """
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="画像ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, unique=True, comment="用户ID，关联sys_user表，唯一约束")
    total_study_time = Column(Integer, default=0, comment="总学习时长，单位：分钟，累计统计")
    completed_points = Column(Integer, default=0, comment="已完成知识点数量，用于学习进度展示")
    current_level = Column(String(32), default="入门", comment="当前学习等级，如：入门/进阶/精通")
    preferred_difficulty = Column(String(32), default="中等", comment="偏好难度，用于推荐过滤：简单/中等/困难")
    tag_weight = Column(Text, default="{}", comment="标签权重字典，JSON格式：{标签ID: 权重值0-1}，用于个性化推荐")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，用户注册时自动创建")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，学习数据变化时刷新")
    total_study_duration = Column(Integer, nullable=False, default=0, comment="总学习时长，单位：秒")
    finished_points_count = Column(Integer, nullable=False, default=0, comment="已完成知识点数量")
    average_score = Column(Float, nullable=False, default=0.0, comment="平均练习得分")
    weak_tags = Column(Text, comment="薄弱知识点标签，JSON格式")
    strong_tags = Column(Text, comment="优势知识点标签，JSON格式")

    # 新增关联
    user = relationship("SysUser", back_populates="profile")


class UserLearningHistory(Base):
    """用户学习历史表（保留原有表，用于基础学习轨迹展示）
    记录用户每次学习知识点的行为，用于学习轨迹展示
    设计说明：与sys_user、knowledge_point多对一关联
    """
    __tablename__ = "user_learning_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="历史ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="用户ID，关联sys_user表")
    point_id = Column(Integer, ForeignKey("knowledge_point.id"), nullable=False, comment="知识点ID，关联knowledge_point表")
    study_duration = Column(Integer, comment="本次学习时长，单位：分钟，用于统计学习投入")
    is_mastered = Column(Integer, default=0, comment="是否已掌握，1=是，0=否，可由用户标记或系统判定")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="学习时间，本次学习的开始时间")


class UserLearningRecord(Base):
    """用户学习行为记录表（新增，用于个性化推荐权重计算）
    详细记录用户每次学习知识点的行为，用于动态更新用户画像标签权重
    设计说明：与sys_user、knowledge_point多对一关联
    """
    __tablename__ = "user_learning_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID，关联sys_user表，级联删除")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID，关联knowledge_point表，级联删除")
    learn_duration = Column(Integer, default=0, comment="本次学习时长，单位：秒，用于统计学习投入")
    is_collected = Column(Boolean, default=False, comment="是否收藏，True=已收藏，False=未收藏")
    feedback_score = Column(Integer, nullable=True, comment="用户反馈评分，1-5分，5分最感兴趣，用于权重计算")
    is_finished = Column(Boolean, default=False, comment="是否完成学习，True=已完成，False=未完成")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="学习时间，本次学习的开始时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，学习行为变化时刷新")


class UserFeedback(Base):
    """用户反馈表
    收集用户对知识点或系统的反馈，用于优化内容与推荐
    """
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="反馈ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="用户ID，关联sys_user表")
    point_id = Column(Integer, ForeignKey("knowledge_point.id"), comment="关联知识点ID，可为空，反馈系统问题时不关联")
    feedback_type = Column(String(32), nullable=False, comment="反馈类型，如：内容错误/建议/其他")
    content = Column(Text, nullable=False, comment="反馈内容，详细描述问题或建议")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，反馈提交时间")


# ==================== 知识库模块模型 ====================
class KnowledgeCategory(Base):
    """知识库分类表
    对文档进行分类管理，便于检索与推荐
    预设分类：如计算机科学、数学、英语等
    """
    __tablename__ = "knowledge_category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID，主键自增")
    category_name = Column(String(64), nullable=False, unique=True, comment="分类名称，唯一标识")
    description = Column(String(255), comment="分类描述，说明该分类的内容范围")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class KnowledgeDocument(Base):
    """知识库文档表
    存储用户上传的文档信息，是知识点的来源
    防重复设计：通过 file_md5 字段实现，相同文件只存储一份
    审核流程：用户上传 → 待审核 → 管理员审核通过/驳回
    私有/公开：通过 is_public 字段控制，0=私有，1=公开
    """
    __tablename__ = "knowledge_document"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文档ID，主键自增")
    title = Column(String(128), nullable=False, comment="文档标题，用户自定义或从文件名提取")
    file_name = Column(String(255), nullable=False, comment="原始文件名，包含后缀")
    file_path = Column(String(512), nullable=False, comment="文件存储路径，绝对路径，便于服务器读取")
    file_md5 = Column(String(32), nullable=False, index=True, comment="文件MD5哈希值，用于防重复上传，加索引用于快速查询")
    file_type = Column(String(32), nullable=False, comment="文件类型，标识文件格式：txt/pdf/docx")
    file_size = Column(Integer, comment="文件大小，单位：字节，用于统计与展示")
    category_id = Column(Integer, ForeignKey("knowledge_category.id"), comment="所属分类ID，关联knowledge_category表")
    upload_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="上传用户ID，关联sys_user表")
    audit_status = Column(Integer, nullable=False, default=0, comment="审核状态：0=待审核，1=已通过，2=已驳回")
    audit_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="审核人ID，关联sys_user表，仅管理员可审核")
    audit_time = Column(TIMESTAMP, comment="审核时间，审核操作的时间")
    audit_remark = Column(String(255), comment="审核备注，审核通过或驳回的原因")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，文档上传时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，文档信息修改或审核状态变化时间")
    is_public = Column(Integer, nullable=False, default=0, comment="是否公开：0=私有，1=公开")
    process_status = Column(Integer, nullable=False, default=0, comment="知识点处理状态：0=待处理，1=处理中，2=处理完成，3=处理失败")
    process_message = Column(String(255), comment="处理状态信息")

    # 新增关联
    knowledge_points = relationship("KnowledgePoint", back_populates="document", cascade="all, delete-orphan")


class KnowledgeTag(Base):
    """知识点标签表（新增，用于个性化推荐）
    给每个知识点打分类标签，是基于内容推荐的基础
    """
    __tablename__ = "knowledge_tag"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="标签ID，主键自增")
    name = Column(String(50), nullable=False, unique=True, index=True, comment="标签名称，唯一标识，如：Python、机器学习、RAG")
    description = Column(String(200), nullable=True, comment="标签描述，说明该标签的内容范围")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class KnowledgePointTagRel(Base):
    """知识点-标签多对多关联表（新增，用于个性化推荐）
    建立知识点和标签的关联关系，一个知识点可以有多个标签，一个标签可以对应多个知识点
    """
    __tablename__ = "knowledge_point_tag_rel"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="关联ID，主键自增")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID，关联knowledge_point表，级联删除")
    tag_id = Column(Integer, ForeignKey("knowledge_tag.id", ondelete="CASCADE"), nullable=False, comment="标签ID，关联knowledge_tag表，级联删除")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")


class KnowledgePoint(Base):
    """知识点表（从文档中提取的结构化内容）
    是RAG系统的核心数据单元，用于语义检索与推荐
    向量化设计：vector_id 关联 FAISS 向量库中的向量
    """
    __tablename__ = "knowledge_point"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="知识点ID，主键自增")
    doc_id = Column(Integer, ForeignKey("knowledge_document.id"), nullable=False, comment="所属文档ID，关联knowledge_document表")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="所属用户ID，实现私有库隔离")
    title = Column(String(255), nullable=False, comment="知识点标题，用于展示与检索")
    content = Column(Text, nullable=False, comment="知识点内容，核心文本，用于向量化与展示")
    key_points = Column(Text, comment="核心要点，JSON数组格式")
    difficulty = Column(String(32), nullable=False, default="中等", comment="难度：简单/中等/困难，用于推荐过滤")
    pre_knowledge = Column(Text, comment="前置知识，JSON数组格式")
    common_mistakes = Column(Text, comment="常见错误，JSON数组格式")
    related_topics = Column(Text, comment="关联知识点，JSON数组格式")
    chunk_index = Column(Integer, comment="原始文档块索引")
    vector_id = Column(String(255), comment="向量数据库中的ID，关联FAISS向量库，用于语义检索")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，从文档中提取的时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，知识点内容修改时间")

    # 新增关联
    document = relationship("KnowledgeDocument", back_populates="knowledge_points")
    user = relationship("SysUser")
    tags = relationship("KnowledgeTag", secondary="knowledge_point_tag_rel", backref="points")
    exercises = relationship("Exercise", secondary="exercise_knowledge", back_populates="knowledge_points")
    user_mastery = relationship("UserKnowledgeMastery", back_populates="knowledge_point", cascade="all, delete-orphan")


# ==================== 审核模块模型 ====================
class AuditRecord(Base):
    """审核记录表
    记录每次文档审核的操作，便于追溯审核历史
    设计说明：与knowledge_document、sys_user多对一关联
    """
    __tablename__ = "audit_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="审核记录ID，主键自增")
    doc_id = Column(Integer, ForeignKey("knowledge_document.id"), nullable=False, comment="文档ID，关联knowledge_document表")
    auditor_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="审核人ID，关联sys_user表")
    audit_status = Column(Integer, nullable=False, comment="审核状态：1=通过，2=驳回")
    audit_remark = Column(String(255), comment="审核备注，审核通过或驳回的详细原因")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="审核时间，审核操作的时间")


# ==================== 推荐模块模型 ====================
class RecommendationRecord(Base):
    """推荐记录表
    记录系统为用户推荐的知识点，用于分析推荐效果
    效果分析：通过 is_clicked 字段统计推荐点击率
    """
    __tablename__ = "recommendation_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="推荐ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="用户ID，关联sys_user表")
    point_id = Column(Integer, ForeignKey("knowledge_point.id"), nullable=False, comment="推荐的知识点ID，关联knowledge_point表")
    recommendation_reason = Column(Text, comment="推荐理由，如：基于收藏的相似推荐/热门推荐")
    is_clicked = Column(Integer, default=0, comment="是否点击，1=是，0=否，用于评估推荐效果")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="推荐时间，系统生成推荐的时间")


# ==================== 新增：内容公开申请表 ====================
class ContentPublicApply(Base):
    """内容公开申请表
    记录用户申请将私有内容转为公共内容的完整审核流程
    状态流转：待审核(0) → 已通过(1)/已驳回(2)
    """
    __tablename__ = "content_public_apply"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="申请ID，主键自增")
    doc_id = Column(Integer, ForeignKey("knowledge_document.id", ondelete="CASCADE"), nullable=False, comment="文档ID")
    apply_user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="申请人ID")
    apply_status = Column(Integer, nullable=False, default=0, comment="申请状态：0=待审核，1=已通过，2=已驳回")
    apply_remark = Column(String(255), comment="申请理由")
    audit_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="审核人ID")
    audit_remark = Column(String(255), comment="审核备注")
    audit_time = Column(TIMESTAMP, comment="审核时间")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="申请时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


# ==================== 新增：错题记录表 ====================
class WrongQuestion(Base):
    """错题记录表
    记录用户做错的题目和练习记录
    """
    __tablename__ = "wrong_question"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="错题ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    question = Column(Text, nullable=False, comment="题目内容")
    user_answer = Column(Text, comment="用户答案")
    correct_answer = Column(Text, comment="正确答案")
    error_reason = Column(String(255), comment="错误原因")
    master_level = Column(Integer, nullable=False, default=0, comment="掌握程度：0=未掌握，1=部分掌握，2=已掌握")
    wrong_count = Column(Integer, nullable=False, default=1, comment="错误次数")
    last_review_time = Column(TIMESTAMP, comment="上次复习时间")
    next_review_time = Column(TIMESTAMP, comment="下次复习时间（艾宾浩斯遗忘曲线）")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


# ==================== 新增：学习进度表 ====================
class LearningProgress(Base):
    """学习进度表
    记录用户对每个知识点的学习进度
    """
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="进度ID")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    progress = Column(Float, nullable=False, default=0.0, comment="学习进度：0-100%")
    is_finished = Column(Boolean, nullable=False, default=False, comment="是否完成学习")
    study_duration = Column(Integer, nullable=False, default=0, comment="累计学习时长，单位：秒")
    last_study_time = Column(TIMESTAMP, comment="上次学习时间")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


# ==================== 新增：习题系统模型 ====================
# 习题-知识点关联表（多对多）
exercise_knowledge = Table(
    "exercise_knowledge",
    Base.metadata,
    Column("exercise_id", Integer, ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True),
    Column("knowledge_point_id", Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), primary_key=True),
    comment="习题-知识点关联表"
)


class Exercise(Base):
    """习题表
    存储所有习题信息，支持多种题型
    权限控制：仅管理员和审核员可添加/编辑/删除
    """
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="习题ID，主键自增")
    title = Column(String(500), nullable=False, comment="题目内容")
    type = Column(String(20), nullable=False, comment="题型：single_choice/multiple_choice/fill_blank/essay")
    difficulty = Column(String(20), default="中等", comment="难度：简单/中等/困难")
    answer = Column(Text, nullable=False, comment="正确答案")
    analysis = Column(Text, comment="答案解析")
    score = Column(Float, default=10.0, comment="题目分值")
    create_user_id = Column(Integer, ForeignKey("sys_user.id"), comment="创建人ID（管理员/审核员）")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    options = relationship("ExerciseOption", back_populates="exercise", cascade="all, delete-orphan")
    knowledge_points = relationship("KnowledgePoint", secondary="exercise_knowledge", back_populates="exercises")
    user_records = relationship("UserExerciseRecord", back_populates="exercise", cascade="all, delete-orphan")
    create_user = relationship("SysUser")


class ExerciseOption(Base):
    """选择题选项表
    存储单选题和多选题的选项
    """
    __tablename__ = "exercise_option"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="选项ID，主键自增")
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), comment="所属习题ID")
    content = Column(String(500), nullable=False, comment="选项内容")
    is_correct = Column(Boolean, default=False, comment="是否正确选项")
    order = Column(Integer, comment="选项顺序")

    # 关联
    exercise = relationship("Exercise", back_populates="options")

    # 🔥 新增：动态生成 option_label（1→A, 2→B...）
    @property
    def option_label(self):
        if self.order:
            return chr(ord('A') + self.order - 1)
        return ""

    # 🔥 新增：别名属性，兼容响应模型
    @property
    def option_content(self):
        return self.content


class UserExerciseRecord(Base):
    """用户答题记录表
    记录用户每次答题的结果
    """
    __tablename__ = "user_exercise_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False, comment="习题ID")
    user_answer = Column(Text, comment="用户答案")
    score = Column(Float, comment="得分")
    is_correct = Column(Boolean, comment="是否答对")
    feedback = Column(Text, comment="批改评语")
    answer_time = Column(Integer, comment="答题时长（秒）")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="答题时间")

    # 关联
    user = relationship("SysUser", back_populates="exercise_records")
    exercise = relationship("Exercise", back_populates="user_records")


class UserKnowledgeMastery(Base):
    """用户知识点掌握度表
    基于答题结果计算的知识点掌握度
    """
    __tablename__ = "user_knowledge_mastery"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="掌握度ID，主键自增")
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False, comment="知识点ID")
    mastery_score = Column(Float, default=0.0, comment="掌握度得分（0-100）")
    level = Column(String(20), default="未掌握", comment="掌握等级：未掌握/初步掌握/熟练掌握/精通")
    total_questions = Column(Integer, default=0, comment="总答题数")
    correct_questions = Column(Integer, default=0, comment="答对题数")
    last_answer_time = Column(TIMESTAMP, comment="最后答题时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    user = relationship("SysUser", back_populates="knowledge_mastery")
    knowledge_point = relationship("KnowledgePoint", back_populates="user_mastery")