# backend/app/router_rag.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from .deps import db_dep
from .schemas import RAGDocIn
from .models.rag import RAGDocument
from .services.rag import index_document

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/docs")
async def add_doc(payload: RAGDocIn, session: AsyncSession = Depends(db_dep)):
    # insert the raw doc
    result = await session.execute(
        insert(RAGDocument)
        .values(title=payload.title, content=payload.content, tags=payload.tags)
        .returning(RAGDocument.id)
    )
    doc_id = result.scalar_one()
    await session.commit()

    # build chunks + embeddings
    await index_document(session, doc_id, payload.title, payload.content, payload.tags)
    return {"ok": True, "doc_id": doc_id}


@router.get("/docs")
async def list_docs(session: AsyncSession = Depends(db_dep)):
    res = await session.execute(select(RAGDocument))
    return [{"id": d.id, "title": d.title, "tags": d.tags} for d in res.scalars().all()]
