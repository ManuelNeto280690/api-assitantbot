"""Brevo WhatsApp integration."""
from uuid import UUID
from typing import Optional
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.campaign import CampaignTarget
from app.integrations.brevo.client import brevo_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.integrations.brevo.whatsapp.send_whatsapp")
def send_whatsapp(target_id: Optional[str], phone: str, content: str, template_id: Optional[str] = None):
    """
    Send WhatsApp message via Brevo.
    
    Args:
        target_id: Campaign target ID
        phone: Phone number
        content: Message content
        template_id: Optional template ID
    """
    import asyncio
    asyncio.run(_send_whatsapp_async(UUID(target_id) if target_id else None, phone, content, template_id))


async def _send_whatsapp_async(target_id: Optional[UUID], phone: str, content: str, template_id: Optional[str]):
    """Async implementation of WhatsApp sending."""
    try:
        # Send WhatsApp
        response = await brevo_client.send_whatsapp(phone, content, template_id)
        
        logger.info(f"WhatsApp sent successfully to {phone}", response=response)
        
        # Update target if provided
        if target_id:
            async with AsyncSessionLocal() as db:
                target = await db.get(CampaignTarget, target_id)
                if target:
                    target.status = "completed"
                    target.metadata["message_id"] = response.get("messageId")
                    await db.commit()
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp to {phone}: {str(e)}")
        
        if target_id:
            async with AsyncSessionLocal() as db:
                target = await db.get(CampaignTarget, target_id)
                if target:
                    target.status = "failed"
                    target.metadata["error"] = str(e)
                    await db.commit()
        
        raise
