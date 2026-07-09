from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import KnowledgeDocument
from app.rag.indexer import reindex_documents
from app.rag.retriever import answer_question
from app.schemas import RagAskRequest, RagAskResponse
from app.serializers import document_to_dict

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/ask", response_model=RagAskResponse)
def ask_rag(payload: RagAskRequest, db: Session = Depends(get_db)) -> dict:
    return answer_question(db, payload.question)


@router.post("/reindex")
def reindex(db: Session = Depends(get_db)) -> dict:
    docs = reindex_documents(db)
    return {"indexed": len(docs), "documents": [document_to_dict(doc) for doc in docs]}


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)) -> list[dict]:
    docs = db.query(KnowledgeDocument).order_by(KnowledgeDocument.title.asc()).all()
    return [document_to_dict(doc) for doc in docs]
