"""Campaign scheduler worker - runs every minute."""
from datetime import datetime
from typing import List
from sqlalchemy import select, and_
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.campaign import Campaign, CampaignTarget, CampaignScheduleRule
from app.models.lead import Lead
from app.utils.timezone_helper import timezone_helper
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.campaign_scheduler.process_pending_targets")
def process_pending_targets():
    """
    Process pending campaign targets.
    
    Runs every minute to find targets ready for execution.
    """
    import asyncio
    asyncio.run(_process_pending_targets_async())


async def _process_pending_targets_async():
    """Async implementation of campaign target processing."""
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        
        # Find targets ready for processing
        query = select(CampaignTarget).where(
            and_(
                CampaignTarget.status.in_(["pending", "retrying"]),
                CampaignTarget.next_attempt_at <= now,
                CampaignTarget.deleted_at.is_(None)
            )
        ).limit(1000)  # Process in batches
        
        result = await db.execute(query)
        targets = result.scalars().all()
        
        logger.info(f"Found {len(targets)} targets ready for processing")
        
        for target in targets:
            try:
                # Get campaign and lead
                campaign = await db.get(Campaign, target.campaign_id)
                lead = await db.get(Lead, target.lead_id)
                
                if not campaign or not lead:
                    continue
                
                # Skip if campaign is not running
                if campaign.status != "running":
                    continue
                
                # Get schedule rules
                schedule_query = select(CampaignScheduleRule).where(
                    CampaignScheduleRule.campaign_id == campaign.id
                )
                schedule_result = await db.execute(schedule_query)
                schedule_rule = schedule_result.scalar_one_or_none()
                
                # Check if within allowed schedule
                if schedule_rule:
                    lead_time = timezone_helper.get_current_time_in_timezone(lead.timezone)
                    
                    if not timezone_helper.is_within_schedule(
                        lead_time,
                        schedule_rule.start_hour,
                        schedule_rule.end_hour,
                        schedule_rule.days_allowed,
                        schedule_rule.blackout_dates
                    ):
                        # Reschedule for next available time
                        next_time = timezone_helper.get_next_available_time(
                            lead_time,
                            schedule_rule.start_hour,
                            schedule_rule.end_hour,
                            schedule_rule.days_allowed,
                            lead.timezone
                        )
                        target.next_attempt_at = next_time
                        await db.commit()
                        logger.info(f"Rescheduled target {target.id} to {next_time}")
                        continue
                
                # Dispatch to smart dispatcher
                celery_app.send_task(
                    "app.workers.smart_dispatcher.dispatch_campaign_target",
                    args=[str(target.id)],
                    queue="dispatcher",
                )
                
                # Update status
                target.status = "processing"
                await db.commit()
                
                logger.info(f"Dispatched target {target.id} for campaign {campaign.id}")
                
            except Exception as e:
                logger.error(f"Error processing target {target.id}: {str(e)}")
                await db.rollback()
