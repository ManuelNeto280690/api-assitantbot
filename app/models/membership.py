"""Membership model linking users to tenants."""
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Membership(Base):
    """
    Membership model linking Supabase users to tenants.
    
    This is the critical table for multi-tenant security.
    user_id comes from Supabase Auth (auth.users.id).
    """
    __tablename__ = "memberships"
    
    # Supabase Auth user ID (UUID from auth.users)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Tenant reference
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Role within this tenant
    role = Column(String(50), nullable=False, default="viewer")  # super_admin, tenant_admin, operator, viewer
    
    # Additional user metadata
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="memberships")
    
    # Composite index for fast lookups
    __table_args__ = (
        Index("ix_memberships_user_tenant", "user_id", "tenant_id"),
    )
    
    def __repr__(self):
        return f"<Membership user={self.user_id} tenant={self.tenant_id} role={self.role}>"
