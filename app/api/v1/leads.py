"""Lead API endpoints."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.auth import get_tenant_context, TenantContext, Role, require_role
from app.models.lead import Lead
from app.workers.event_bus import event_bus
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Schemas
class LeadCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    timezone: str = "UTC"
    status: str = "new"
    custom_fields: dict = {}
    tags: List[str] = []
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None
    custom_fields: Optional[dict] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: Optional[str]
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    timezone: str
    status: str
    custom_fields: dict
    tags: List[str]
    source: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    context: TenantContext = Depends(require_role(Role.OPERATOR)),
    db: AsyncSession = Depends(get_db)
):
    """Create new lead."""
    # Validate at least email or phone provided
    if not lead_data.email and not lead_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided"
        )
    
    # Create lead
    lead = Lead(
        tenant_id=context.tenant_id,
        **lead_data.model_dump()
    )
    
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    
    logger.info(f"Created lead {lead.id}", tenant_id=str(context.tenant_id))
    
    # Publish event
    event_bus.publish(
        "lead_created",
        str(context.tenant_id),
        {
            "lead_id": str(lead.id),
            "email": lead.email,
            "phone": lead.phone,
            "status": lead.status,
            "tags": lead.tags
        }
    )
    
    return lead


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    status_filter: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """List leads for current tenant."""
    query = select(Lead).where(
        and_(
            Lead.tenant_id == context.tenant_id,
            Lead.deleted_at.is_(None)
        )
    )
    
    if status_filter:
        query = query.where(Lead.status == status_filter)
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    # Filter by tag if provided (JSONB filtering)
    if tag:
        leads = [lead for lead in leads if tag in lead.tags]
    
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Get lead by ID."""
    lead = await db.get(Lead, lead_id)
    
    if not lead or lead.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    context: TenantContext = Depends(require_role(Role.OPERATOR)),
    db: AsyncSession = Depends(get_db)
):
    """Update lead."""
    lead = await db.get(Lead, lead_id)
    
    if not lead or lead.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Update fields
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    await db.commit()
    await db.refresh(lead)
    
    logger.info(f"Updated lead {lead.id}", tenant_id=str(context.tenant_id))
    
    # Publish event
    event_bus.publish(
        "lead_updated",
        str(context.tenant_id),
        {
            "lead_id": str(lead.id),
            "changes": update_data
        }
    )
    
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    context: TenantContext = Depends(require_role(Role.OPERATOR)),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete lead."""
    lead = await db.get(Lead, lead_id)
    
    if not lead or lead.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    lead.soft_delete()
    await db.commit()
    
    logger.info(f"Deleted lead {lead.id}", tenant_id=str(context.tenant_id))
    
    return None
