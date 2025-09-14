from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY  # ← add this
from pgvector.sqlalchemy import Vector
from ..db import Base


class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(
        ForeignKey("rag_documents.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )  # ← fixed
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
