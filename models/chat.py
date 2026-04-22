from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  pass
class Chat(Base):
    __tablename__ = "chats"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(default="New chat")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Добавить связь:
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        cascade="all, delete-orphan",
        back_populates="chat",
        lazy="noload",
    )

    def __init__(self, **kwargs):
        if kwargs.get("title") is None:
            kwargs["title"] = "New chat"
        super().__init__(**kwargs)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Добавить:
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages", lazy="noload")
