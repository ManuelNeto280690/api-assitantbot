"""Conversation and message models for unified chat."""
from sqlalchemy import Column, String, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Conversation(Base):
    """
    Conversation model for unified inbox.
    
    Tracks conversations across all channels.
    """
    __tablename__ = "conversations"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Lead reference
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Channel
    channel = Column(String(20), nullable=False)  # sms, whatsapp, email, voice
    
    # Status
    status = Column(String(20), default="open", nullable=False)  # open, closed, archived
    
    # External conversation ID (from channel provider)
    external_id = Column(String(255), nullable=True, index=True)
    
    # Metadata (JSONB)
    extra_data = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="conversations")
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    __table_args__ = (
        Index("ix_conversations_tenant_status", "tenant_id", "status"),
        Index("ix_conversations_tenant_lead", "tenant_id", "lead_id"),
    )
    
    def __repr__(self):
        return f"<Conversation lead={self.lead_id} channel={self.channel}>"


class Message(Base):
    """
    Message model for conversation history.
    
    Stores messages from both bot and human agents.
    """
    __tablename__ = "messages"
    
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Sender type
    sender_type = Column(String(20), nullable=False)  # bot, human, system
    
    # Sender ID (user_id for human, bot_id for bot)
    sender_id = Column(String(255), nullable=True)
    
    # Message content
    content = Column(Text, nullable=False)
    
    # Message type
    message_type = Column(String(20), default="text", nullable=False)  # text, image, file, audio, video
    
    # Status
    status = Column(String(20), default="sent", nullable=False)  # sent, delivered, read, failed
    
    # External message ID (from channel provider)
    external_id = Column(String(255), nullable=True, index=True)
    
    # Metadata (JSONB)
    # Stores attachments, delivery info, etc.
    extra_data = Column(JSONB, default={}, nullable=False)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")
    
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<Message conversation={self.conversation_id} sender={self.sender_type}>"
