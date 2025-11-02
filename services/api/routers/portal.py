"""
Customer Self-Service Portal Router
Handles onboarding, account management, and team collaboration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import logging

from portal.onboarding import OnboardingManager, OnboardingStep
from portal.account_management import AccountManager, TeamMemberInvite, AccountSettings
from middleware import get_current_tenant, get_current_user_id
from deps import get_postgres

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portal", tags=["portal", "onboarding", "account"])


# ============================================================================
# Onboarding Endpoints
# ============================================================================

@router.get("/onboarding")
async def get_onboarding_status(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📊 Get onboarding progress
    """
    try:
        manager = OnboardingManager(db)
        
        status = await manager.get_onboarding_status(tenant_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get onboarding status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get onboarding status"
        )


@router.post("/onboarding/start")
async def start_onboarding(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    🚀 Start onboarding wizard
    """
    try:
        manager = OnboardingManager(db)
        
        steps = await manager.start_onboarding(tenant_id)
        
        return {
            "success": True,
            "steps": [step.dict() for step in steps]
        }
        
    except Exception as e:
        logger.error(f"Failed to start onboarding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start onboarding"
        )


@router.post("/onboarding/{step_id}/complete")
async def complete_onboarding_step(
    step_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    ✅ Mark onboarding step as complete
    """
    try:
        manager = OnboardingManager(db)
        
        result = await manager.complete_step(tenant_id, step_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to complete step: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete step"
        )


@router.get("/onboarding/checklist")
async def get_onboarding_checklist(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📝 Get personalized onboarding checklist
    """
    try:
        manager = OnboardingManager(db)
        
        checklist = await manager.generate_onboarding_checklist(tenant_id)
        
        return {"checklist": checklist}
        
    except Exception as e:
        logger.error(f"Failed to get checklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get checklist"
        )


# ============================================================================
# Account Management Endpoints
# ============================================================================

@router.get("/account")
async def get_account_info(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📊 Get account information
    
    Returns account details with usage statistics
    """
    try:
        manager = AccountManager(db)
        
        account_info = await manager.get_account_info(tenant_id)
        
        return {"account": account_info}
        
    except Exception as e:
        logger.error(f"Failed to get account info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get account information"
        )


@router.get("/account/settings")
async def get_settings(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    ⚙️ Get account settings
    """
    try:
        manager = AccountManager(db)
        
        settings = await manager.get_account_settings(tenant_id)
        
        return {"settings": settings.dict()}
        
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get settings"
        )


@router.put("/account/settings")
async def update_settings(
    settings: AccountSettings,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    ✏️ Update account settings
    """
    try:
        manager = AccountManager(db)
        
        updated = await manager.update_account_settings(tenant_id, settings)
        
        return {
            "success": True,
            "settings": updated
        }
        
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )


# ============================================================================
# Team Management Endpoints
# ============================================================================

@router.get("/team")
async def get_team_members(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    👥 Get all team members
    """
    try:
        manager = AccountManager(db)
        
        members = await manager.get_team_members(tenant_id)
        
        return {"team_members": members}
        
    except Exception as e:
        logger.error(f"Failed to get team members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team members"
        )


@router.post("/team/invite")
async def invite_team_member(
    invite: TeamMemberInvite,
    tenant_id: str = Depends(get_current_tenant),
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    ✉️ Invite team member
    
    Sends invitation email to new team member
    """
    try:
        manager = AccountManager(db)
        
        result = await manager.invite_team_member(tenant_id, invite, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to invite team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite team member"
        )


@router.delete("/team/{member_id}")
async def remove_team_member(
    member_id: int,
    tenant_id: str = Depends(get_current_tenant),
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    🗑️ Remove team member
    """
    try:
        manager = AccountManager(db)
        
        result = await manager.remove_team_member(tenant_id, member_id, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to remove team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove team member"
        )


class UpdateRoleRequest(BaseModel):
    new_role: str


@router.patch("/team/{member_id}/role")
async def update_team_member_role(
    member_id: int,
    request: UpdateRoleRequest,
    tenant_id: str = Depends(get_current_tenant),
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    ✏️ Update team member role
    """
    try:
        manager = AccountManager(db)
        
        result = await manager.update_team_member_role(
            tenant_id, member_id, request.new_role, user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to update role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )


# ============================================================================
# Activity Log
# ============================================================================

@router.get("/activity")
async def get_activity_log(
    limit: int = 100,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📋 Get account activity log
    
    Returns recent account activities for audit
    """
    try:
        manager = AccountManager(db)
        
        activities = await manager.get_activity_log(tenant_id, limit=limit)
        
        return {"activities": activities}
        
    except Exception as e:
        logger.error(f"Failed to get activity log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity log"
        )

