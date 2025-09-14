# backend/app/services/rag.py
from __future__ import annotations
from typing import List, Tuple
import re
from collections import Counter
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from sqlalchemy import text as sqltext

from ..models.rag import RAGDocument
from ..models.rag_chunk import RAGChunk
from .llm import embed_texts, answer_with_llm

log = logging.getLogger("rag")


# =========================
# Chunking (fixed)
# =========================
def _chunk(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    """
    Simple character chunker with overlap; avoids infinite loops.
    """
    s = (text or "").strip()
    if not s:
        return []
    step = max(1, max_chars - max(0, overlap))
    out: List[str] = []
    i, n = 0, len(s)
    while i < n:
        j = min(i + max_chars, n)
        out.append(s[i:j])
        if j >= n:
            break
        i += step
    return out


# =========================
# Keyword fallback
# =========================
_WORD_RE = re.compile(r"[a-z0-9]+", re.I)
_STOP = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "in",
    "on",
    "at",
    "to",
    "for",
    "with",
    "of",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "this",
    "that",
    "as",
    "from",
    "about",
    "into",
    "over",
    "after",
    "before",
    "than",
    "then",
    "so",
    "such",
    "not",
    "no",
    "do",
    "does",
    "did",
    "doing",
    "can",
    "could",
    "should",
    "would",
    "you",
    "your",
    "yours",
    "we",
    "our",
    "ours",
    "they",
    "their",
    "them",
    "i",
    "me",
    "my",
}


def _tokens(s: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(s or "") if t.lower() not in _STOP]


def _overlap_score(q: List[str], d: List[str]) -> float:
    if not q or not d:
        return 0.0
    qC, dC = Counter(q), Counter(d)
    inter = sum(min(qC[t], dC[t]) for t in set(qC) & set(dC))
    denom = (sum(qC.values()) ** 0.5) * (sum(dC.values()) ** 0.5)
    return inter / denom if denom else 0.0


async def _retrieve_context_keyword(
    session: AsyncSession, question: str, k: int = 3
) -> List[Tuple[str, float]]:
    q = _tokens(question)
    res = await session.execute(select(RAGDocument))
    docs = res.scalars().all()
    scored: List[Tuple[float, str]] = []
    for d in docs:
        toks = _tokens(f"{d.title or ''} {d.content or ''}")
        s = _overlap_score(q, toks)
        if s > 0:
            scored.append((s, d.content))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(c, float(s)) for s, c in scored[:k]]


# pgvector helpers
def _vec_literal(vec: List[float]) -> str:
    """Render python list -> pgvector literal: '[0.1,0.2,...]'"""
    return "[" + ",".join(f"{x:.7f}" for x in vec) + "]"


# Indexing
async def index_document(
    session: AsyncSession,
    doc_id: int,
    title: str | None,
    content: str,
    tags: List[str] | None,
):
    chunks = _chunk(content)
    if not chunks:
        return

    try:
        embs = embed_texts(chunks)
        # Insert using SQL text so we can cast string -> vector
        for idx, (ch, emb) in enumerate(zip(chunks, embs)):
            await session.execute(
                sqltext(
                    """
                    INSERT INTO rag_chunks (doc_id, content, embedding, tags, chunk_index)
                    VALUES (:doc_id, :content, :embedding::vector, :tags, :idx)
                """
                ),
                {
                    "doc_id": doc_id,
                    "content": ch,
                    "embedding": _vec_literal(emb),
                    "tags": tags or None,
                    "idx": idx,
                },
            )
    except Exception as e:
        # Keep pipeline alive even if embeddings fail
        log.warning("[index_document] Embedding failed, storing without vectors: %s", e)
        rows = [
            {
                "doc_id": doc_id,
                "content": ch,
                "embedding": None,
                "tags": tags,
                "chunk_index": idx,
            }
            for idx, ch in enumerate(chunks)
        ]
        await session.execute(insert(RAGChunk), rows)

    await session.commit()


# Retrieval
async def retrieve_context(
    session: AsyncSession, question: str, k: int = 3
) -> List[Tuple[str, float]]:
    try:
        q_emb = embed_texts([question])[0]
        qvec = _vec_literal(q_emb)
        rows = (
            await session.execute(
                sqltext(
                    """
                    SELECT content, 1.0 - (embedding <=> :qvec::vector) AS score
                    FROM rag_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> :qvec::vector
                    LIMIT :k
                """
                ),
                {"qvec": qvec, "k": k},
            )
        ).all()
        if rows:
            return [(r[0], float(r[1])) for r in rows]
        log.info("[retrieve_context] No embedded chunks; using keyword fallback.")
        return await _retrieve_context_keyword(session, question, k)
    except Exception as e:
        log.warning(
            "[retrieve_context] Vector search failed, fallback to keyword: %s", e
        )
        return await _retrieve_context_keyword(session, question, k)


# Answering / Orchestration
async def generate_answer(
    question: str, contexts: List[Tuple[str, float]]
) -> tuple[str | None, float]:
    if not contexts:
        return None, 0.0
    contents = [c for c, _ in contexts]
    answer = answer_with_llm(question, contents)
    conf = max(s for _, s in contexts)
    return answer, conf


async def answer_or_escalate(session: AsyncSession, account, email_ctx) -> bool:
    from .responder import reply_text, reply_escalated

    question = (email_ctx.get("body") or "").strip()
    top = await retrieve_context(session, question, k=3)
    answer, score = await generate_answer(question, top)
    if answer and score >= 0.35:
        await reply_text(
            account,
            email_ctx["thread_id"],
            email_ctx["from_email"],
            email_ctx["subject"],
            answer,
        )
        return True
    await reply_escalated(account, email_ctx)
    return False
