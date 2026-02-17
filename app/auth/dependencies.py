"""FastAPI dependencies for authentication and authorization."""
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.jwt import jwt_validator
from app.auth.rbac import Role, require_role as check_role
from app.models.membership import Membership


security = HTTPBearer()


class TenantContext:
    """Tenant context for request."""
    
    def __init__(self, user_id: str, tenant_id: UUID, role: Role, membership_id: UUID):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.membership_id = membership_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID from Supabase
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    user_id = jwt_validator.extract_user_id(token)
    return user_id


async def get_tenant_context(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: Optional[str] = None,
) -> TenantContext:
    """
    Get tenant context for current user.
    
    CRITICAL: This function determines tenant_id from the user's membership.
    NEVER trust tenant_id from frontend - it's only used as a hint for
    users with multiple memberships.
    
    Args:
        user_id: Current user ID
        db: Database session
        tenant_id: Optional tenant ID hint (not trusted)
        
    Returns:
        Tenant context with validated tenant_id
        
    Raises:
        HTTPException: If user has no membership or invalid tenant
    """
    from sqlalchemy import select
    
    # Query user's memberships
    query = select(Membership).where(
        Membership.user_id == user_id,
        Membership.deleted_at.is_(None)
    )
    
    # If tenant_id hint provided, try to use it
    if tenant_id:
        query = query.where(Membership.tenant_id == UUID(tenant_id))
    
    result = await db.execute(query)
    membership = result.scalar_one_or_none()
    
    if not membership:
        # If no membership found with hint, get first active membership
        query = select(Membership).where(
            Membership.user_id == user_id,
            Membership.deleted_at.is_(None)
        ).limit(1)
        
        result = await db.execute(query)
        membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active tenant membership",
        )
    
    return TenantContext(
        user_id=user_id,
        tenant_id=membership.tenant_id,
        role=Role(membership.role),
        membership_id=membership.id,
    )


def require_role(required_role: Role):
    """
    Dependency to require specific role level.
    
    Args:
        required_role: Minimum required role
        
    Returns:
        Dependency function
    """
    async def role_checker(
        context: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        check_role(context.role, required_role)
        return context
    
    return role_checker
