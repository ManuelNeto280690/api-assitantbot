"""Tenant model for multi-tenant isolation."""
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Tenant(Base):
    """
    Tenant model for multi-tenant SaaS.
    
    Each tenant represents a separate organization/customer.
    All operational data is isolated by tenant_id.
    """
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), default="free", nullable=False)  # free, starter, pro, enterprise
    
    # JSONB for flexible tenant settings
    settings = Column(JSONB, default={}, nullable=False)
    
    # Usage tracking
    usage_limits = Column(JSONB, default={
        "max_leads": 1000,
        "max_campaigns_per_month": 10,
        "max_sms_per_month": 1000,
        "max_emails_per_month": 5000,
        "max_voice_calls_per_month": 100,
    }, nullable=False)
    
    current_usage = Column(JSONB, default={
        "leads_count": 0,
        "campaigns_this_month": 0,
        "sms_this_month": 0,
        "emails_this_month": 0,
        "voice_calls_this_month": 0,
    }, nullable=False)
    
    # Relationships
    memberships = relationship("Membership", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="tenant", cascade="all, delete-orphan")
    automations = relationship("Automation", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name} ({self.slug})>"
