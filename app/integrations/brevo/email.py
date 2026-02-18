"""Brevo Email integration."""
from uuid import UUID
from typing import Optional
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.campaign import CampaignTarget
from app.integrations.brevo.client import brevo_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.integrations.brevo.email.send_email")
def send_email(target_id: Optional[str], to: str, subject: str, html_content: str):
    """
    Send email via Brevo.
    
    Args:
        target_id: Campaign target ID
        to: Recipient email
        subject: Email subject
        html_content: HTML content
    """
    import asyncio
    asyncio.run(_send_email_async(UUID(target_id) if target_id else None, to, subject, html_content))


async def _send_email_async(target_id: Optional[UUID], to: str, subject: str, html_content: str):
    """Async implementation of email sending."""
    try:
        # Send email
        response = await brevo_client.send_email(to, subject, html_content)
        
        logger.info(f"Email sent successfully to {to}", response=response)
        
        # Update target if provided
        if target_id:
            async with AsyncSessionLocal() as db:
                target = await db.get(CampaignTarget, target_id)
                if target:
                    target.status = "completed"
                    target.extra_data["message_id"] = response.get("messageId")
                    await db.commit()
        
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}")
        
        if target_id:
            async with AsyncSessionLocal() as db:
                target = await db.get(CampaignTarget, target_id)
                if target:
                    target.status = "failed"
                    target.extra_data["error"] = str(e)
                    await db.commit()
        
        raise
