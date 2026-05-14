"""
通用文件上传接口
支持图片、视频、文档等文件上传
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import os
import uuid
from datetime import datetime

from db.sqlite_conn import get_db
from sqlalchemy.orm import Session
from utils.logger import logger
from utils.response import success_response

# 🔥 修复：移除 prefix，因为在 __init__.py 中已经通过 include_router 统一挂载
router = APIRouter(tags=["通用文件上传"])

# 允许的图片类型
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "webp"]
# 允许的视频类型
ALLOWED_VIDEO_TYPES = ["mp4", "avi", "mov", "mkv", "flv", "wmv"]
# 允许的文档类型
ALLOWED_DOCUMENT_TYPES = ["pdf", "docx", "doc", "txt", "md"]

# 上传目录配置
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/image", summary="上传图片文件")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片文件（课程封面、头像等）
    """
    try:
        # 验证文件类型
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片格式，仅支持: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        # 验证文件大小（限制10MB）
        file_size = 0
        content = await file.read()
        file_size = len(content)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片大小不能超过10MB")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        upload_path = os.path.join(UPLOAD_DIR, "images")
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        # 返回文件URL（相对路径）
        file_url = f"/static/uploads/images/{filename}"

        logger.info(f"图片上传成功: {file.filename}, 大小: {file_size} bytes")

        return success_response(
            data={
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file_size,
                "file_type": file_ext
            },
            msg="图片上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail="图片上传失败")


@router.post("/video", summary="上传视频文件")
async def upload_video(file: UploadFile = File(...)):
    """
    上传视频文件
    """
    try:
        # 验证文件类型
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的视频格式，仅支持: {', '.join(ALLOWED_VIDEO_TYPES)}"
            )

        # 验证文件大小（限制500MB）
        content = await file.read()
        file_size = len(content)
        if file_size > 500 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="视频大小不能超过500MB")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        upload_path = os.path.join(UPLOAD_DIR, "videos")
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        file_url = f"/static/uploads/videos/{filename}"

        logger.info(f"视频上传成功: {file.filename}, 大小: {file_size} bytes")

        return success_response(
            data={
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file_size,
                "file_type": file_ext
            },
            msg="视频上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"视频上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail="视频上传失败")


@router.post("/document", summary="上传文档文件")
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档文件
    """
    try:
        # 验证文件类型
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文档格式，仅支持: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
            )

        # 验证文件大小（限制50MB）
        content = await file.read()
        file_size = len(content)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文档大小不能超过50MB")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        upload_path = os.path.join(UPLOAD_DIR, "documents")
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        file_url = f"/static/uploads/documents/{filename}"

        logger.info(f"文档上传成功: {file.filename}, 大小: {file_size} bytes")

        return success_response(
            data={
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file_size,
                "file_type": file_ext
            },
            msg="文档上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail="文档上传失败")


@router.post("/", summary="通用文件上传（自动识别类型）")
async def upload_file(file: UploadFile = File(...)):
    """
    通用文件上传接口，自动识别文件类型并保存到对应目录
    """
    try:
        # 验证文件类型
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""

        # 确定文件类型和保存目录
        if file_ext in ALLOWED_IMAGE_TYPES:
            category = "images"
            max_size = 10 * 1024 * 1024  # 10MB
        elif file_ext in ALLOWED_VIDEO_TYPES:
            category = "videos"
            max_size = 500 * 1024 * 1024  # 500MB
        elif file_ext in ALLOWED_DOCUMENT_TYPES:
            category = "documents"
            max_size = 50 * 1024 * 1024  # 50MB
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_IMAGE_TYPES + ALLOWED_VIDEO_TYPES + ALLOWED_DOCUMENT_TYPES)}"
            )

        # 验证文件大小
        content = await file.read()
        file_size = len(content)
        if file_size > max_size:
            raise HTTPException(status_code=400, detail=f"文件大小超过限制")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        upload_path = os.path.join(UPLOAD_DIR, category)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        file_url = f"/static/uploads/{category}/{filename}"

        logger.info(f"文件上传成功: {file.filename}, 类型: {category}, 大小: {file_size} bytes")

        return success_response(
            data={
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": file_size,
                "file_type": file_ext,
                "category": category
            },
            msg="文件上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail="文件上传失败")


# 🔥 新增：兼容前端的 /upload 路径
@router.post("/upload", summary="通用文件上传（兼容旧接口）")
async def upload_file_compat(file: UploadFile = File(...)):
    """
    兼容前端的 /common/upload 接口
    """
    return await upload_file(file)
