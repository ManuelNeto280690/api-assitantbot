"""Brevo SMS integration."""
from uuid import UUID
from typing import Optional
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.campaign import CampaignTarget
from app.integrations.brevo.client import brevo_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.integrations.brevo.sms.send_sms")
def send_sms(target_id: Optional[str], phone: str, content: str):
    """
    Send SMS via Brevo.
    
    Args:
        target_id: Campaign target ID (optional for automation)
        phone: Phone number
        content: Message content
    """
    import asyncio
    asyncio.run(_send_sms_async(UUID(target_id) if target_id else None, phone, content))


async def _send_sms_async(target_id: Optional[UUID], phone: str, content: str):
    """Async implementation of SMS sending."""
    try:
        # Send SMS
        response = await brevo_client.send_sms(phone, content)
        
        logger.info(f"SMS sent successfully to {phone}", response=response)
        
        # Update target if provided
        if target_id:
            async with AsyncSessionLocal() as db:
                target = await db.get(CampaignTarget, target_id)
                if target:
                    target.status = "completed"
                    target.metadata["message_id"] = response.get("messageId")
                    target.metadata["reference"] = response.get("reference")
                    await db.commit()
        
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        
        # Update target status
        if target_id:
            async with AsyncSessionLocal() as db:
                target = await db.get(CampaignTarget, target_id)
                if target:
                    target.status = "failed"
                    target.metadata["error"] = str(e)
                    await db.commit()
        
        raise
