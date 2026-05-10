"""
用户-私有内容管理业务逻辑（线上大模型提取知识点版）
功能：文件切分 → 线上glm-4-flash提取知识点 → 存数据库 → 同步向量库
规则：无降级，大模型调用失败直接报错，支持手动重试
"""
import os
import uuid
import json
import re
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from utils.document_parser import document_parser, calculate_md5
from models.db_models import (
    KnowledgeDocument, KnowledgePoint, LearningProgress, WrongQuestion,
    ContentPublicApply, UserKnowledgeMastery
)
from models.schemas import (
    DocumentUploadResponse,
    DocumentInfoResponse,
    DocumentUpdateRequest,
    KnowledgePointResponse
)
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger
from config import settings

from langchain_text_splitters import RecursiveCharacterTextSplitter
# 🔥 核心修改：引入线上大模型
from core.llm import llm


class ContentPrivateService:
    """私有内容管理服务类"""

    def __init__(self):
        # 优化切分大小，适配线上大模型上下文
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
            length_function=len
        )
        logger.info("✅ 私有内容服务初始化完成（使用线上大模型glm-4-flash）")

    @staticmethod
    async def upload_document(
            db: Session,
            file: UploadFile,
            title: str,
            category_id: Optional[int],
            user_id: int
    ) -> DocumentUploadResponse:
        allowed_types = ["txt", "pdf", "docx"]
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in allowed_types:
            raise BusinessException(
                code=BusinessErrorCode.FILE_TYPE_NOT_SUPPORT,
                msg=f"不支持的文件类型，仅支持: {', '.join(allowed_types)}"
            )

        file_content = await file.read()
        file_md5 = calculate_md5(file_content)

        exist_doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.file_md5 == file_md5,
            KnowledgeDocument.upload_user_id == user_id
        ).first()

        if exist_doc:
            logger.info(f"文件已存在，直接返回已有记录，文档ID: {exist_doc.id}")
            return DocumentUploadResponse.model_validate(exist_doc)

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        file_uuid = str(uuid.uuid4())
        save_filename = f"{file_uuid}.{file_ext}"
        save_path = os.path.join(upload_dir, save_filename)

        with open(save_path, "wb") as f:
            f.write(file_content)

        file_size = len(file_content)

        new_doc = KnowledgeDocument(
            title=title,
            file_name=file.filename,
            file_path=save_path,
            file_md5=file_md5,
            file_type=file_ext,
            file_size=file_size,
            category_id=category_id,
            upload_user_id=user_id,
            audit_status=0,
            process_status=0
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        logger.info(f"文档上传成功: {file.filename}, 文档ID: {new_doc.id}")
        return DocumentUploadResponse.model_validate(new_doc)

    @staticmethod
    def get_private_document_list(db: Session, user_id: int):
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.upload_user_id == user_id
        ).order_by(KnowledgeDocument.create_time.desc()).all()
        return [DocumentInfoResponse.model_validate(item) for item in documents]

    @staticmethod
    def update_document(db: Session, doc_id: int, request: DocumentUpdateRequest, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        if request.title:
            doc.title = request.title
        if request.category_id is not None:
            doc.category_id = request.category_id

        db.commit()
        db.refresh(doc)
        logger.info(f"文档修改成功，文档ID: {doc_id}")
        return DocumentInfoResponse.model_validate(doc)

    @staticmethod
    def delete_document(db: Session, doc_id: int, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")
        db.query(LearningProgress).filter(
            LearningProgress.point_id.in_(
                db.query(KnowledgePoint.id).filter(KnowledgePoint.doc_id == doc_id)
            )
        ).delete(synchronize_session=False)

        db.query(WrongQuestion).filter(
            WrongQuestion.point_id.in_(
                db.query(KnowledgePoint.id).filter(KnowledgePoint.doc_id == doc_id)
            )
        ).delete(synchronize_session=False)

        db.query(UserKnowledgeMastery).filter(
            UserKnowledgeMastery.knowledge_point_id.in_(
                db.query(KnowledgePoint.id).filter(KnowledgePoint.doc_id == doc_id)
            )
        ).delete(synchronize_session=False)

        db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).delete()

        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"删除本地文件失败: {str(e)}")

        db.delete(doc)
        db.commit()
        logger.info(f"文档删除成功，文档ID: {doc_id}")

    async def parse_and_extract_points(self, db: Session, doc_id: int, user_id: int):
        """
        解析文档并提取知识点（线上大模型版，无降级）
        流程：1. 解析文档 → 2. 切分 → 3. 大模型提取 → 4. 存DB → 5. 同步向量
        """
        # 1. 查询文档
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在"
            )

        # 2. 更新状态为处理中
        doc.process_status = 1
        doc.process_message = "正在解析文档并提取知识点..."
        db.commit()

        # 3. 🔥 关键：删除已有知识点（支持重新解析）
        db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).delete()
        db.commit()
        logger.info(f"已清空文档 {doc_id} 的旧知识点，准备重新提取")

        try:
            # 4. 解析文档全文
            text_content = document_parser.parse_document(doc.file_path, doc.file_type)
            logger.info(f"文档解析成功，全文长度: {len(text_content)}")
        except Exception as e:
            logger.error(f"文档解析失败: {doc_id}, 错误: {str(e)}")
            doc.process_status = 3
            doc.process_message = f"文档解析失败: {str(e)}"
            db.commit()
            raise BusinessException(
                code=BusinessErrorCode.DOC_PARSE_ERROR,
                msg="文档解析失败"
            )

        try:
            # 5. 切分文档
            chunks = self.text_splitter.split_text(text_content)
            logger.info(f"文档切分为 {len(chunks)} 个块，开始调用大模型提取知识点")

            points_created = 0

            # 6. 逐块调用线上大模型提取知识点
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                logger.info(f"正在处理第 {i+1}/{len(chunks)} 个块...")

                # 构建大模型提示词
                prompt = f"""你是专业的文档结构化提取专家。
任务：从以下文本中提取知识点，只输出合法JSON数组，不要输出任何其他文字。

要求：
1. title：简洁明了的知识点标题（20字以内）
2. content：完整的知识点内容（保留原文核心信息）
3. key_points：核心要点数组（3-5个）
4. difficulty：难度（简单/中等/困难）

文本内容：
{chunk}

输出格式示例：
[{{"title":"xxx","content":"xxx","key_points":["xxx","xxx"],"difficulty":"中等"}}]
"""

                # 🔥 核心：调用线上大模型（异步 + 超时30秒）
                try:
                    response = await llm.chat(prompt, timeout=30)
                except Exception as e:
                    logger.error(f"大模型调用失败（第 {i+1} 块）: {str(e)}")
                    doc.process_status = 3
                    doc.process_message = f"大模型调用失败: {str(e)}"
                    db.commit()
                    raise BusinessException(
                        code=BusinessErrorCode.DOC_PARSE_ERROR,
                        msg=f"大模型提取知识点失败: {str(e)}"
                    )

                # 解析大模型返回的JSON
                knowledge_points = self._safe_parse_json(response)
                if not knowledge_points:
                    logger.error(f"大模型返回JSON解析失败（第 {i+1} 块）: {response[:200]}")
                    doc.process_status = 3
                    doc.process_message = "大模型返回格式错误"
                    db.commit()
                    raise BusinessException(
                        code=BusinessErrorCode.DOC_PARSE_ERROR,
                        msg="大模型返回格式错误，解析失败"
                    )

                # 存入数据库
                for kp in knowledge_points:
                    new_point = KnowledgePoint(
                        doc_id=doc_id,
                        user_id=user_id,
                        title=kp["title"][:255],  # 防止标题过长
                        content=kp["content"],
                        key_points=json.dumps(kp.get("key_points", []), ensure_ascii=False),
                        difficulty=kp.get("difficulty", "中等"),
                        pre_knowledge=json.dumps(kp.get("pre_knowledge", []), ensure_ascii=False),
                        common_mistakes=json.dumps(kp.get("common_mistakes", []), ensure_ascii=False),
                        related_topics=json.dumps(kp.get("related_topics", []), ensure_ascii=False),
                        chunk_index=i
                    )
                    db.add(new_point)
                    points_created += 1

            # 7. 批量提交数据库
            db.commit()
            logger.info(f"✅ 知识点提取完成，共存入 {points_created} 个知识点")

            # 8. 更新文档状态
            doc.process_status = 2
            doc.process_message = f"处理完成，共提取 {points_created} 个知识点"
            db.commit()

            # 9. 同步到向量库
            try:
                from utils.vector_store import VectorStoreManager
                vector_store = VectorStoreManager(user_id)
                points = db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).all()
                vector_store.add_knowledge_points([
                    {
                        "id": p.id,
                        "title": p.title,
                        "content": p.content,
                        "difficulty": p.difficulty
                    }
                    for p in points
                ])
                logger.info(f"✅ 知识点同步到向量库成功")
            except Exception as e:
                logger.warning(f"存入向量库失败: {e}，但知识点已存入数据库")

            return {"doc_id": doc_id, "points_count": points_created, "is_new": True}

        except BusinessException:
            # 业务异常直接抛出
            raise
        except Exception as e:
            logger.error(f"知识点提取流程异常: {doc_id}, 错误: {str(e)}")
            doc.process_status = 3
            doc.process_message = f"处理异常: {str(e)}"
            db.commit()
            raise BusinessException(
                code=BusinessErrorCode.DOC_PARSE_ERROR,
                msg=f"处理异常: {str(e)}"
            )

    @staticmethod
    def get_private_knowledge_points(db: Session, doc_id: int, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        points = db.query(KnowledgePoint).filter(
            KnowledgePoint.doc_id == doc_id
        ).order_by(KnowledgePoint.create_time.asc()).all()
        return [KnowledgePointResponse.model_validate(item) for item in points]

    @staticmethod
    def apply_public(db: Session, doc_id: int, apply_remark: str, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(code=BusinessErrorCode.DOC_NOT_EXIST, msg="文档不存在")

        if doc.is_public == 1:
            raise BusinessException(code=BusinessErrorCode.PARAM_ERROR, msg="文档已经是公开状态")

        exist_apply = db.query(ContentPublicApply).filter(
            ContentPublicApply.doc_id == doc_id,
            ContentPublicApply.apply_status == 0
        ).first()
        if exist_apply:
            raise BusinessException(code=BusinessErrorCode.PARAM_ERROR, msg="已有待审核的公开申请")

        new_apply = ContentPublicApply(
            doc_id=doc_id,
            apply_user_id=user_id,
            apply_remark=apply_remark,
            apply_status=0
        )
        db.add(new_apply)
        db.commit()
        db.refresh(new_apply)

        logger.info(f"文档公开申请提交成功，文档ID: {doc_id}")
        return {"apply_id": new_apply.id, "doc_id": doc_id, "status": "待审核"}

    def _safe_parse_json(self, text: str):
        """安全解析大模型返回的JSON"""
        try:
            text = text.strip()
            result = json.loads(text)
            if isinstance(result, dict):
                return [result]
            if isinstance(result, list):
                return result
        except:
            pass

        try:
            json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                if isinstance(result, dict):
                    return [result]
                return result
        except:
            pass

        try:
            t = text.replace("'", '"')
            t = re.sub(r',\s*}', '}', t)
            t = re.sub(r',\s*]', ']', t)
            result = json.loads(t)
            if isinstance(result, dict):
                return [result]
            return result
        except:
            pass

        logger.warning(f"JSON解析失败，输出片段: {text[:200]}")
        return []


content_private_service = ContentPrivateService()