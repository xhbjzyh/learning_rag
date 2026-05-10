from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from service.admin.admin_knowledge_service import admin_knowledge_service
from models.schemas import KnowledgePointCreate, KnowledgePointUpdate

# 🔥 修复：删除重复前缀
router = APIRouter(tags=["管理员-知识点管理"])

@router.get("/list")
def list_knowledge(page: int=1, size: int=10, db: Session=Depends(get_db)):
    return admin_knowledge_service.get_knowledge_list(db, page, size)

@router.post("/create")
def create_knowledge(data: KnowledgePointCreate, db: Session=Depends(get_db)):
    return admin_knowledge_service.create_knowledge(db, data)

@router.put("/update/{kid}")
def update_knowledge(kid: int, data: KnowledgePointUpdate, db: Session=Depends(get_db)):
    return admin_knowledge_service.update_knowledge(db, kid, data)

@router.delete("/delete/{kid}")
def delete_knowledge(kid: int, db: Session=Depends(get_db)):
    return admin_knowledge_service.delete_knowledge(db, kid)