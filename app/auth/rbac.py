"""Role-based access control (RBAC) system."""
from enum import Enum
from typing import List
from fastapi import HTTPException, status


class Role(str, Enum):
    """User roles in the system."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = [
    Role.VIEWER,
    Role.OPERATOR,
    Role.TENANT_ADMIN,
    Role.SUPER_ADMIN,
]


class Permission(str, Enum):
    """System permissions."""
    # Tenant management
    TENANT_CREATE = "tenant:create"
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Lead management
    LEAD_CREATE = "lead:create"
    LEAD_READ = "lead:read"
    LEAD_UPDATE = "lead:update"
    LEAD_DELETE = "lead:delete"
    
    # Campaign management
    CAMPAIGN_CREATE = "campaign:create"
    CAMPAIGN_READ = "campaign:read"
    CAMPAIGN_UPDATE = "campaign:update"
    CAMPAIGN_DELETE = "campaign:delete"
    CAMPAIGN_EXECUTE = "campaign:execute"
    
    # Automation management
    AUTOMATION_CREATE = "automation:create"
    AUTOMATION_READ = "automation:read"
    AUTOMATION_UPDATE = "automation:update"
    AUTOMATION_DELETE = "automation:delete"
    
    # Settings
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [p for p in Permission],  # All permissions
    Role.TENANT_ADMIN: [
        Permission.TENANT_READ,
        Permission.TENANT_UPDATE,
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.LEAD_CREATE,
        Permission.LEAD_READ,
        Permission.LEAD_UPDATE,
        Permission.LEAD_DELETE,
        Permission.CAMPAIGN_CREATE,
        Permission.CAMPAIGN_READ,
        Permission.CAMPAIGN_UPDATE,
        Permission.CAMPAIGN_DELETE,
        Permission.CAMPAIGN_EXECUTE,
        Permission.AUTOMATION_CREATE,
        Permission.AUTOMATION_READ,
        Permission.AUTOMATION_UPDATE,
        Permission.AUTOMATION_DELETE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_UPDATE,
    ],
    Role.OPERATOR: [
        Permission.TENANT_READ,
        Permission.USER_READ,
        Permission.LEAD_CREATE,
        Permission.LEAD_READ,
        Permission.LEAD_UPDATE,
        Permission.CAMPAIGN_CREATE,
        Permission.CAMPAIGN_READ,
        Permission.CAMPAIGN_UPDATE,
        Permission.CAMPAIGN_EXECUTE,
        Permission.AUTOMATION_READ,
        Permission.SETTINGS_READ,
    ],
    Role.VIEWER: [
        Permission.TENANT_READ,
        Permission.USER_READ,
        Permission.LEAD_READ,
        Permission.CAMPAIGN_READ,
        Permission.AUTOMATION_READ,
        Permission.SETTINGS_READ,
    ],
}


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Check if role has specific permission.
    
    Args:
        role: User role
        permission: Required permission
        
    Returns:
        True if role has permission
    """
    return permission in ROLE_PERMISSIONS.get(role, [])


def has_role(user_role: Role, required_role: Role) -> bool:
    """
    Check if user role meets or exceeds required role.
    
    Args:
        user_role: User's current role
        required_role: Required role level
        
    Returns:
        True if user role is sufficient
    """
    try:
        user_level = ROLE_HIERARCHY.index(user_role)
        required_level = ROLE_HIERARCHY.index(required_role)
        return user_level >= required_level
    except ValueError:
        return False


def require_permission(user_role: Role, permission: Permission):
    """
    Raise exception if user doesn't have required permission.
    
    Args:
        user_role: User's role
        permission: Required permission
        
    Raises:
        HTTPException: If permission denied
    """
    if not has_permission(user_role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value} required",
        )


def require_role(user_role: Role, required_role: Role):
    """
    Raise exception if user doesn't have required role level.
    
    Args:
        user_role: User's role
        required_role: Required role level
        
    Raises:
        HTTPException: If role insufficient
    """
    if not has_role(user_role, required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role: {required_role.value} required",
        )
