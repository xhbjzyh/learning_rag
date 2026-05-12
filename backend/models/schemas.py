"""
Pydantic请求/响应模型定义（对齐最终版数据库 | 双知识点体系分离）
"""
from typing import Optional, TypeVar, Generic, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

# 泛型定义
T = TypeVar("T")

# ==================== 基础 Schema 配置（全局统一） ====================
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # ✅ 核心修复：处理 None 值，永不报错！
            datetime: lambda v: v.isoformat() if v is not None else None
        }
    )

# 通用成功响应
class SuccessResponse(BaseSchema, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: Optional[T] = None

# ==================== 用户模块 ====================
class UserRegisterRequest(BaseSchema):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=32)
    confirm_password: str

class UserLoginRequest(BaseSchema):
    username: str
    password: str

class UserInfoResponse(BaseSchema):
    id: int
    username: str
    role_id: int
    is_active: int
    # ✅ 时间改为可选
    create_time: Optional[datetime] = None

class UserLoginResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user_info: UserInfoResponse

class UserPasswordUpdateRequest(BaseSchema):
    old_password: str
    new_password: str = Field(min_length=6, max_length=32)
    confirm_new_password: str

# 管理员安全操作
class AdminCreateAuditorRequest(BaseSchema):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=32)

class AdminCreateUserRequest(BaseSchema):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=32)
    role_id: int = Field(ge=2, le=3, description="2=审核员 3=普通用户")

class AdminResetPasswordRequest(BaseSchema):
    user_id: int = Field(description="要重置密码的用户ID")
    new_password: str = Field(min_length=6, max_length=32, description="新密码")

# ==================== 知识库模块 ====================
class CategoryCreateRequest(BaseSchema):
    category_name: str = Field(min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)

class CategoryInfoResponse(BaseSchema):
    id: int
    category_name: str
    description: Optional[str]
    create_time: Optional[datetime] = None

class DocumentUploadResponse(BaseSchema):
    id: int
    title: str
    file_name: str
    file_type: str
    audit_status: int

class DocumentInfoResponse(BaseSchema):
    id: int
    title: str
    file_name: str
    file_type: str
    file_size: Optional[int]
    category_id: Optional[int]
    audit_status: int
    process_status: int = 0  # 🔥 新增：处理状态 0=待处理 1=解析中 2=已解析 3=失败
    is_public: int = 0  # 🔥 新增：是否公开 0=私有 1=公开
    upload_username: Optional[str] = None  # 🔥 新增：上传用户名(仅公共文档)
    create_time: Optional[datetime] = None

class DocumentUpdateRequest(BaseSchema):
    title: Optional[str] = Field(min_length=1, max_length=128, description="文档标题")
    category_id: Optional[int] = Field(None, description="所属分类ID")

class DocumentAuditRequest(BaseSchema):
    audit_status: int = Field(description="审核状态：1=通过，2=驳回")
    audit_remark: Optional[str] = Field(None, max_length=255, description="审核备注")

# ==================== 🔥 知识库知识点（独立体系） ====================
class KnowledgePointCreate(BaseSchema):
    doc_id: int
    user_id: int
    title: str
    content: str
    difficulty: str = "中等"
    key_points: Optional[str] = None
    pre_knowledge: Optional[str] = None
    common_mistakes: Optional[str] = None

class KnowledgePointUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None
    key_points: Optional[str] = None
    pre_knowledge: Optional[str] = None
    common_mistakes: Optional[str] = None

class KnowledgePointResponse(BaseSchema):
    id: int
    doc_id: int
    user_id: int
    title: str
    content: str
    key_points: Optional[str]
    difficulty: str
    pre_knowledge: Optional[str]
    common_mistakes: Optional[str]
    vector_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

# ==================== 🔥 课程专属知识点（独立体系 | 新增全套） ====================
class CourseKnowledgePointCreate(BaseSchema):
    course_id: int
    title: str
    content: str
    key_points: Optional[str] = None
    difficulty: str = "中等"
    sort_order: int = 0
    is_published: bool = True

class CourseKnowledgePointUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    key_points: Optional[str] = None
    difficulty: Optional[str] = None
    sort_order: Optional[int] = None
    is_published: Optional[bool] = None

class CourseKnowledgePointResponse(BaseSchema):
    id: int
    course_id: int
    title: str
    content: str
    key_points: Optional[str]
    difficulty: str
    sort_order: int
    is_published: bool
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

# 课程知识点学习进度
class UserCourseKnowledgeProgressResponse(BaseSchema):
    id: int
    user_id: int
    course_knowledge_id: int
    progress: float
    is_finished: bool
    study_duration: int
    last_study_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

# 课程知识点掌握度
class UserCourseKnowledgeMasteryResponse(BaseSchema):
    id: int
    user_id: int
    course_knowledge_id: int
    mastery_score: float
    level: str
    update_time: Optional[datetime] = None

# ==================== 习题模块 ====================
# 题型枚举（严格约束）
class ExerciseType(str, Enum):
    SINGLE_CHOICE = "single_choice"    # 单选题
    TRUE_FALSE = "true_false"          # 判断题
    MULTIPLE_CHOICE = "multiple_choice"# 多选题

# 习题选项
class ExerciseOptionBase(BaseSchema):
    option_label: str
    option_content: str
    is_correct: bool

class ExerciseOptionCreate(ExerciseOptionBase):
    pass

class ExerciseOptionItem(ExerciseOptionBase):
    id: int
    exercise_id: int

# 习题主体
class ExerciseCreate(BaseSchema):
    title: str
    type: ExerciseType
    difficulty: str
    analysis: Optional[str] = None
    knowledge_ids: List[int]
    options: List[ExerciseOptionCreate]
    course_knowledge_ids: List[int] = Field(default_factory=list)  # 新增


class ExerciseUpdate(BaseSchema):
    id: int
    title: Optional[str] = None
    type: Optional[ExerciseType] = None
    difficulty: Optional[str] = None
    analysis: Optional[str] = None
    knowledge_ids: Optional[List[int]] = None
    options: Optional[List[ExerciseOptionCreate]] = None
    course_knowledge_ids: Optional[List[int]] = None  # 新增

class ExerciseItem(BaseSchema):
    id: int
    title: str
    type: ExerciseType
    difficulty: str
    analysis: Optional[str]
    create_user_id: Optional[int]
    create_time: Optional[datetime] = None
    options: List[ExerciseOptionItem] = []

class ExerciseListResponse(BaseSchema):
    total: int
    list: List[ExerciseItem]
    page: int
    size: int

# ==================== 答题记录与错题本 ====================
class ExerciseSubmitRequest(BaseSchema):
    exercise_id: int
    user_answer: str
    answer_time: Optional[int] = None

class ExerciseSubmitResponse(BaseSchema):
    exercise_id: int
    is_correct: bool
    user_answer: str
    correct_answer: str
    score: float
    analysis: Optional[str] = None

class ExerciseSubmit(BaseModel):
    exercise_id: int
    user_answer: str
    answer_time: Optional[int] = None

class UserExerciseRecordItem(BaseSchema):
    id: int
    user_id: int
    exercise_id: int
    user_answer: str
    score: float
    is_correct: bool
    feedback: Optional[str]
    answer_time: Optional[int]
    create_time: Optional[datetime] = None

class WrongQuestionItem(BaseSchema):
    id: int
    user_id: int
    exercise_id: int
    # ✅ 修复：数据库是 question_title，不是 question
    question_title: str
    user_answer: str
    correct_answer: str
    error_reason: Optional[str]
    master_level: int
    wrong_count: int
    last_review_time: Optional[str] = None
    next_review_time: Optional[str] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None

# ==================== 用户画像与推荐 ====================
class TagInfo(BaseSchema):
    tag_id: int
    tag_name: str
    avg_mastery: Optional[float] = None

class UserProfileResponse(BaseSchema):
    user_id: int
    total_study_time: int
    completed_points: int
    current_level: str
    preferred_difficulty: str
    tag_weight: str
    total_study_duration: int
    finished_points_count: int
    average_score: float
    weak_tags: str
    strong_tags: str
    # 三源融合字段
    video_completion_rate: float
    video_study_ratio: float
    exercise_accuracy: float
    average_answer_speed: float
    qa_count: int
    qa_solve_rate: float
    average_qa_score: float
    comprehensive_ability: float
    learning_efficiency: float
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class KnowledgePointRecommendItem(BaseSchema):
    id: int
    title: str
    content: str
    difficulty: str
    key_points: Optional[str]
    doc_id: Optional[int]

class LearningPathItem(KnowledgePointRecommendItem):
    order: int
    reason: Optional[str] = "基于你的薄弱点推荐"
    suggestion: Optional[str] = None

# ==================== 课程系统 ====================
class CourseCategoryItem(BaseSchema):
    id: int
    name: str
    parent_id: int
    level: int
    sort_order: int
    description: Optional[str]
    icon: Optional[str]
    children: List["CourseCategoryItem"] = []

class CourseListItem(BaseSchema):
    id: int
    title: str
    cover_url: Optional[str]
    description: Optional[str]
    lecturer: Optional[str]
    category_id: int
    difficulty: str
    view_count: int
    is_public: int
    create_time: Optional[datetime] = None

class CourseResourceItem(BaseSchema):
    id: int
    course_id: int
    title: str
    type: str
    description: Optional[str]
    url: Optional[str]
    duration: Optional[int]
    file_size: Optional[int]
    file_type: Optional[str]
    exercise_id: Optional[int]
    sort_order: int
    is_published: bool
    create_time: Optional[datetime] = None

# 简化知识点模型
class KnowledgePointSimpleItem(BaseSchema):
    id: int
    title: str
    content: str
    difficulty: str

class ExerciseSimpleItem(BaseSchema):
    id: int
    title: str
    type: str
    difficulty: str
    score: float

class CourseDetailItem(BaseSchema):
    id: int
    title: str
    cover_url: Optional[str]
    description: Optional[str]
    lecturer: Optional[str]
    category_id: int
    difficulty: str
    view_count: int
    is_public: int
    resources: List[CourseResourceItem]
    # 双知识点体系分离展示
    knowledge_points: List[KnowledgePointSimpleItem]
    course_knowledge_points: List[CourseKnowledgePointResponse]
    exercises: List[ExerciseSimpleItem]
    user_progress: Optional[dict] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

# 管理员课程管理
class AdminCourseCreateRequest(BaseSchema):
    title: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    lecturer: Optional[str] = None
    category_id: int
    difficulty: str = "中等"
    is_published: bool = True
    is_public: int = 1

class AdminCourseUpdateRequest(BaseSchema):
    title: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    lecturer: Optional[str] = None
    category_id: Optional[int] = None
    difficulty: Optional[str] = None
    is_published: Optional[bool] = None
    is_public: Optional[int] = None

# ==================== 课程资源管理 ====================
# 资源类型子模型
class CourseResourceVideoCreate(BaseSchema):
    video_url: str
    duration: Optional[int] = None
    cover_url: Optional[str] = None

class CourseResourceDocumentCreate(BaseSchema):
    file_url: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class CourseResourceExerciseCreate(BaseSchema):
    exercise_id: int

# 主创建/更新模型
class CourseResourceCreate(BaseSchema):
    title: str = Field(min_length=1, max_length=255)
    type: str = Field(description="videos/document/exercise")
    description: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    sort_order: int = 0
    is_published: bool = True
    # 关联知识点
    knowledge_ids: List[int] = Field(default_factory=list)
    course_knowledge_ids: List[int] = Field(default_factory=list)

class CourseResourceUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    sort_order: Optional[int] = None
    is_published: Optional[bool] = None
    knowledge_ids: Optional[List[int]] = None
    course_knowledge_ids: Optional[List[int]] = None

# 响应模型
class CourseResourceResponse(BaseSchema):
    id: int
    course_id: int
    title: str
    type: str
    description: Optional[str]
    url: Optional[str]
    duration: Optional[int]
    file_size: Optional[int]
    file_type: Optional[str]
    exercise_id: Optional[int]
    sort_order: int
    is_published: bool
    upload_user_id: Optional[int]
    download_count: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    # 双知识点关联
    knowledge_ids: List[int] = []
    course_knowledge_ids: List[int] = []

# 文件上传专用
class CourseResourceFileUpload(BaseSchema):
    course_id: int
    title: str
    type: str
    knowledge_ids: list[int]
    course_knowledge_ids: list[int] = []
    sort_order: int = 0
    description: Optional[str] = None

# ==================== 学习进度 ====================
class ResourceProgressUpdate(BaseSchema):
    progress: Optional[float] = Field(None, ge=0, le=100)
    is_finished: Optional[bool] = None
    total_study_duration: Optional[int] = None
    study_duration: Optional[float] = 0.0
    # 视频
    watch_position: Optional[int] = None
    pause_count: Optional[int] = None
    fast_forward_count: Optional[int] = None
    rewind_count: Optional[int] = None
    # 习题
    exercise_score: Optional[float] = None
    correct_count: Optional[int] = None
    total_count: Optional[int] = None
    wrong_question_ids: Optional[str] = None
    average_answer_time: Optional[float] = None
    # 文档
    read_pages: Optional[int] = None
    total_pages: Optional[int] = None
    highlight_count: Optional[int] = None
    note_count: Optional[int] = None

class UserCourseProgressResponse(BaseSchema):
    id: int
    user_id: int
    course_id: int
    progress: float
    is_finished: bool
    last_study_time: Optional[datetime] = None
    total_study_duration: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class UserResourceProgressResponse(BaseSchema):
    id: int
    user_id: int
    resource_id: int
    progress: float
    is_finished: bool
    last_study_time: Optional[datetime] = None
    total_study_duration: int
    study_count: int
    # 视频字段
    watch_position: int
    pause_count: int
    fast_forward_count: int
    rewind_count: int
    completion_rate: float
    # 习题字段
    exercise_score: Optional[float]
    correct_count: int
    total_count: int
    wrong_question_ids: Optional[str]
    average_answer_time: Optional[float]
    # 文档字段
    read_pages: int
    total_pages: int
    highlight_count: int
    note_count: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

# ==================== 知识点问答系统 ====================
class KnowledgeQaCreate(BaseSchema):
    knowledge_point_id: int
    query: str
    answer: str
    related_resource_ids: Optional[str] = None
    difficulty: str = "中等"
    is_solved: bool = True
    follow_up_count: int = 0

class KnowledgeQaFeedbackUpdate(BaseSchema):
    feedback_score: Optional[int] = Field(None, ge=1, le=5)
    is_solved: Optional[bool] = None
    follow_up_count: Optional[int] = None

class KnowledgeQaResponse(BaseSchema):
    id: int
    user_id: int
    knowledge_point_id: int
    query: str
    answer: str
    related_resource_ids: Optional[str]
    difficulty: str
    is_solved: bool
    feedback_score: Optional[int]
    follow_up_count: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

# ==================== 通用分页响应 ====================
class PageResponse(BaseSchema, Generic[T]):
    total: int
    list: List[T]
    page: int
    size: int