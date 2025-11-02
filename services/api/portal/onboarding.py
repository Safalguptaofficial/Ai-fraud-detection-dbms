"""
Customer Onboarding
Handles self-service signup, onboarding wizard, and initial setup
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)


class OnboardingStep(BaseModel):
    """Individual onboarding step"""
    step_id: str
    step_name: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    data: Optional[Dict] = None


class OnboardingManager:
    """Manages customer onboarding flow"""
    
    # Define onboarding steps
    ONBOARDING_STEPS = [
        {"step_id": "create_account", "step_name": "Create Account"},
        {"step_id": "verify_email", "step_name": "Verify Email"},
        {"step_id": "choose_plan", "step_name": "Choose Subscription Plan"},
        {"step_id": "setup_payment", "step_name": "Setup Payment Method"},
        {"step_id": "configure_basics", "step_name": "Basic Configuration"},
        {"step_id": "upload_data", "step_name": "Upload Initial Data"},
        {"step_id": "invite_team", "step_name": "Invite Team Members"},
        {"step_id": "complete", "step_name": "Complete Onboarding"}
    ]
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def start_onboarding(self, tenant_id: str) -> List[OnboardingStep]:
        """
        Initialize onboarding for a new tenant
        
        Returns: List of onboarding steps
        """
        cursor = self.db.cursor()
        
        try:
            # Create onboarding record
            cursor.execute("""
                INSERT INTO tenant_onboarding (
                    tenant_id, current_step, steps_data, started_at
                ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (tenant_id) DO NOTHING
            """, (
                tenant_id,
                'create_account',
                {'steps': [step for step in self.ONBOARDING_STEPS]}
            ))
            
            self.db.commit()
            
            logger.info(f"Started onboarding for tenant {tenant_id}")
            
            return [OnboardingStep(**step) for step in self.ONBOARDING_STEPS]
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start onboarding: {e}")
            raise
        finally:
            cursor.close()
    
    async def get_onboarding_status(self, tenant_id: str) -> Dict:
        """
        Get current onboarding status
        
        Returns: Onboarding progress
        """
        cursor = self.db.cursor()
        
        try:
            cursor.execute("""
                SELECT current_step, steps_data, started_at, completed_at,
                       (SELECT COUNT(*) FROM jsonb_array_elements(steps_data->'steps') WHERE (value->>'completed')::boolean = true) as completed_steps
                FROM tenant_onboarding
                WHERE tenant_id = %s
            """, (tenant_id,))
            
            result = cursor.fetchone()
            
            if not result:
                # No onboarding started yet
                return {
                    "status": "not_started",
                    "current_step": None,
                    "progress": 0,
                    "steps": []
                }
            
            current_step, steps_data, started_at, completed_at, completed_count = result
            total_steps = len(self.ONBOARDING_STEPS)
            progress = (completed_count / total_steps) * 100 if total_steps > 0 else 0
            
            return {
                "status": "completed" if completed_at else "in_progress",
                "current_step": current_step,
                "progress": round(progress, 2),
                "started_at": started_at,
                "completed_at": completed_at,
                "steps": steps_data.get('steps', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get onboarding status: {e}")
            raise
        finally:
            cursor.close()
    
    async def complete_step(
        self,
        tenant_id: str,
        step_id: str,
        step_data: Optional[Dict] = None
    ) -> Dict:
        """
        Mark an onboarding step as complete
        
        Args:
            tenant_id: Tenant ID
            step_id: Step identifier
            step_data: Additional data collected in this step
        
        Returns: Updated onboarding status
        """
        cursor = self.db.cursor()
        
        try:
            # Update step as completed
            cursor.execute("""
                UPDATE tenant_onboarding
                SET steps_data = jsonb_set(
                    steps_data,
                    '{steps}',
                    (
                        SELECT jsonb_agg(
                            CASE
                                WHEN elem->>'step_id' = %s THEN
                                    jsonb_set(
                                        jsonb_set(elem, '{completed}', 'true'::jsonb),
                                        '{completed_at}', to_jsonb(CURRENT_TIMESTAMP::text)
                                    )
                                ELSE elem
                            END
                        )
                        FROM jsonb_array_elements(steps_data->'steps') elem
                    )
                ),
                current_step = %s
                WHERE tenant_id = %s
                RETURNING current_step
            """, (step_id, step_id, tenant_id))
            
            # Check if all steps are complete
            cursor.execute("""
                SELECT COUNT(*) = 0
                FROM jsonb_array_elements(steps_data->'steps') step
                WHERE (step->>'completed')::boolean = false
                FROM tenant_onboarding
                WHERE tenant_id = %s
            """, (tenant_id,))
            
            all_complete = cursor.fetchone()[0]
            
            if all_complete:
                # Mark onboarding as complete
                cursor.execute("""
                    UPDATE tenant_onboarding
                    SET completed_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = %s
                """, (tenant_id,))
            
            self.db.commit()
            
            logger.info(f"Completed step {step_id} for tenant {tenant_id}")
            
            return await self.get_onboarding_status(tenant_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to complete step: {e}")
            raise
        finally:
            cursor.close()
    
    async def send_welcome_email(self, tenant_id: str, admin_email: str):
        """
        Send welcome email to new customer
        
        TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        """
        logger.info(f"Sending welcome email to {admin_email} for tenant {tenant_id}")
        
        email_content = f"""
        Welcome to FraudGuard!
        
        Your account has been created successfully.
        
        Next steps:
        1. Verify your email
        2. Choose a subscription plan
        3. Setup payment method
        4. Upload your transaction data
        5. Invite your team members
        
        Login at: https://app.fraudguard.com
        
        Need help? Contact support@fraudguard.com
        """
        
        # TODO: Send actual email
        logger.info(f"Welcome email content:\n{email_content}")
    
    async def generate_onboarding_checklist(self, tenant_id: str) -> List[Dict]:
        """
        Generate personalized onboarding checklist
        
        Returns: List of tasks with completion status
        """
        status = await self.get_onboarding_status(tenant_id)
        
        checklist = []
        
        for step in status['steps']:
            task = {
                "task": step['step_name'],
                "completed": step.get('completed', False),
                "description": self._get_step_description(step['step_id']),
                "cta": self._get_step_cta(step['step_id'])
            }
            checklist.append(task)
        
        return checklist
    
    def _get_step_description(self, step_id: str) -> str:
        """Get description for a step"""
        descriptions = {
            "create_account": "Sign up with your business email",
            "verify_email": "Click the link in your email to verify",
            "choose_plan": "Select a plan that fits your needs",
            "setup_payment": "Add your payment method",
            "configure_basics": "Set up your fraud detection rules",
            "upload_data": "Upload your historical transaction data",
            "invite_team": "Add team members to your account",
            "complete": "You're all set!"
        }
        return descriptions.get(step_id, "")
    
    def _get_step_cta(self, step_id: str) -> str:
        """Get call-to-action for a step"""
        ctas = {
            "create_account": "/signup",
            "verify_email": "/verify",
            "choose_plan": "/plans",
            "setup_payment": "/billing/payment",
            "configure_basics": "/settings/rules",
            "upload_data": "/data/upload",
            "invite_team": "/team/invite",
            "complete": "/dashboard"
        }
        return ctas.get(step_id, "/")

