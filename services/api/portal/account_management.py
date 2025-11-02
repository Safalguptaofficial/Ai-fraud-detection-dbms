"""
Account Management
Self-service account settings, team management, and preferences
"""
from typing import Optional, Dict, List
from datetime import datetime
import logging
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)


class TeamMemberInvite(BaseModel):
    """Team member invitation"""
    email: EmailStr
    role: str = "ANALYST"
    message: Optional[str] = None


class AccountSettings(BaseModel):
    """Account settings configuration"""
    notifications_enabled: bool = True
    email_alerts: bool = True
    sms_alerts: bool = False
    alert_threshold: float = 0.8  # Fraud score threshold
    daily_summary: bool = True
    timezone: str = "UTC"
    language: str = "en"


class AccountManager:
    """Manages account settings and team members"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_account_info(self, tenant_id: str) -> Dict:
        """
        Get account information
        
        Returns: Account details with usage statistics
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    t.tenant_id,
                    t.organization_name,
                    t.subdomain,
                    t.admin_email,
                    t.plan,
                    t.status,
                    t.created_at,
                    ts.stripe_customer_id,
                    ts.status as subscription_status,
                    ts.current_period_end,
                    tu.transaction_count as transactions_this_month,
                    t.max_transactions_per_month,
                    (SELECT COUNT(*) FROM tenant_users WHERE tenant_id = t.tenant_id AND is_active = true) as active_users,
                    t.max_users
                FROM tenants t
                LEFT JOIN tenant_subscriptions ts ON t.tenant_id = ts.tenant_id
                LEFT JOIN tenant_usage tu ON t.tenant_id = tu.tenant_id 
                    AND tu.period_start = DATE_TRUNC('month', CURRENT_DATE)
                WHERE t.tenant_id = %s
            """, (tenant_id,))
            
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Tenant {tenant_id} not found")
            
            columns = [desc[0] for desc in cursor.description]
            account_data = dict(zip(columns, result))
            
            # Calculate usage percentage
            if account_data['max_transactions_per_month']:
                usage_pct = (account_data['transactions_this_month'] / account_data['max_transactions_per_month']) * 100
                account_data['usage_percentage'] = round(usage_pct, 2)
            else:
                account_data['usage_percentage'] = 0
            
            return account_data
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
        finally:
            cursor.close()
    
    async def update_account_settings(
        self,
        tenant_id: str,
        settings: AccountSettings
    ) -> Dict:
        """
        Update account settings
        
        Returns: Updated settings
        """
        cursor = self.db.cursor()
        
        try:
            # Store settings in tenant_settings table (create if needed)
            cursor.execute("""
                INSERT INTO tenant_settings (tenant_id, settings, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (tenant_id)
                DO UPDATE SET settings = %s, updated_at = CURRENT_TIMESTAMP
                RETURNING settings
            """, (tenant_id, settings.dict(), settings.dict()))
            
            updated_settings = cursor.fetchone()[0]
            self.db.commit()
            
            logger.info(f"Updated settings for tenant {tenant_id}")
            
            return updated_settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update settings: {e}")
            raise
        finally:
            cursor.close()
    
    async def get_account_settings(self, tenant_id: str) -> AccountSettings:
        """
        Get account settings
        
        Returns: Account settings
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT settings
                FROM tenant_settings
                WHERE tenant_id = %s
            """, (tenant_id,))
            
            result = cursor.fetchone()
            
            if result:
                return AccountSettings(**result[0])
            else:
                # Return default settings
                return AccountSettings()
            
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            return AccountSettings()
        finally:
            cursor.close()
    
    async def invite_team_member(
        self,
        tenant_id: str,
        invite: TeamMemberInvite,
        invited_by: int
    ) -> Dict:
        """
        Invite a team member
        
        Returns: Invitation details
        """
        cursor = self.db.cursor()
        
        try:
            # Check if user already exists
            cursor.execute("""
                SELECT id FROM tenant_users
                WHERE tenant_id = %s AND email = %s
            """, (tenant_id, invite.email))
            
            existing = cursor.fetchone()
            
            if existing:
                return {
                    "success": False,
                    "error": "User already exists in this tenant"
                }
            
            # Create invitation
            import secrets
            invite_token = secrets.token_urlsafe(32)
            
            cursor.execute("""
                INSERT INTO team_invitations (
                    tenant_id, email, role, invited_by,
                    invite_token, expires_at
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '7 days')
                RETURNING id, invite_token
            """, (tenant_id, invite.email, invite.role, invited_by, invite_token))
            
            invite_id, token = cursor.fetchone()
            self.db.commit()
            
            # TODO: Send invitation email
            invite_link = f"https://app.fraudguard.com/accept-invite?token={token}"
            
            logger.info(f"Created invitation {invite_id} for {invite.email}")
            
            return {
                "success": True,
                "invitation_id": invite_id,
                "invite_link": invite_link,
                "expires_in_days": 7
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create invitation: {e}")
            raise
        finally:
            cursor.close()
    
    async def get_team_members(self, tenant_id: str) -> List[Dict]:
        """
        Get all team members
        
        Returns: List of team members
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    id, email, full_name, role, is_active,
                    last_login, created_at
                FROM tenant_users
                WHERE tenant_id = %s
                ORDER BY created_at DESC
            """, (tenant_id,))
            
            columns = [desc[0] for desc in cursor.description]
            members = []
            
            for row in cursor.fetchall():
                member = dict(zip(columns, row))
                members.append(member)
            
            return members
            
        except Exception as e:
            logger.error(f"Failed to get team members: {e}")
            raise
        finally:
            cursor.close()
    
    async def remove_team_member(
        self,
        tenant_id: str,
        user_id: int,
        removed_by: int
    ) -> Dict:
        """
        Remove a team member
        
        Returns: Success status
        """
        cursor = self.db.cursor()
        
        try:
            # Check if user is admin (can't remove last admin)
            cursor.execute("""
                SELECT role FROM tenant_users
                WHERE id = %s AND tenant_id = %s
            """, (user_id, tenant_id))
            
            result = cursor.fetchone()
            
            if not result:
                return {"success": False, "error": "User not found"}
            
            user_role = result[0]
            
            if user_role == 'ADMIN':
                # Check if this is the last admin
                cursor.execute("""
                    SELECT COUNT(*) FROM tenant_users
                    WHERE tenant_id = %s AND role = 'ADMIN' AND is_active = true
                """, (tenant_id,))
                
                admin_count = cursor.fetchone()[0]
                
                if admin_count <= 1:
                    return {
                        "success": False,
                        "error": "Cannot remove the last admin. Please promote another user first."
                    }
            
            # Soft delete (deactivate) user
            cursor.execute("""
                UPDATE tenant_users
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND tenant_id = %s
            """, (user_id, tenant_id))
            
            # Log the action
            cursor.execute("""
                INSERT INTO audit_logs (
                    tenant_id, user_id, action, resource_type, resource_id, severity
                ) VALUES (%s, %s, 'REMOVE_TEAM_MEMBER', 'USER', %s, 'INFO')
            """, (tenant_id, removed_by, str(user_id)))
            
            self.db.commit()
            
            logger.info(f"Removed user {user_id} from tenant {tenant_id}")
            
            return {"success": True}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove team member: {e}")
            raise
        finally:
            cursor.close()
    
    async def update_team_member_role(
        self,
        tenant_id: str,
        user_id: int,
        new_role: str,
        updated_by: int
    ) -> Dict:
        """
        Update team member's role
        
        Returns: Success status
        """
        cursor = self.db.cursor()
        
        try:
            valid_roles = ['ADMIN', 'MANAGER', 'ANALYST', 'VIEWER']
            
            if new_role not in valid_roles:
                return {"success": False, "error": f"Invalid role. Must be one of: {valid_roles}"}
            
            cursor.execute("""
                UPDATE tenant_users
                SET role = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND tenant_id = %s
                RETURNING role
            """, (new_role, user_id, tenant_id))
            
            result = cursor.fetchone()
            
            if not result:
                return {"success": False, "error": "User not found"}
            
            # Log the action
            cursor.execute("""
                INSERT INTO audit_logs (
                    tenant_id, user_id, action, resource_type, resource_id,
                    new_value, severity
                ) VALUES (%s, %s, 'UPDATE_USER_ROLE', 'USER', %s, %s, 'INFO')
            """, (tenant_id, updated_by, str(user_id), {"new_role": new_role}))
            
            self.db.commit()
            
            logger.info(f"Updated role for user {user_id} to {new_role}")
            
            return {"success": True, "new_role": result[0]}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update role: {e}")
            raise
        finally:
            cursor.close()
    
    async def get_activity_log(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent account activity
        
        Returns: List of recent activities
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    al.id,
                    al.action,
                    al.resource_type,
                    al.resource_id,
                    al.timestamp,
                    tu.email as user_email,
                    tu.full_name as user_name
                FROM audit_logs al
                LEFT JOIN tenant_users tu ON al.user_id = tu.id
                WHERE al.tenant_id = %s
                ORDER BY al.timestamp DESC
                LIMIT %s
            """, (tenant_id, limit))
            
            columns = [desc[0] for desc in cursor.description]
            activities = []
            
            for row in cursor.fetchall():
                activity = dict(zip(columns, row))
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get activity log: {e}")
            raise
        finally:
            cursor.close()

