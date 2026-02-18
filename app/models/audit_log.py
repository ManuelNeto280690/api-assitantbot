"""Audit log model for security and compliance."""
from sqlalchemy import Column, String, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET

from app.database import Base


class AuditLog(Base):
    """
    Audit log for tracking all important actions.
    
    Records who did what, when, and from where.
    """
    __tablename__ = "audit_logs"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # User who performed the action
    user_id = Column(String(255), nullable=False, index=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # create, update, delete, login, etc.
    resource_type = Column(String(50), nullable=False)  # lead, campaign, tenant, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Changes (JSONB)
    # Stores before/after values for updates
    changes = Column(JSONB, default={}, nullable=False)
    
    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Additional metadata
    extra_data = Column(JSONB, default={}, nullable=False)
    
    __table_args__ = (
        Index("ix_audit_logs_tenant_created", "tenant_id", "created_at"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type} by {self.user_id}>"
