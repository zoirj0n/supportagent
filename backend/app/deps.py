from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db


async def db_dep(session: AsyncSession = Depends(get_db)):
	return session
