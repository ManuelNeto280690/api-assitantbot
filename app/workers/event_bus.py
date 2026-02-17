"""Event bus for internal event publishing."""
from typing import Dict, Any
from app.workers.celery_app import celery_app
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """Internal event bus for automation triggers."""
    
    EVENT_TYPES = [
        "lead_created",
        "lead_updated",
        "message_received",
        "campaign_completed",
        "campaign_started",
        "voice_failed",
        "voice_completed",
        "scheduled_time",
        "email_opened",
        "email_clicked",
        "sms_delivered",
        "whatsapp_received",
    ]
    
    @staticmethod
    def publish(event_type: str, tenant_id: str, data: Dict[str, Any]):
        """
        Publish event to event bus.
        
        Args:
            event_type: Type of event
            tenant_id: Tenant ID for isolation
            data: Event data
        """
        if event_type not in EventBus.EVENT_TYPES:
            logger.warning(f"Unknown event type: {event_type}")
            return
        
        logger.info(f"Publishing event: {event_type}", tenant_id=tenant_id, data=data)
        
        # Send to automation engine
        celery_app.send_task(
            "app.workers.automation_engine.process_event",
            args=[event_type, tenant_id, data],
            queue="automation",
        )


# Global event bus instance
event_bus = EventBus()
