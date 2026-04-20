import pytest
from sqlalchemy.orm import Session
from db.sqlite_conn import get_db
from models.db_models import SysUser
from utils.password_utils import hash_password, verify_password
from utils.jwt_utils import create_access_token, verify_token

def test_password_hash_and_verify():
    """测试密码加密与校验"""
    original_password = "test123456"
    # 加密
    hashed = hash_password(original_password)
    # 校验正确密码
    assert verify_password(original_password, hashed) is True
    # 校验错误密码
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_token_create_and_verify():
    """测试JWT令牌生成与校验"""
    user_id = 1
    # 生成令牌
    token = create_access_token(user_id=user_id)
    # 校验令牌
    verified_user_id = verify_token(token)
    assert verified_user_id == user_id
    # 校验无效令牌
    assert verify_token("invalid_token") is None

def test_init_db():
    """测试数据库初始化是否成功"""
    db: Session = next(get_db())
    # 检查是否有默认管理员
    admin = db.query(SysUser).filter(SysUser.username == "admin").first()
    assert admin is not None
    assert admin.role_id == 1  # 超级管理员角色
    db.close()