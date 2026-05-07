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