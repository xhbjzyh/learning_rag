import os
import uuid
from fastapi import UploadFile
from datetime import datetime

# 基础存储路径
BASE_UPLOAD_DIR = "static/resources"
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

def save_upload_file(file: UploadFile, resource_type: str) -> str:
    """保存上传文件，返回文件URL"""
    # 按类型分文件夹
    save_dir = os.path.join(BASE_UPLOAD_DIR, resource_type)
    os.makedirs(save_dir, exist_ok=True)
    # 生成唯一文件名
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(save_dir, filename)
    # 写入文件
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    # 返回相对路径（用于下载）
    return f"/static/resources/{resource_type}/{filename}"

def get_file_path(file_url: str) -> str:
    """根据URL获取本地文件路径"""
    return file_url.lstrip("/")