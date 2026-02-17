"""Lead model for CRM."""
from sqlalchemy import Column, String, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Lead(Base):
    """
    Lead model for CRM.
    
    Stores contact information with timezone for campaign scheduling.
    """
    __tablename__ = "leads"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    
    # Timezone for campaign scheduling (IANA timezone, e.g., "America/New_York")
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Lead status
    status = Column(String(50), default="new", nullable=False)  # new, contacted, qualified, converted, lost
    
    # Custom fields stored as JSONB
    custom_fields = Column(JSONB, default={}, nullable=False)
    
    # Tags for segmentation
    tags = Column(JSONB, default=[], nullable=False)
    
    # Source tracking
    source = Column(String(100), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="leads")
    list_items = relationship("LeadListItem", back_populates="lead", cascade="all, delete-orphan")
    campaign_targets = relationship("CampaignTarget", back_populates="lead", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_leads_tenant_email", "tenant_id", "email"),
        Index("ix_leads_tenant_phone", "tenant_id", "phone"),
        Index("ix_leads_tenant_status", "tenant_id", "status"),
    )
    
    def __repr__(self):
        return f"<Lead {self.email or self.phone}>"
