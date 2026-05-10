from sqlalchemy.orm import Session
from models.db_models import KnowledgePoint, KnowledgeDocument
from models.schemas import KnowledgePointCreate, KnowledgePointUpdate
from fastapi import HTTPException

class AdminKnowledgeService:
    # 查询知识点列表
    def get_knowledge_list(self, db: Session, page: int=1, size: int=10, title: str=None):
        query = db.query(KnowledgePoint)
        if title:
            query = query.filter(KnowledgePoint.title.like(f"%{title}%"))
        total = query.count()
        items = query.offset((page-1)*size).limit(size).all()
        return {"total": total, "items": items, "page": page, "size": size}

    # 创建知识点
    def create_knowledge(self, db: Session, data: KnowledgePointCreate):
        # 校验文档存在
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id==data.doc_id).first()
        if not doc:
            raise HTTPException(404, "知识库文档不存在")
        knowledge = KnowledgePoint(**data.model_dump())
        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)
        return knowledge

    # 更新知识点
    def update_knowledge(self, db: Session, kid: int, data: KnowledgePointUpdate):
        know = db.query(KnowledgePoint).filter(KnowledgePoint.id==kid).first()
        if not know:
            raise HTTPException(404, "知识点不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(know, k, v)
        db.commit()
        db.refresh(know)
        return know

    # 删除知识点
    def delete_knowledge(self, db: Session, kid: int):
        know = db.query(KnowledgePoint).filter(KnowledgePoint.id==kid).first()
        if not know:
            raise HTTPException(404, "知识点不存在")
        db.delete(know)
        db.commit()
        return True

admin_knowledge_service = AdminKnowledgeService()