import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from ..db import Base


class AppUser(Base):
    __tablename__ = "app_user"
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
