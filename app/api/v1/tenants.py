"""Tenant API endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_tenant_context, TenantContext, Role, require_role
from app.models.tenant import Tenant
from app.models.membership import Membership
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Schemas
class TenantCreate(BaseModel):
    name: str
    slug: str
    plan: str = "free"


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    current_usage: dict
    usage_limits: dict
    
    class Config:
        from_attributes = True


class MembershipCreate(BaseModel):
    user_id: str
    role: str = "viewer"
    email: str
    full_name: str | None = None


class MembershipResponse(BaseModel):
    id: UUID
    user_id: str
    tenant_id: UUID
    role: str
    email: str
    full_name: str | None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    context: TenantContext = Depends(require_role(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Create new tenant (super admin only)."""
    # Check if slug already exists
    query = select(Tenant).where(Tenant.slug == tenant_data.slug)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this slug already exists"
        )
    
    # Create tenant
    tenant = Tenant(
        name=tenant_data.name,
        slug=tenant_data.slug,
        plan=tenant_data.plan
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    logger.info(f"Created tenant {tenant.id}", tenant_id=str(tenant.id))
    
    return tenant


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Get current tenant details."""
    tenant = await db.get(Tenant, context.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant


@router.get("/current/memberships", response_model=List[MembershipResponse])
async def list_memberships(
    context: TenantContext = Depends(require_role(Role.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """List all memberships for current tenant."""
    query = select(Membership).where(
        Membership.tenant_id == context.tenant_id,
        Membership.deleted_at.is_(None)
    )
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    return memberships


@router.post("/current/memberships", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def create_membership(
    membership_data: MembershipCreate,
    context: TenantContext = Depends(require_role(Role.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Add user to current tenant."""
    # Check if membership already exists
    query = select(Membership).where(
        Membership.tenant_id == context.tenant_id,
        Membership.user_id == membership_data.user_id,
        Membership.deleted_at.is_(None)
    )
    
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has membership in this tenant"
        )
    
    # Create membership
    membership = Membership(
        tenant_id=context.tenant_id,
        user_id=membership_data.user_id,
        role=membership_data.role,
        email=membership_data.email,
        full_name=membership_data.full_name
    )
    
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    
    logger.info(f"Created membership {membership.id}", tenant_id=str(context.tenant_id))
    
    return membership
