from fastapi import APIRouter, Depends, Path, Request, Response
from db.database import SessionDep
from services.service import ChatService
from schemas.chat import ChatOut
from schemas.chat_message import ChatMessageOut
from schemas.message import MessageSchema
from schemas.send_message import SendMessageOut


main_router = APIRouter()

def get_chat_service(request: Request) -> ChatService:
    ai_client = getattr(request.app.state, "ai_client", None)
    return ChatService(ai_client=ai_client)


@main_router.get("/chats", response_model=list[ChatOut])
async def get_chats(
    request: Request,
    response: Response,
    session: SessionDep,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatOut]:
    user_id = service.get_or_create_session_id(request, response)
    return await service.get_user_chats(user_id, session)


@main_router.get("/chats/{chat_id}/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(
    request: Request,
    response: Response,
    session: SessionDep,
    chat_id: int = Path(..., gt=0),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageOut]:
    user_id = service.get_or_create_session_id(request, response)
    return await service.get_chat_messages(chat_id, user_id, session)


@main_router.post("/chats/{chat_id}/messages", response_model=SendMessageOut)
async def send_message(
    request: Request,
    response: Response,
    session: SessionDep,
    body: MessageSchema,
    chat_id: int = Path(..., gt=0),
    service: ChatService = Depends(get_chat_service),
) -> SendMessageOut:
    user_id = service.get_or_create_session_id(request, response)
    return await service.send_message(chat_id, user_id, body.content, session)


@main_router.post("/chats", response_model=ChatOut)
async def create_chat(
    request: Request,
    response: Response,
    session: SessionDep,
    service: ChatService = Depends(get_chat_service),
) -> ChatOut:
    user_id = service.get_or_create_session_id(request, response)
    return await service.create_chat(user_id, session)


@main_router.delete("/chats/{chat_id}")
async def delete_chat(
    request: Request,
    response: Response,
    session: SessionDep,
    chat_id: int = Path(..., gt=0),
    service: ChatService = Depends(get_chat_service),
) -> dict:
    user_id = service.get_or_create_session_id(request, response)
    return await service.delete_chat(chat_id, user_id, session)
