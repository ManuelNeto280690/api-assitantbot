"""Campaign models for multi-channel campaigns."""
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Index, DateTime, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    """
    Campaign model for multi-channel outreach.
    
    Supports SMS, WhatsApp, Email, and Voice channels.
    """
    __tablename__ = "campaigns"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Channel
    channel = Column(String(20), nullable=False)  # sms, whatsapp, email, voice
    
    # Lead list
    lead_list_id = Column(UUID(as_uuid=True), ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True)
    
    # Scheduling
    start_datetime = Column(DateTime, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Retry strategy (JSONB)
    # Example: {"max_attempts": 3, "delays": [30, 120, 360], "retry_on": ["busy", "no_answer"]}
    retry_strategy = Column(JSONB, default={
        "max_attempts": 3,
        "delays_minutes": [30, 120, 360],
        "retry_on": ["busy", "no_answer", "failed"]
    }, nullable=False)
    
    # Campaign status
    status = Column(String(20), default="draft", nullable=False)  # draft, scheduled, running, paused, completed, cancelled
    
    # Message content (JSONB for flexibility)
    # SMS/WhatsApp: {"body": "text"}
    # Email: {"subject": "...", "body": "...", "template_id": "..."}
    # Voice: {"script": "...", "assistant_id": "..."}
    message_content = Column(JSONB, default={}, nullable=False)
    
    # Statistics
    total_targets = Column(Integer, default=0, nullable=False)
    completed_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="campaigns")
    lead_list = relationship("LeadList", back_populates="campaigns")
    schedule_rules = relationship("CampaignScheduleRule", back_populates="campaign", cascade="all, delete-orphan")
    targets = relationship("CampaignTarget", back_populates="campaign", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_campaigns_tenant_status", "tenant_id", "status"),
        Index("ix_campaigns_tenant_channel", "tenant_id", "channel"),
    )
    
    def __repr__(self):
        return f"<Campaign {self.name} ({self.channel})>"


class CampaignScheduleRule(Base):
    """
    Schedule rules for campaigns.
    
    Defines allowed hours and days for campaign execution.
    """
    __tablename__ = "campaign_schedule_rules"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Time windows (24-hour format)
    start_hour = Column(Integer, default=9, nullable=False)  # 9 AM
    end_hour = Column(Integer, default=17, nullable=False)  # 5 PM
    
    # Days allowed (0=Monday, 6=Sunday)
    days_allowed = Column(ARRAY(Integer), default=[0, 1, 2, 3, 4], nullable=False)  # Weekdays
    
    # Blackout dates (holidays, etc.)
    blackout_dates = Column(ARRAY(String), default=[], nullable=False)  # ["2024-12-25", "2024-01-01"]
    
    # Relationship
    campaign = relationship("Campaign", back_populates="schedule_rules")
    
    def __repr__(self):
        return f"<CampaignScheduleRule campaign={self.campaign_id}>"


class CampaignTarget(Base):
    """
    Individual campaign target tracking.
    
    Tracks each lead's progress through the campaign.
    """
    __tablename__ = "campaign_targets"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, retrying, completed, failed
    
    # Attempt tracking
    attempt_count = Column(Integer, default=0, nullable=False)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    last_attempt_at = Column(DateTime, nullable=True)
    
    # Result metadata (JSONB)
    # Stores channel-specific results: message_id, delivery_status, error_code, etc.
    metadata = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="targets")
    lead = relationship("Lead", back_populates="campaign_targets")
    
    __table_args__ = (
        Index("ix_campaign_targets_campaign_status", "campaign_id", "status"),
        Index("ix_campaign_targets_next_attempt", "next_attempt_at"),
        Index("ix_campaign_targets_campaign_lead", "campaign_id", "lead_id", unique=True),
    )
    
    def __repr__(self):
        return f"<CampaignTarget campaign={self.campaign_id} lead={self.lead_id} status={self.status}>"
