import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from openai import OpenAIError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.client.ai_client import AiClient
from backend.config.ai_client_config import app_config
from backend.models.chat import Chat, ChatMessage

logger = logging.getLogger(__name__)

# Serializer for signed cookies (prevents client-side tampering of session_id)
serializer = URLSafeTimedSerializer(app_config.SECRET_KEY)


class ChatService:
    def __init__(self, *, ai_client: AiClient | None = None):
        self.ai_client = ai_client or AiClient()

    # -------- CHATS --------

    async def create_chat(self, user_id: int, session: AsyncSession) -> Chat:
        chat = Chat(
            user_id=user_id,
            title="New chat",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
        return chat

    async def get_user_chats(self, user_id: int, session: AsyncSession) -> list[Chat]:
        result = await session.execute(
            select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc())
        )
        return result.scalars().all()

    async def delete_chat(self, chat_id: int, user_id: int, session: AsyncSession) -> dict:
        chat = await self._get_chat_or_404(chat_id, user_id, session)

        await session.execute(delete(ChatMessage).where(ChatMessage.chat_id == chat_id))
        await session.delete(chat)
        await session.commit()

        return {"status": "deleted"}

    # -------- MESSAGES --------

    async def get_chat_messages(self, chat_id: int, user_id: int, session: AsyncSession) -> list[ChatMessage]:
        await self._get_chat_or_404(chat_id, user_id, session)

        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return result.scalars().all()

    async def send_message(self, chat_id: int, user_id: int, content: str, session: AsyncSession) -> dict:
        chat = await self._get_chat_or_404(chat_id, user_id, session)

        content = (content or "").strip()
        if not content:
            raise HTTPException(status_code=422, detail="Message content is required")

        # 1) Store user message
        user_message = ChatMessage(chat_id=chat_id, role="user", content=content)
        session.add(user_message)
        await session.flush()  # get ID

        # 2) Load history (exclude just-added message to not waste context slots)
        history = await self._get_last_messages(
            chat_id,
            session,
            limit=app_config.MAX_MESSAGES_IN_CONTEXT,
            exclude_message_id=user_message.id,
        )

        # 3) Build LLM messages
        llm_messages: list[dict] = [{"role": "system", "content": "You are a helpful assistant."}]
        for msg in history:
            llm_messages.append({"role": msg.role, "content": msg.content})
        llm_messages.append({"role": "user", "content": content})

        # 4) Call LLM
        try:
            ai_response = await self.ai_client.chat(llm_messages)
        except OpenAIError as e:
            logger.error("Failed to get AI response for chat %s: %s", chat_id, e)
            raise HTTPException(status_code=503, detail="AI service unavailable")
        except Exception as e:
            logger.error("Unexpected error in AI call: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

        # 5) Store assistant message + bump chat timestamp
        ai_message = ChatMessage(chat_id=chat_id, role="assistant", content=ai_response)
        session.add(ai_message)

        chat.updated_at = datetime.now(timezone.utc)
        await session.commit()

        return {"user_message": content, "ai_response": ai_response}

    # -------- INTERNAL --------

    async def _get_chat_or_404(self, chat_id: int, user_id: int, session: AsyncSession) -> Chat:
        result = await session.execute(
            select(Chat).where(Chat.id == chat_id).where(Chat.user_id == user_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat

    async def _get_last_messages(
        self,
        chat_id: int,
        session: AsyncSession,
        limit: int = 10,
        exclude_message_id: int | None = None,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
        if exclude_message_id is not None:
            stmt = stmt.where(ChatMessage.id != exclude_message_id)

        result = await session.execute(stmt)
        messages = list(result.scalars().all())
        return list(reversed(messages))
