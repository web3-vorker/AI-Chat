from typing import Annotated

import os

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///chat_history.db")
engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
  # Ensure SQLite enforces foreign keys (needed for ON DELETE CASCADE)
  try:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
  except Exception:
    pass

async def get_session():
  async with new_session() as session:
    yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


