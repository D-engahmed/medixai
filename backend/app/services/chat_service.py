"""
Chat service with RAG support and auto-escalation
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
import numpy as np
from uuid import UUID

from app.models.chat import (
    ChatSession,
    ChatMessage,
    ChatEscalation,
    MedicalReference,
    ChatType,
    ChatStatus,
    MessageRole
)
from app.models.user import User
from app.core.security import encrypt_data, decrypt_data
from app.utils.logger import get_logger
from app.config.settings import get_settings

settings = get_settings()
logger = get_logger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize ML models
        self.medical_model = None  # BioMedX2 model
        self.general_model = None  # General chat model
        self.embedding_model = None  # For semantic search
        self._load_models()
    
    def _load_models(self):
        """Load ML models"""
        try:
            # Load BioMedX2 model
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.medical_model = AutoModelForCausalLM.from_pretrained(
                settings.BIOMEDX2_MODEL_PATH,
                device_map="auto",
                torch_dtype="auto"
            )
            self.medical_tokenizer = AutoTokenizer.from_pretrained(
                settings.BIOMEDX2_MODEL_PATH
            )
            
            # Load general chat model
            self.general_model = AutoModelForCausalLM.from_pretrained(
                settings.GENERAL_CHAT_MODEL_PATH,
                device_map="auto",
                torch_dtype="auto"
            )
            self.general_tokenizer = AutoTokenizer.from_pretrained(
                settings.GENERAL_CHAT_MODEL_PATH
            )
            
            # Load embedding model for semantic search
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
        except Exception as e:
            logger.error(f"Failed to load ML models: {str(e)}")
            raise
    
    async def create_chat_session(
        self,
        patient_id: UUID,
        chat_type: ChatType,
        initial_context: Dict[str, Any] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            patient_id=patient_id,
            chat_type=chat_type,
            context=initial_context or {},
            status=ChatStatus.ACTIVE
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Add system message
        await self.add_message(
            session.id,
            MessageRole.SYSTEM,
            self._get_system_prompt(chat_type)
        )
        
        return session
    
    def _get_system_prompt(self, chat_type: ChatType) -> str:
        """Get appropriate system prompt based on chat type"""
        if chat_type == ChatType.MEDICAL:
            return """You are an AI medical assistant. You can help with medical questions but:
            1. Always cite reliable medical sources
            2. Never make definitive diagnoses
            3. Recommend seeing a doctor for serious concerns
            4. Be clear about limitations
            5. Focus on general health information and guidance"""
        else:
            return """You are a helpful AI assistant. You can discuss general topics but:
            1. Defer to medical chat for health questions
            2. Be friendly and professional
            3. Ask for clarification when needed
            4. Stay within ethical boundaries
            5. Focus on being helpful while being clear about limitations"""
    
    async def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> ChatMessage:
        """Add a message to the chat session"""
        # Create message
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        # Generate embedding for semantic search
        if role == MessageRole.USER:
            message.embedding = self._generate_embedding(content)
        
        self.db.add(message)
        
        # Update session last_message_at
        session = await self.get_session(session_id)
        session.last_message_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """Get chat session by ID"""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get messages from a chat session"""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))
    
    async def process_message(
        self,
        session_id: UUID,
        user_message: str
    ) -> Tuple[ChatMessage, bool]:
        """Process user message and generate response"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("Invalid session ID")
        
        # Add user message
        user_msg = await self.add_message(
            session_id,
            MessageRole.USER,
            user_message
        )
        
        # Get relevant documents for medical chat
        relevant_docs = []
        if session.chat_type == ChatType.MEDICAL:
            relevant_docs = await self._get_relevant_documents(user_message)
            session.relevant_documents = [doc.id for doc in relevant_docs]
        
        # Generate response
        response_content, confidence = await self._generate_response(
            session,
            user_message,
            relevant_docs
        )
        
        # Check if response requires escalation
        requires_escalation = self._check_escalation_needed(
            response_content,
            confidence,
            session.chat_type
        )
        
        # Add assistant response
        assistant_msg = await self.add_message(
            session_id,
            MessageRole.ASSISTANT,
            response_content,
            metadata={
                "confidence": confidence,
                "requires_escalation": requires_escalation,
                "relevant_docs": [str(doc.id) for doc in relevant_docs]
            }
        )
        
        # Handle escalation if needed
        if requires_escalation:
            await self._handle_escalation(
                session,
                assistant_msg,
                "Low confidence or critical medical concern detected"
            )
        
        return assistant_msg, requires_escalation
    
    async def _get_relevant_documents(
        self,
        query: str,
        top_k: int = 5
    ) -> List[MedicalReference]:
        """Get relevant medical references using semantic search"""
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Get all references (in production, use a vector database)
        result = await self.db.execute(
            select(MedicalReference)
            .where(MedicalReference.is_verified == True)
        )
        references = result.scalars().all()
        
        # Calculate similarities
        similarities = []
        for ref in references:
            if ref.embedding:
                similarity = np.dot(
                    query_embedding,
                    ref.embedding
                )
                similarities.append((similarity, ref))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [ref for _, ref in similarities[:top_k]]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embedding_model.encode(text).tolist()
    
    async def _generate_response(
        self,
        session: ChatSession,
        user_message: str,
        relevant_docs: List[MedicalReference]
    ) -> Tuple[str, float]:
        """Generate response using appropriate model"""
        try:
            # Prepare context
            messages = await self.get_session_messages(session.id)
            context = self._prepare_context(messages, relevant_docs)
            
            # Choose model based on chat type
            model = self.medical_model if session.chat_type == ChatType.MEDICAL else self.general_model
            tokenizer = self.medical_tokenizer if session.chat_type == ChatType.MEDICAL else self.general_tokenizer
            
            # Generate response
            inputs = tokenizer(context, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs,
                max_length=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate confidence score
            confidence = outputs.sequences_scores.item() if hasattr(outputs, 'sequences_scores') else 0.8
            
            return response, confidence
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response. Please try again or contact support if the problem persists.", 0.0
    
    def _prepare_context(
        self,
        messages: List[ChatMessage],
        relevant_docs: List[MedicalReference]
    ) -> str:
        """Prepare context for model input"""
        context = ""
        
        # Add relevant documents
        if relevant_docs:
            context += "Relevant medical information:\n"
            for doc in relevant_docs:
                context += f"- {doc.title}: {doc.content}\n"
            context += "\n"
        
        # Add conversation history
        for msg in messages[-5:]:  # Last 5 messages
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            context += f"{role}: {msg.content}\n"
        
        return context
    
    def _check_escalation_needed(
        self,
        response: str,
        confidence: float,
        chat_type: ChatType
    ) -> bool:
        """Check if response requires escalation"""
        if chat_type != ChatType.MEDICAL:
            return False
        
        # Check confidence threshold
        if confidence < settings.CHAT_AUTO_ESCALATION_THRESHOLD:
            return True
        
        # Check for critical keywords
        critical_keywords = [
            "emergency",
            "immediate medical attention",
            "call 911",
            "life-threatening",
            "severe",
            "critical"
        ]
        
        return any(keyword in response.lower() for keyword in critical_keywords)
    
    async def _handle_escalation(
        self,
        session: ChatSession,
        trigger_message: ChatMessage,
        reason: str
    ) -> ChatEscalation:
        """Handle chat escalation to doctor"""
        # Create escalation record
        escalation = ChatEscalation(
            session_id=session.id,
            trigger_message_id=trigger_message.id,
            reason=reason,
            status="pending"
        )
        
        # Update session status
        session.status = ChatStatus.ESCALATED
        
        self.db.add(escalation)
        await self.db.commit()
        
        # Notify available doctors (implement in notification service)
        # await self.notification_service.notify_doctors(escalation)
        
        return escalation
    
    async def accept_escalation(
        self,
        escalation_id: UUID,
        doctor_id: UUID
    ) -> ChatEscalation:
        """Doctor accepts chat escalation"""
        escalation = await self.db.get(ChatEscalation, escalation_id)
        if not escalation:
            raise ValueError("Invalid escalation ID")
        
        escalation.doctor_id = doctor_id
        escalation.status = "accepted"
        await self.db.commit()
        
        return escalation
    
    async def complete_escalation(
        self,
        escalation_id: UUID,
        doctor_notes: str
    ) -> ChatEscalation:
        """Complete chat escalation"""
        escalation = await self.db.get(ChatEscalation, escalation_id)
        if not escalation:
            raise ValueError("Invalid escalation ID")
        
        escalation.status = "completed"
        escalation.doctor_notes = doctor_notes
        escalation.resolved_at = datetime.utcnow()
        
        # Update session status
        session = await self.get_session(escalation.session_id)
        session.status = ChatStatus.ACTIVE
        
        await self.db.commit()
        
        return escalation
