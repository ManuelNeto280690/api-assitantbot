"""Automation models for event-driven workflows."""
from sqlalchemy import Column, String, ForeignKey, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Automation(Base):
    """
    Automation model for event-driven workflows.
    
    Trigger → Conditions → Actions
    """
    __tablename__ = "automations"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Trigger type
    trigger_type = Column(String(50), nullable=False)  # lead_created, message_received, campaign_completed, voice_failed, scheduled_time
    
    # Trigger configuration (JSONB)
    # For scheduled_time: {"cron": "0 9 * * *", "timezone": "UTC"}
    # For event triggers: {"event_filters": {...}}
    trigger_config = Column(JSONB, default={}, nullable=False)
    
    # Status
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="automations")
    conditions = relationship("AutomationCondition", back_populates="automation", cascade="all, delete-orphan", order_by="AutomationCondition.order")
    actions = relationship("AutomationAction", back_populates="automation", cascade="all, delete-orphan", order_by="AutomationAction.order")
    
    __table_args__ = (
        Index("ix_automations_tenant_enabled", "tenant_id", "enabled"),
        Index("ix_automations_trigger_type", "trigger_type"),
    )
    
    def __repr__(self):
        return f"<Automation {self.name} ({self.trigger_type})>"


class AutomationCondition(Base):
    """
    Conditions for automation execution.
    
    All conditions must be met for actions to execute (AND logic).
    """
    __tablename__ = "automation_conditions"
    
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Condition type
    condition_type = Column(String(50), nullable=False)  # field_equals, field_contains, tag_has, time_range, etc.
    
    # Condition configuration (JSONB)
    # Examples:
    # {"field": "status", "operator": "equals", "value": "qualified"}
    # {"field": "tags", "operator": "contains", "value": "vip"}
    # {"start_hour": 9, "end_hour": 17, "timezone": "America/New_York"}
    condition_config = Column(JSONB, default={}, nullable=False)
    
    # Execution order
    order = Column(Integer, default=0, nullable=False)
    
    # Relationship
    automation = relationship("Automation", back_populates="conditions")
    
    def __repr__(self):
        return f"<AutomationCondition automation={self.automation_id} type={self.condition_type}>"


class AutomationAction(Base):
    """
    Actions to execute when automation triggers and conditions are met.
    """
    __tablename__ = "automation_actions"
    
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Action type
    action_type = Column(String(50), nullable=False)  # send_email, send_sms, update_lead, create_task, trigger_webhook, etc.
    
    # Action configuration (JSONB)
    # Examples:
    # {"channel": "email", "template_id": "...", "subject": "..."}
    # {"field": "status", "value": "contacted"}
    # {"webhook_url": "https://...", "method": "POST", "payload": {...}}
    action_config = Column(JSONB, default={}, nullable=False)
    
    # Execution order
    order = Column(Integer, default=0, nullable=False)
    
    # Delay before execution (seconds)
    delay_seconds = Column(Integer, default=0, nullable=False)
    
    # Relationship
    automation = relationship("Automation", back_populates="actions")
    
    def __repr__(self):
        return f"<AutomationAction automation={self.automation_id} type={self.action_type}>"
