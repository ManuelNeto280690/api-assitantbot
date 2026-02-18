"""Smart dispatcher for campaign execution."""
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.campaign import Campaign, CampaignTarget
from app.models.lead import Lead
from app.models.tenant import Tenant
from app.utils.rate_limiter import rate_limiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.smart_dispatcher.dispatch_campaign_target")
def dispatch_campaign_target(target_id: str):
    """
    Dispatch campaign target to appropriate channel.
    
    Args:
        target_id: Campaign target ID
    """
    import asyncio
    asyncio.run(_dispatch_campaign_target_async(UUID(target_id)))


async def _dispatch_campaign_target_async(target_id: UUID):
    """Async implementation of campaign target dispatch."""
    async with AsyncSessionLocal() as db:
        try:
            # Get target, campaign, and lead
            target = await db.get(CampaignTarget, target_id)
            if not target:
                logger.error(f"Target {target_id} not found")
                return
            
            campaign = await db.get(Campaign, target.campaign_id)
            lead = await db.get(Lead, target.lead_id)
            tenant = await db.get(Tenant, campaign.tenant_id)
            
            if not campaign or not lead or not tenant:
                logger.error(f"Missing campaign, lead, or tenant for target {target_id}")
                return
            
            # Check rate limits
            rate_key = f"tenant:{tenant.id}:{campaign.channel}"
            is_allowed, remaining = rate_limiter.check_rate_limit(
                rate_key,
                limit=100,  # 100 per minute per channel per tenant
                window_seconds=60
            )
            
            if not is_allowed:
                # Reschedule for 1 minute later
                target.next_attempt_at = datetime.utcnow() + timedelta(minutes=1)
                await db.commit()
                logger.warning(f"Rate limit exceeded for {rate_key}, rescheduling")
                return
            
            # Dispatch to appropriate channel
            if campaign.channel == "sms":
                await _dispatch_sms(target, campaign, lead, db)
            elif campaign.channel == "whatsapp":
                await _dispatch_whatsapp(target, campaign, lead, db)
            elif campaign.channel == "email":
                await _dispatch_email(target, campaign, lead, db)
            elif campaign.channel == "voice":
                await _dispatch_voice(target, campaign, lead, db)
            else:
                logger.error(f"Unknown channel: {campaign.channel}")
                target.status = "failed"
                target.extra_data["error"] = f"Unknown channel: {campaign.channel}"
                await db.commit()
            
        except Exception as e:
            logger.error(f"Error dispatching target {target_id}: {str(e)}")
            await db.rollback()


async def _dispatch_sms(target: CampaignTarget, campaign: Campaign, lead: Lead, db):
    """Dispatch SMS message."""
    try:
        # Send to Brevo SMS integration
        celery_app.send_task(
            "app.integrations.brevo.sms.send_sms",
            args=[str(target.id), lead.phone, campaign.message_content.get("body", "")],
            queue="dispatcher",
        )
        
        target.last_attempt_at = datetime.utcnow()
        target.attempt_count += 1
        await db.commit()
        
    except Exception as e:
        await _handle_dispatch_failure(target, campaign, str(e), db)


async def _dispatch_whatsapp(target: CampaignTarget, campaign: Campaign, lead: Lead, db):
    """Dispatch WhatsApp message."""
    try:
        celery_app.send_task(
            "app.integrations.brevo.whatsapp.send_whatsapp",
            args=[str(target.id), lead.phone, campaign.message_content.get("body", "")],
            queue="dispatcher",
        )
        
        target.last_attempt_at = datetime.utcnow()
        target.attempt_count += 1
        await db.commit()
        
    except Exception as e:
        await _handle_dispatch_failure(target, campaign, str(e), db)


async def _dispatch_email(target: CampaignTarget, campaign: Campaign, lead: Lead, db):
    """Dispatch email."""
    try:
        celery_app.send_task(
            "app.integrations.brevo.email.send_email",
            args=[
                str(target.id),
                lead.email,
                campaign.message_content.get("subject", ""),
                campaign.message_content.get("body", "")
            ],
            queue="dispatcher",
        )
        
        target.last_attempt_at = datetime.utcnow()
        target.attempt_count += 1
        await db.commit()
        
    except Exception as e:
        await _handle_dispatch_failure(target, campaign, str(e), db)


async def _dispatch_voice(target: CampaignTarget, campaign: Campaign, lead: Lead, db):
    """Dispatch voice call."""
    try:
        celery_app.send_task(
            "app.integrations.vapi.voice.make_call",
            args=[
                str(target.id),
                lead.phone,
                campaign.message_content.get("assistant_id", ""),
                campaign.message_content.get("script", "")
            ],
            queue="dispatcher",
        )
        
        target.last_attempt_at = datetime.utcnow()
        target.attempt_count += 1
        await db.commit()
        
    except Exception as e:
        await _handle_dispatch_failure(target, campaign, str(e), db)


async def _handle_dispatch_failure(target: CampaignTarget, campaign: Campaign, error: str, db):
    """Handle dispatch failure with retry logic."""
    target.attempt_count += 1
    target.last_attempt_at = datetime.utcnow()
    
    retry_strategy = campaign.retry_strategy
    max_attempts = retry_strategy.get("max_attempts", 3)
    
    if target.attempt_count >= max_attempts:
        # Max retries exceeded - send to dead letter queue
        target.status = "failed"
        target.extra_data["error"] = error
        target.extra_data["max_retries_exceeded"] = True
        
        logger.error(f"Target {target.id} failed after {max_attempts} attempts")
    else:
        # Schedule retry
        delays = retry_strategy.get("delays_minutes", [30, 120, 360])
        delay_index = min(target.attempt_count - 1, len(delays) - 1)
        delay_minutes = delays[delay_index]
        
        target.status = "retrying"
        target.next_attempt_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        target.extra_data["last_error"] = error
        
        logger.info(f"Rescheduling target {target.id} in {delay_minutes} minutes")
    
    await db.commit()
