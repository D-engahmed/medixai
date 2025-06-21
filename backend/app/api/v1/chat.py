"""
Chat API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID
import json

from app.core.dependencies import get_db, get_current_patient, get_current_doctor
from app.services.chat_service import ChatService
from app.models.chat import ChatType, ChatStatus
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse,
    ChatEscalationResponse
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

# WebSocket connections store
active_connections: Dict[UUID, WebSocket] = {}

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db)
) -> ChatSessionResponse:
    """Create a new chat session"""
    try:
        chat_service = ChatService(db)
        session = await chat_service.create_chat_session(
            patient_id=current_user.patient.id,
            chat_type=session_data.chat_type,
            initial_context=session_data.initial_context
        )
        return ChatSessionResponse.from_orm(session)
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db)
) -> ChatSessionResponse:
    """Get chat session details"""
    try:
        chat_service = ChatService(db)
        session = await chat_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Verify ownership
        if session.patient_id != current_user.patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return ChatSessionResponse.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat session"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db)
) -> List[ChatMessageResponse]:
    """Get messages from a chat session"""
    try:
        chat_service = ChatService(db)
        session = await chat_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Verify ownership
        if session.patient_id != current_user.patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        messages = await chat_service.get_session_messages(session_id, limit)
        return [ChatMessageResponse.from_orm(msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat messages"
        )

@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    try:
        # Authenticate user
        current_user = await get_current_patient(token, db)
        
        # Get chat session
        chat_service = ChatService(db)
        session = await chat_service.get_session(session_id)
        
        if not session or session.patient_id != current_user.patient.id:
            await websocket.close(code=4003)
            return
        
        # Accept connection
        await websocket.accept()
        active_connections[session_id] = websocket
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process message
                assistant_msg, requires_escalation = await chat_service.process_message(
                    session_id,
                    message_data["content"]
                )
                
                # Send response
                await websocket.send_json({
                    "message": ChatMessageResponse.from_orm(assistant_msg).dict(),
                    "requires_escalation": requires_escalation
                })
                
        except WebSocketDisconnect:
            active_connections.pop(session_id, None)
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011)
        except:
            pass

@router.post("/escalations/{escalation_id}/accept")
async def accept_chat_escalation(
    escalation_id: UUID,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db)
) -> ChatEscalationResponse:
    """Doctor accepts chat escalation"""
    try:
        chat_service = ChatService(db)
        escalation = await chat_service.accept_escalation(
            escalation_id,
            current_user.doctor.id
        )
        return ChatEscalationResponse.from_orm(escalation)
    except Exception as e:
        logger.error(f"Failed to accept chat escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept escalation"
        )

@router.post("/escalations/{escalation_id}/complete")
async def complete_chat_escalation(
    escalation_id: UUID,
    doctor_notes: str,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db)
) -> ChatEscalationResponse:
    """Complete chat escalation"""
    try:
        chat_service = ChatService(db)
        escalation = await chat_service.complete_escalation(
            escalation_id,
            doctor_notes
        )
        return ChatEscalationResponse.from_orm(escalation)
    except Exception as e:
        logger.error(f"Failed to complete chat escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete escalation"
        )
