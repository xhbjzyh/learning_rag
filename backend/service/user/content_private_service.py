"""
用户-私有内容管理业务逻辑
"""
import os
import uuid
import json
import re
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from concurrent.futures import ThreadPoolExecutor

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
from langchain_community.llms import Ollama
from config.rag_config import RAG_CONFIG


class ContentPrivateService:
    """私有内容管理服务类"""

    def __init__(self):
        # 🔥 关键修复：分块改小，7B模型绝对不卡死
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
            length_function=len
        )

        # 🔥 关键修复：删除 format="json"，这是卡死元凶
        try:
            self.llm = Ollama(
                model=RAG_CONFIG["llm_model"],
                temperature=0.0,
                num_ctx=8192,
            )
            logger.info("✅ 本地大模型初始化成功（安全模式）")
        except Exception as e:
            logger.warning(f"⚠️ 本地大模型初始化失败: {e}，将使用基础切分")
            self.llm = None

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

    def parse_and_extract_points(self, db: Session, doc_id: int, user_id: int):
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.upload_user_id == user_id
        ).first()
        if not doc:
            raise BusinessException(
                code=BusinessErrorCode.DOC_NOT_EXIST,
                msg="文档不存在"
            )

        doc.process_status = 1
        doc.process_message = "正在提取知识点..."
        db.commit()

        exist_points = db.query(KnowledgePoint).filter(
            KnowledgePoint.doc_id == doc_id
        ).first()

        if exist_points:
            points_count = db.query(KnowledgePoint).filter(
                KnowledgePoint.doc_id == doc_id
            ).count()
            logger.info(f"文档已解析过，直接返回已有数据，知识点数量: {points_count}")
            doc.process_status = 2
            doc.process_message = f"处理完成，共 {points_count} 个知识点"
            db.commit()
            return {"doc_id": doc_id, "points_count": points_count, "is_new": False}

        try:
            text_content = document_parser.parse_document(doc.file_path, doc.file_type)
        except Exception as e:
            logger.error(f"文档解析失败: {doc_id}, 错误: {str(e)}")
            doc.process_status = 3
            doc.process_message = "文档解析失败"
            db.commit()
            raise BusinessException(
                code=BusinessErrorCode.DOC_PARSE_ERROR,
                msg="文档解析失败"
            )

        try:
            chunks = self.text_splitter.split_text(text_content)
            logger.info(f"文档粗切分为 {len(chunks)} 个块")

            points_created = 0

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                if self.llm:
                    try:
                        subject = self._get_subject_by_category(doc.category_id)

                        prompt = f"""你是专业的文档结构化提取专家。
任务：从文本中提取知识点，只输出合法JSON，不要输出任何多余内容。

输出格式：
[{{"title":"简洁标题","content":"完整内容","key_points":[],"difficulty":"中等"}}]

文本内容：
{chunk}
"""

                        # 🔥 关键修复：模型调用增加30秒超时，绝不卡死
                        executor = ThreadPoolExecutor(max_workers=1)
                        future = executor.submit(self.llm.invoke, prompt)
                        try:
                            response = future.result(timeout=30)
                        except:
                            executor.shutdown(wait=False)
                            raise Exception("模型调用超时")

                        knowledge_points = self._safe_parse_json(response)

                        if not knowledge_points:
                            raise Exception("JSON解析失败或返回空")

                        for kp in knowledge_points:
                            new_point = KnowledgePoint(
                                doc_id=doc_id,
                                user_id=user_id,
                                title=kp["title"],
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

                    except Exception as e:
                        logger.warning(f"大模型提取失败，使用基础切分")
                        point_title = f"{doc.title} - 第{i + 1}部分"
                        new_point = KnowledgePoint(
                            doc_id=doc_id,
                            user_id=user_id,
                            title=point_title,
                            content=chunk,
                            difficulty="中等"
                        )
                        db.add(new_point)
                        points_created += 1
                else:
                    point_title = f"{doc.title} - 第{i + 1}部分"
                    new_point = KnowledgePoint(
                        doc_id=doc_id,
                        user_id=user_id,
                        title=point_title,
                        content=chunk,
                        difficulty="中等"
                    )
                    db.add(new_point)
                    points_created += 1

            db.commit()

            doc.process_status = 2
            doc.process_message = f"处理完成，共提取 {points_created} 个知识点"
            db.commit()

            logger.info(f"✅ 知识点提取完成，文档ID: {doc_id}, 共提取 {points_created} 个知识点")

            try:
                from utils.vector_store import VectorStoreManager
                vector_store = VectorStoreManager(user_id)
                points = db.query(KnowledgePoint).filter(KnowledgePoint.doc_id == doc_id).all()
                vector_store.add_knowledge_points([
                    {
                        "id": p.id,
                        "document_id": p.doc_id,
                        "title": p.title,
                        "content": p.content,
                        "difficulty": p.difficulty
                    }
                    for p in points
                ])
                logger.info(f"✅ 知识点存入向量库成功")
            except Exception as e:
                logger.warning(f"存入向量库失败: {e}")

            return {"doc_id": doc_id, "points_count": points_created, "is_new": True}

        except Exception as e:
            logger.error(f"知识点提取失败: {doc_id}, 错误: {str(e)}")
            doc.process_status = 3
            doc.process_message = f"知识点提取失败: {str(e)}"
            db.commit()
            raise BusinessException(
                code=BusinessErrorCode.DOC_PARSE_ERROR,
                msg="知识点提取失败"
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

    def _get_subject_by_category(self, category_id: int):
        subject_map = {
            1: "计算机科学",
            2: "英语",
            3: "数学"
        }
        return subject_map.get(category_id, "通用")

    def _safe_parse_json(self, text: str):
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