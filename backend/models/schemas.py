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