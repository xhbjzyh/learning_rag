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
from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func

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
    title = Column(String(255), nullable=False, comment="知识点标题，用于展示与检索")
    content = Column(Text, nullable=False, comment="知识点内容，核心文本，用于向量化与展示")
    difficulty = Column(String(32), nullable=False, default="中等", comment="难度：简单/中等/困难，用于推荐过滤")
    vector_id = Column(String(255), comment="向量数据库中的ID，关联FAISS向量库，用于语义检索")
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), comment="创建时间，从文档中提取的时间")
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，知识点内容修改时间")


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