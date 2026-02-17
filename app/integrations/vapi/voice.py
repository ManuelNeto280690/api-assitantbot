"""VAPI Voice integration with smart retry logic."""
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.campaign import CampaignTarget, Campaign
from app.integrations.vapi.client import vapi_client
from app.workers.event_bus import event_bus
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Voice call retry strategy
VOICE_RETRY_STRATEGY = {
    "busy": 30,  # Retry in 30 minutes
    "no_answer": 120,  # Retry in 2 hours
    "voicemail": None,  # Mark as completed
    "failed": None,  # Mark as failed
}


@celery_app.task(name="app.integrations.vapi.voice.make_call")
def make_call(target_id: str, phone: str, assistant_id: str, script: Optional[str] = None):
    """
    Make voice call via VAPI.
    
    Args:
        target_id: Campaign target ID
        phone: Phone number
        assistant_id: VAPI assistant ID
        script: Optional script override
    """
    import asyncio
    asyncio.run(_make_call_async(UUID(target_id), phone, assistant_id, script))


async def _make_call_async(target_id: UUID, phone: str, assistant_id: str, script: Optional[str]):
    """Async implementation of voice call."""
    try:
        # Create call
        metadata = {"target_id": str(target_id)}
        if script:
            metadata["script"] = script
        
        response = await vapi_client.create_call(phone, assistant_id, metadata)
        
        logger.info(f"Voice call initiated to {phone}", response=response)
        
        # Update target
        async with AsyncSessionLocal() as db:
            target = await db.get(CampaignTarget, target_id)
            if target:
                target.metadata["call_id"] = response.get("id")
                target.metadata["call_status"] = "initiated"
                await db.commit()
        
    except Exception as e:
        logger.error(f"Failed to initiate call to {phone}: {str(e)}")
        
        async with AsyncSessionLocal() as db:
            target = await db.get(CampaignTarget, target_id)
            if target:
                target.status = "failed"
                target.metadata["error"] = str(e)
                await db.commit()
        
        raise


async def handle_voice_webhook(call_id: str, status: str, metadata: dict):
    """
    Handle VAPI webhook for call status updates.
    
    Args:
        call_id: Call ID
        status: Call status (busy, no_answer, voicemail, completed, failed)
        metadata: Additional metadata
    """
    target_id = metadata.get("target_id")
    if not target_id:
        logger.warning(f"No target_id in webhook metadata for call {call_id}")
        return
    
    async with AsyncSessionLocal() as db:
        try:
            target = await db.get(CampaignTarget, UUID(target_id))
            if not target:
                logger.error(f"Target {target_id} not found")
                return
            
            campaign = await db.get(Campaign, target.campaign_id)
            
            # Update metadata
            target.metadata["call_status"] = status
            target.metadata["call_completed_at"] = datetime.utcnow().isoformat()
            
            # Apply smart retry logic
            retry_delay = VOICE_RETRY_STRATEGY.get(status)
            
            if retry_delay is not None:
                # Schedule retry
                target.status = "retrying"
                target.next_attempt_at = datetime.utcnow() + timedelta(minutes=retry_delay)
                target.metadata["retry_reason"] = status
                
                logger.info(f"Rescheduling call for target {target_id} in {retry_delay} minutes due to {status}")
                
                # Publish event
                event_bus.publish(
                    "voice_failed",
                    str(campaign.tenant_id),
                    {
                        "target_id": str(target_id),
                        "call_id": call_id,
                        "status": status,
                        "retry_in_minutes": retry_delay
                    }
                )
            
            elif status == "voicemail":
                # Mark as completed
                target.status = "completed"
                target.metadata["completed_reason"] = "voicemail"
                
                logger.info(f"Call to voicemail for target {target_id}, marking as completed")
                
                event_bus.publish(
                    "voice_completed",
                    str(campaign.tenant_id),
                    {
                        "target_id": str(target_id),
                        "call_id": call_id,
                        "status": "voicemail"
                    }
                )
            
            elif status == "completed":
                # Successfully completed
                target.status = "completed"
                
                logger.info(f"Call completed successfully for target {target_id}")
                
                event_bus.publish(
                    "voice_completed",
                    str(campaign.tenant_id),
                    {
                        "target_id": str(target_id),
                        "call_id": call_id,
                        "status": "completed"
                    }
                )
            
            else:
                # Failed
                target.status = "failed"
                target.metadata["failure_reason"] = status
                
                logger.error(f"Call failed for target {target_id}: {status}")
                
                event_bus.publish(
                    "voice_failed",
                    str(campaign.tenant_id),
                    {
                        "target_id": str(target_id),
                        "call_id": call_id,
                        "status": status
                    }
                )
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error handling voice webhook: {str(e)}")
            await db.rollback()
