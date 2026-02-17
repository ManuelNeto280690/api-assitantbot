"""Lead list models for static and dynamic segmentation."""
from sqlalchemy import Column, String, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class LeadList(Base):
    """
    Lead list for campaign targeting.
    
    Supports both static and dynamic lists.
    - Static: manually added leads
    - Dynamic: leads matching filter criteria
    """
    __tablename__ = "lead_lists"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # List type
    list_type = Column(String(20), nullable=False, default="static")  # static, dynamic
    
    # Filters for dynamic lists (JSONB)
    # Example: {"status": ["qualified", "new"], "tags": ["vip"], "custom_fields.industry": "tech"}
    filters = Column(JSONB, default={}, nullable=True)
    
    # Relationships
    items = relationship("LeadListItem", back_populates="lead_list", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="lead_list")
    
    __table_args__ = (
        Index("ix_lead_lists_tenant_type", "tenant_id", "list_type"),
    )
    
    def __repr__(self):
        return f"<LeadList {self.name} ({self.list_type})>"


class LeadListItem(Base):
    """
    Items in a lead list (for static lists).
    
    Dynamic lists don't use this table - they evaluate filters at runtime.
    """
    __tablename__ = "lead_list_items"
    
    lead_list_id = Column(UUID(as_uuid=True), ForeignKey("lead_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    added_at = Column(DateTime, nullable=False)
    
    # Relationships
    lead_list = relationship("LeadList", back_populates="items")
    lead = relationship("Lead", back_populates="list_items")
    
    __table_args__ = (
        Index("ix_lead_list_items_list_lead", "lead_list_id", "lead_id", unique=True),
    )
    
    def __repr__(self):
        return f"<LeadListItem list={self.lead_list_id} lead={self.lead_id}>"
