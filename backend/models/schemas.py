"""
Pydantic请求/响应模型定义
"""
from typing import Optional, TypeVar, Generic, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

T = TypeVar("T")

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class SuccessResponse(BaseSchema, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: Optional[T] = None

# ==================== 用户模型 ====================
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
    create_time: datetime

class UserLoginResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user_info: UserInfoResponse

class UserPasswordUpdateRequest(BaseSchema):
    old_password: str
    new_password: str = Field(min_length=6, max_length=32)
    confirm_new_password: str

# 🔴 新增：管理员创建账号安全请求模型（修复敏感参数漏洞）
class AdminCreateAuditorRequest(BaseSchema):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=32)

class AdminCreateUserRequest(BaseSchema):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=32)
    role_id: int = Field(ge=2, le=3, description="2=审核员 3=普通用户")

# ==================== 知识库模型 ====================
class CategoryCreateRequest(BaseSchema):
    category_name: str = Field(min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)

class CategoryInfoResponse(BaseSchema):
    id: int
    category_name: str
    description: Optional[str]
    create_time: datetime

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
    create_time: datetime

class KnowledgePointResponse(BaseSchema):
    id: int
    doc_id: int
    title: str
    content: str
    difficulty: str | None
    vector_id: str | None
    create_time: datetime
    update_time: datetime

class DocumentUpdateRequest(BaseSchema):
        title: Optional[str] = Field(min_length=1, max_length=128, description="文档标题")
        category_id: Optional[int] = Field(None, description="所属分类ID")
# ==================== 新增：文档审核请求模型 ====================
class DocumentAuditRequest(BaseSchema):
    audit_status: int = Field(description="审核状态：1=通过，2=驳回")
    audit_remark: Optional[str] = Field(None, max_length=255, description="审核备注")
# ==================== 新增：管理员重置密码请求模型 ====================
class AdminResetPasswordRequest(BaseSchema):
    user_id: int = Field(description="要重置密码的用户ID")
    new_password: str = Field(min_length=6, max_length=32, description="新密码")
# ===================== 习题模块模型 =====================
from typing import List, Optional
from enum import Enum

# 新增：题型枚举，严格限制输入
class ExerciseType(str, Enum):
    SINGLE_CHOICE = "single_choice"  # 单选题
    TRUE_FALSE = "true_false"        # 判断题
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题

# 习题选项
class ExerciseOptionBase(BaseModel):
    option_label: str  # 如：A、B、C、D
    option_content: str
    is_correct: bool

class ExerciseOptionCreate(ExerciseOptionBase):
    pass

class ExerciseOptionItem(ExerciseOptionBase):
    id: int
    exercise_id: int

    # 🔥 新增：允许从模型属性读取
    model_config = {
        "from_attributes": True
    }

# 习题主体
class ExerciseCreate(BaseModel):
    title: str
    exercise_type: ExerciseType  # 🔥 改为枚举类型，严格校验
    difficulty: str
    analysis: Optional[str] = None
    knowledge_ids: List[int]  # 绑定知识点id列表
    options: List[ExerciseOptionCreate]

class ExerciseUpdate(ExerciseCreate):
    id: int

class ExerciseItem(BaseModel):
    id: int
    title: str
    type: ExerciseType
    difficulty: str
    analysis: Optional[str] = None
    create_user_id: Optional[int] = None
    create_time: datetime
    options: List[ExerciseOptionItem] = []

    # 🔥 新增：允许从模型属性读取
    model_config = {
        "from_attributes": True
    }

class ExerciseListResponse(BaseModel):
    total: int
    list: List[ExerciseItem]
    page: int
    size: int
# ===================== 答题记录与错题本模型 =====================
class ExerciseSubmitRequest(BaseModel):
    """用户提交答题请求"""
    exercise_id: int
    user_answer: str  # 如："A"、"B"、"AB"
    answer_time: Optional[int] = None  # 答题时长（秒）

class ExerciseSubmitResponse(BaseModel):
    """答题结果响应"""
    exercise_id: int
    is_correct: bool
    user_answer: str
    correct_answer: str
    score: float
    analysis: Optional[str] = None

class UserExerciseRecordItem(BaseModel):
    """答题记录项"""
    id: int
    exercise_id: int
    exercise_title: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    score: float
    answer_time: Optional[int] = None
    create_time: datetime

    model_config = {
        "from_attributes": True
    }

class WrongQuestionItem(BaseModel):
    """错题本项"""
    id: int
    exercise_id: int
    exercise_title: str
    user_answer: str
    correct_answer: str
    error_reason: Optional[str] = None
    master_level: int
    wrong_count: int
    last_review_time: Optional[datetime] = None
    next_review_time: Optional[datetime] = None
    create_time: datetime

    model_config = {
        "from_attributes": True
    }
# ===================== 用户画像与推荐模型 =====================
class TagInfo(BaseSchema):
    """标签信息"""
    tag_id: int
    tag_name: str
    avg_mastery: Optional[float] = None


class UserProfileResponse(BaseSchema):
    """用户画像完整响应"""
    user_id: int
    total_study_duration: int
    finished_points_count: int
    current_level: str
    preferred_difficulty: str
    average_score: float
    total_questions: int
    correct_rate: float
    weak_tags: List[TagInfo]
    strong_tags: List[TagInfo]
    create_time: datetime
    update_time: datetime


class KnowledgePointRecommendItem(BaseSchema):
    """推荐知识点项"""
    id: int
    title: str
    content: str
    difficulty: str
    key_points: Optional[str] = None
    doc_id: Optional[int] = None


class LearningPathItem(KnowledgePointRecommendItem):
    """学习路径项"""
    order: int
    reason: Optional[str] = "基于你的薄弱点推荐"
    suggestion: Optional[str] = None  # 🔥 新增：学习建议
# ==================== 课程系统相关 Schema ====================
class CourseCategoryItem(BaseModel):
    """课程分类项"""
    id: int
    name: str
    parent_id: int
    level: int
    sort_order: int
    description: Optional[str] = None
    icon: Optional[str] = None
    children: List["CourseCategoryItem"] = []

    class Config:
        from_attributes = True

class CourseListItem(BaseModel):
    """课程列表项"""
    id: int
    title: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    lecturer: Optional[str] = None
    category_id: int
    view_count: int
    create_time: datetime

    class Config:
        from_attributes = True

class CourseResourceItem(BaseModel):
    """课程资源项（列表用）"""
    id: int
    title: str
    type: str
    url: str
    description: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    sort_order: int
    is_published: bool
    create_time: datetime

    class Config:
        from_attributes = True

class KnowledgePointSimpleItem(BaseModel):
    """知识点简项"""
    id: int
    title: str
    content: str
    difficulty: str

    class Config:
        from_attributes = True

class ExerciseSimpleItem(BaseModel):
    """习题简项"""
    id: int
    title: str
    type: str
    difficulty: str
    score: float

    class Config:
        from_attributes = True

class CourseDetailItem(BaseModel):
    """课程详情"""
    id: int
    title: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    lecturer: Optional[str] = None
    category_id: int
    view_count: int
    resources: List[CourseResourceItem]
    knowledge_points: List[KnowledgePointSimpleItem]
    exercises: List[ExerciseSimpleItem]
    user_progress: Optional[dict] = None
    create_time: datetime

    class Config:
        from_attributes = True
# ==================== 管理员课程管理 ====================
class AdminCourseCreateRequest(BaseSchema):
    title: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    lecturer: Optional[str] = None
    category_id: int
    difficulty: Optional[str] = "中等"
    is_published: bool = True

class AdminCourseUpdateRequest(BaseSchema):
    title: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    lecturer: Optional[str] = None
    category_id: Optional[int] = None
    difficulty: Optional[str] = None
    is_published: Optional[bool] = None

# ==================== 🔥 课程资源管理Schema（唯一定义，含url+文件字段） ====================
class CourseResourceVideoCreate(BaseSchema):
    """视频资料创建模型"""
    video_url: str = Field(description="视频地址")
    duration: Optional[int] = Field(None, description="视频时长(秒)")
    cover_url: Optional[str] = Field(None, description="视频封面地址")

class CourseResourceVideoUpdate(BaseSchema):
    """视频资料更新模型"""
    video_url: Optional[str] = None
    duration: Optional[int] = None
    cover_url: Optional[str] = None

class CourseResourceVideoResponse(BaseSchema):
    """视频资料响应模型"""
    id: int
    video_url: str
    duration: Optional[int] = None
    cover_url: Optional[str] = None

class CourseResourceDocumentCreate(BaseSchema):
    """文档资料创建模型"""
    file_url: str = Field(description="文件地址")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    file_type: Optional[str] = Field(None, description="文件类型：pdf/docx/txt")

class CourseResourceDocumentUpdate(BaseSchema):
    """文档资料更新模型"""
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class CourseResourceDocumentResponse(BaseSchema):
    """文档资料响应模型"""
    id: int
    file_url: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class CourseResourceExerciseCreate(BaseSchema):
    """习题资料创建模型"""
    exercise_id: int = Field(description="关联的习题ID")

class CourseResourceExerciseUpdate(BaseSchema):
    """习题资料更新模型"""
    exercise_id: Optional[int] = None

class CourseResourceExerciseResponse(BaseSchema):
    """习题资料响应模型"""
    id: int
    exercise_id: int
    title: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None

# 🔥 终极修复：包含 url + file_type + file_size + duration 所有字段
class CourseResourceCreate(BaseSchema):
    """创建课程资源请求模型"""
    title: str = Field(min_length=1, max_length=255, description="资源标题")
    type: str = Field(description="资源类型：video/document/exercise")
    description: Optional[str] = Field(None, max_length=500, description="资源描述")
    url: Optional[str] = Field(None, description="资源链接（视频/文档用）")
    # 🔥 新增文件核心字段
    file_type: Optional[str] = Field(None, description="文件类型(pdf/mp4/docx)")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    duration: Optional[int] = Field(None, description="视频时长(秒)")
    sort_order: Optional[int] = Field(0, description="排序")
    is_published: Optional[bool] = Field(True, description="是否发布")

    # 类型专属字段
    video: Optional[CourseResourceVideoCreate] = None
    document: Optional[CourseResourceDocumentCreate] = None
    exercise: Optional[CourseResourceExerciseCreate] = None

    # 关联知识点
    knowledge_ids: Optional[List[int]] = Field(default_factory=list, description="关联知识点ID列表")

class CourseResourceUpdate(BaseSchema):
    """更新课程资源请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    sort_order: Optional[int] = None
    is_published: Optional[bool] = None

    # 类型专属字段
    video: Optional[CourseResourceVideoUpdate] = None
    document: Optional[CourseResourceDocumentUpdate] = None
    exercise: Optional[CourseResourceExerciseUpdate] = None

    # 关联知识点
    knowledge_ids: Optional[List[int]] = None

class CourseResourceResponse(BaseSchema):
    """课程资源完整响应模型"""
    id: int
    course_id: int
    title: str
    type: str
    description: Optional[str] = None
    url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    sort_order: int
    is_published: bool
    create_time: datetime
    update_time: datetime

    # 类型专属数据
    video: Optional[CourseResourceVideoResponse] = None
    document: Optional[CourseResourceDocumentResponse] = None
    exercise: Optional[CourseResourceExerciseResponse] = None

    # 关联知识点ID列表
    knowledge_ids: List[int] = Field(default_factory=list)

# ==================== 🔥 学习进度更新Schema ====================
class ResourceProgressUpdate(BaseSchema):
    """更新用户资源学习进度请求模型"""
    # 通用进度字段
    progress: Optional[float] = Field(None, ge=0, le=100, description="整体进度(0-100%)")
    is_finished: Optional[bool] = None
    total_study_duration: Optional[int] = Field(None, ge=0, description="累计学习时长(秒)")

    # 视频专属字段
    watch_position: Optional[int] = Field(None, ge=0, description="当前观看位置(秒)")
    pause_count: Optional[int] = Field(None, ge=0)
    fast_forward_count: Optional[int] = Field(None, ge=0)
    rewind_count: Optional[int] = Field(None, ge=0)

    # 习题专属字段
    exercise_score: Optional[float] = Field(None, ge=0, le=100)
    correct_count: Optional[int] = Field(None, ge=0)
    total_count: Optional[int] = Field(None, ge=0)
    wrong_question_ids: Optional[str] = Field(None, description="错题ID列表(JSON)")
    average_answer_time: Optional[float] = Field(None, ge=0)

    # 文档专属字段
    read_pages: Optional[int] = Field(None, ge=0)
    total_pages: Optional[int] = Field(None, ge=0)
    highlight_count: Optional[int] = Field(None, ge=0)
    note_count: Optional[int] = Field(None, ge=0)

# ==================== 🔥 知识点问答系统Schema ====================
class KnowledgeQaCreate(BaseSchema):
    """创建知识点问答请求模型"""
    knowledge_point_id: int = Field(description="关联知识点ID")
    query: str = Field(min_length=1, description="用户问题")
    answer: str = Field(min_length=1, description="系统回答")
    related_resource_ids: Optional[str] = Field(None, description="关联课程资源ID列表(JSON)")
    difficulty: Optional[str] = Field("中等", description="问题难度：简单/中等/困难")
    is_solved: Optional[bool] = Field(True, description="问题是否解决")
    follow_up_count: Optional[int] = Field(0, ge=0, description="追问次数")

class KnowledgeQaFeedbackUpdate(BaseSchema):
    """更新问答反馈请求模型"""
    feedback_score: Optional[int] = Field(None, ge=1, le=5, description="用户反馈评分(1-5)")
    is_solved: Optional[bool] = None
    follow_up_count: Optional[int] = None

class KnowledgeQaResponse(BaseSchema):
    """知识点问答响应模型"""
    id: int
    user_id: int
    knowledge_point_id: int
    query: str
    answer: str
    related_resource_ids: Optional[str] = None
    difficulty: str
    is_solved: bool
    feedback_score: Optional[int] = None
    follow_up_count: int
    create_time: datetime
    update_time: datetime
# ==================== 知识点 Schema ====================
class KnowledgePointCreate(BaseModel):
    doc_id: int
    user_id: int
    title: str
    content: str
    difficulty: str = "中等"

class KnowledgePointUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    difficulty: str | None = None

class KnowledgePointResp(KnowledgePointCreate):
    id: int
    create_time: datetime
    class Config: from_attributes = True

# ==================== 课程资源文件上传专用Schema ====================
class CourseResourceFileUpload(BaseModel):
    """
    课程资源文件上传专用Schema
    包含文件上传所需的所有字段，与普通JSON创建区分开
    """
    course_id: int
    title: str
    type: str  # video/document/exercise
    knowledge_ids: list[int]
    sort_order: int = 0
    description: Optional[str] = None

    class Config:
        from_attributes = True