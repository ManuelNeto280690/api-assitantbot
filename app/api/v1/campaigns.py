"""Campaign API endpoints."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_tenant_context, TenantContext, Role, require_role
from app.models.campaign import Campaign, CampaignTarget, CampaignScheduleRule
from app.models.lead_list import LeadList, LeadListItem
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Schemas
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    channel: str  # sms, whatsapp, email, voice
    lead_list_id: UUID
    start_datetime: datetime
    timezone: str = "UTC"
    message_content: dict
    retry_strategy: dict = {
        "max_attempts": 3,
        "delays_minutes": [30, 120, 360],
        "retry_on": ["busy", "no_answer", "failed"]
    }


class ScheduleRuleCreate(BaseModel):
    start_hour: int = 9
    end_hour: int = 17
    days_allowed: List[int] = [0, 1, 2, 3, 4]  # Weekdays
    blackout_dates: List[str] = []


class CampaignResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    channel: str
    lead_list_id: UUID
    start_datetime: datetime
    timezone: str
    status: str
    total_targets: int
    completed_count: int
    failed_count: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    schedule_rule: Optional[ScheduleRuleCreate] = None,
    context: TenantContext = Depends(require_role(Role.OPERATOR)),
    db: AsyncSession = Depends(get_db)
):
    """Create new campaign."""
    # Verify lead list exists and belongs to tenant
    lead_list = await db.get(LeadList, campaign_data.lead_list_id)
    
    if not lead_list or lead_list.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead list not found"
        )
    
    # Create campaign
    campaign = Campaign(
        tenant_id=context.tenant_id,
        **campaign_data.model_dump()
    )
    
    db.add(campaign)
    await db.flush()
    
    # Create schedule rule if provided
    if schedule_rule:
        rule = CampaignScheduleRule(
            campaign_id=campaign.id,
            **schedule_rule.model_dump()
        )
        db.add(rule)
    
    # Initialize campaign targets
    await _initialize_campaign_targets(campaign, lead_list, db)
    
    await db.commit()
    await db.refresh(campaign)
    
    logger.info(f"Created campaign {campaign.id}", tenant_id=str(context.tenant_id))
    
    return campaign


async def _initialize_campaign_targets(campaign: Campaign, lead_list: LeadList, db: AsyncSession):
    """Initialize campaign targets from lead list."""
    # Get leads from list
    if lead_list.list_type == "static":
        # Static list - get from lead_list_items
        query = select(LeadListItem).where(LeadListItem.lead_list_id == lead_list.id)
        result = await db.execute(query)
        items = result.scalars().all()
        
        for item in items:
            target = CampaignTarget(
                campaign_id=campaign.id,
                lead_id=item.lead_id,
                status="pending",
                next_attempt_at=campaign.start_datetime
            )
            db.add(target)
        
        campaign.total_targets = len(items)
    
    else:
        # Dynamic list - evaluate filters
        # This is simplified - in production, implement proper filter evaluation
        from app.models.lead import Lead
        
        query = select(Lead).where(
            and_(
                Lead.tenant_id == campaign.tenant_id,
                Lead.deleted_at.is_(None)
            )
        )
        
        result = await db.execute(query)
        leads = result.scalars().all()
        
        for lead in leads:
            target = CampaignTarget(
                campaign_id=campaign.id,
                lead_id=lead.id,
                status="pending",
                next_attempt_at=campaign.start_datetime
            )
            db.add(target)
        
        campaign.total_targets = len(leads)


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    status_filter: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """List campaigns for current tenant."""
    query = select(Campaign).where(
        and_(
            Campaign.tenant_id == context.tenant_id,
            Campaign.deleted_at.is_(None)
        )
    )
    
    if status_filter:
        query = query.where(Campaign.status == status_filter)
    
    if channel:
        query = query.where(Campaign.channel == channel)
    
    query = query.limit(limit).offset(offset).order_by(Campaign.created_at.desc())
    
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Get campaign by ID."""
    campaign = await db.get(Campaign, campaign_id)
    
    if not campaign or campaign.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: UUID,
    context: TenantContext = Depends(require_role(Role.OPERATOR)),
    db: AsyncSession = Depends(get_db)
):
    """Start campaign execution."""
    campaign = await db.get(Campaign, campaign_id)
    
    if not campaign or campaign.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status not in ["draft", "paused"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start campaign in {campaign.status} status"
        )
    
    campaign.status = "running"
    await db.commit()
    
    logger.info(f"Started campaign {campaign.id}", tenant_id=str(context.tenant_id))
    
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    context: TenantContext = Depends(require_role(Role.OPERATOR)),
    db: AsyncSession = Depends(get_db)
):
    """Pause campaign execution."""
    campaign = await db.get(Campaign, campaign_id)
    
    if not campaign or campaign.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is not running"
        )
    
    campaign.status = "paused"
    await db.commit()
    
    logger.info(f"Paused campaign {campaign.id}", tenant_id=str(context.tenant_id))
    
    return campaign
