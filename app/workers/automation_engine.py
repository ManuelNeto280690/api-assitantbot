"""Automation engine worker."""
from typing import Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, and_
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.automation import Automation, AutomationCondition, AutomationAction
from app.models.lead import Lead
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.automation_engine.process_event")
def process_event(event_type: str, tenant_id: str, data: Dict[str, Any]):
    """
    Process event and trigger matching automations.
    
    Args:
        event_type: Type of event
        tenant_id: Tenant ID
        data: Event data
    """
    import asyncio
    asyncio.run(_process_event_async(event_type, UUID(tenant_id), data))


async def _process_event_async(event_type: str, tenant_id: UUID, data: Dict[str, Any]):
    """Async implementation of event processing."""
    async with AsyncSessionLocal() as db:
        try:
            # Find enabled automations for this event type
            query = select(Automation).where(
                and_(
                    Automation.tenant_id == tenant_id,
                    Automation.trigger_type == event_type,
                    Automation.enabled == True,
                    Automation.deleted_at.is_(None)
                )
            )
            
            result = await db.execute(query)
            automations = result.scalars().all()
            
            logger.info(f"Found {len(automations)} automations for event {event_type}")
            
            for automation in automations:
                try:
                    # Check conditions
                    if await _check_conditions(automation, data, db):
                        # Execute actions
                        await _execute_actions(automation, data, db)
                        logger.info(f"Executed automation {automation.id}")
                    
                except Exception as e:
                    logger.error(f"Error executing automation {automation.id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {str(e)}")


async def _check_conditions(automation: Automation, data: Dict[str, Any], db) -> bool:
    """
    Check if all conditions are met.
    
    Args:
        automation: Automation instance
        data: Event data
        db: Database session
        
    Returns:
        True if all conditions met
    """
    # Get conditions
    query = select(AutomationCondition).where(
        AutomationCondition.automation_id == automation.id
    ).order_by(AutomationCondition.order)
    
    result = await db.execute(query)
    conditions = result.scalars().all()
    
    # If no conditions, allow execution
    if not conditions:
        return True
    
    # Check each condition (AND logic)
    for condition in conditions:
        config = condition.condition_config
        
        if condition.condition_type == "field_equals":
            field = config.get("field")
            value = config.get("value")
            if data.get(field) != value:
                return False
        
        elif condition.condition_type == "field_contains":
            field = config.get("field")
            value = config.get("value")
            field_value = data.get(field, "")
            if value not in str(field_value):
                return False
        
        elif condition.condition_type == "tag_has":
            tag = config.get("tag")
            tags = data.get("tags", [])
            if tag not in tags:
                return False
        
        # Add more condition types as needed
    
    return True


async def _execute_actions(automation: Automation, data: Dict[str, Any], db):
    """
    Execute automation actions.
    
    Args:
        automation: Automation instance
        data: Event data
        db: Database session
    """
    # Get actions
    query = select(AutomationAction).where(
        AutomationAction.automation_id == automation.id
    ).order_by(AutomationAction.order)
    
    result = await db.execute(query)
    actions = result.scalars().all()
    
    for action in actions:
        try:
            config = action.action_config
            
            if action.action_type == "send_email":
                celery_app.send_task(
                    "app.integrations.brevo.email.send_email",
                    args=[
                        None,  # No target ID for automation emails
                        data.get("email"),
                        config.get("subject"),
                        config.get("body")
                    ],
                    countdown=action.delay_seconds,
                    queue="dispatcher",
                )
            
            elif action.action_type == "send_sms":
                celery_app.send_task(
                    "app.integrations.brevo.sms.send_sms",
                    args=[None, data.get("phone"), config.get("body")],
                    countdown=action.delay_seconds,
                    queue="dispatcher",
                )
            
            elif action.action_type == "update_lead":
                lead_id = data.get("lead_id")
                if lead_id:
                    lead = await db.get(Lead, UUID(lead_id))
                    if lead:
                        field = config.get("field")
                        value = config.get("value")
                        setattr(lead, field, value)
                        await db.commit()
            
            # Add more action types as needed
            
            logger.info(f"Executed action {action.action_type} for automation {automation.id}")
            
        except Exception as e:
            logger.error(f"Error executing action {action.id}: {str(e)}")


@celery_app.task(name="app.workers.automation_engine.process_scheduled_automations")
def process_scheduled_automations():
    """Process scheduled automations (cron-based)."""
    import asyncio
    asyncio.run(_process_scheduled_automations_async())


async def _process_scheduled_automations_async():
    """Async implementation of scheduled automation processing."""
    async with AsyncSessionLocal() as db:
        # Find scheduled automations
        query = select(Automation).where(
            and_(
                Automation.trigger_type == "scheduled_time",
                Automation.enabled == True,
                Automation.deleted_at.is_(None)
            )
        )
        
        result = await db.execute(query)
        automations = result.scalars().all()
        
        for automation in automations:
            # Check if it's time to run (based on cron config)
            # This is a simplified version - in production, use a proper cron parser
            try:
                await _execute_actions(automation, {}, db)
            except Exception as e:
                logger.error(f"Error executing scheduled automation {automation.id}: {str(e)}")
