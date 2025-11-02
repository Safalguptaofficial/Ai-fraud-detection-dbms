"""
Billing & Subscription Router
Handles Stripe subscriptions, invoices, and usage metering
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List
import logging

from billing.stripe_billing import StripeBillingManager, SubscriptionPlan
from billing.usage_metering import UsageMetering
from middleware import get_current_tenant, get_current_user_id
from deps import get_postgres, get_redis
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing", "subscriptions"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SubscriptionCreateRequest(BaseModel):
    plan: SubscriptionPlan
    payment_method_id: Optional[str] = None


class SubscriptionUpdateRequest(BaseModel):
    new_plan: SubscriptionPlan


# ============================================================================
# Subscription Endpoints
# ============================================================================

@router.post("/subscriptions")
async def create_subscription(
    request: SubscriptionCreateRequest,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    💳 Create new subscription
    
    Creates Stripe subscription for the tenant
    """
    try:
        billing = StripeBillingManager(api_key=settings.stripe_api_key)
        
        # Get tenant info
        cursor = db.cursor()
        cursor.execute(
            "SELECT organization_name, admin_email FROM tenants WHERE tenant_id = %s",
            (tenant_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        org_name, admin_email = result
        
        # Create or get Stripe customer
        cursor.execute(
            "SELECT stripe_customer_id FROM tenant_subscriptions WHERE tenant_id = %s",
            (tenant_id,)
        )
        existing = cursor.fetchone()
        
        if existing and existing[0]:
            customer_id = existing[0]
        else:
            # Create new customer
            customer_id = await billing.create_customer(
                tenant_id=tenant_id,
                email=admin_email,
                name=org_name
            )
        
        # Create subscription
        subscription = await billing.create_subscription(
            customer_id=customer_id,
            plan=request.plan,
            payment_method_id=request.payment_method_id
        )
        
        # Store in database
        cursor.execute("""
            INSERT INTO tenant_subscriptions (
                tenant_id, stripe_customer_id, stripe_subscription_id,
                plan, status, current_period_start, current_period_end
            ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 month')
            ON CONFLICT (tenant_id)
            DO UPDATE SET
                stripe_subscription_id = %s,
                plan = %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
        """, (
            tenant_id, customer_id, subscription['subscription_id'],
            request.plan.value, subscription['status'],
            subscription['subscription_id'], request.plan.value, subscription['status']
        ))
        
        # Update tenant plan
        cursor.execute(
            "UPDATE tenants SET plan = %s WHERE tenant_id = %s",
            (request.plan.value, tenant_id)
        )
        
        db.commit()
        cursor.close()
        
        logger.info(f"Created subscription for tenant {tenant_id}")
        
        return {
            "success": True,
            "subscription": subscription
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription creation failed: {str(e)}"
        )


@router.get("/subscriptions")
async def get_subscription(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📊 Get current subscription
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                stripe_customer_id, stripe_subscription_id,
                plan, status, current_period_start, current_period_end,
                trial_end, cancel_at, canceled_at
            FROM tenant_subscriptions
            WHERE tenant_id = %s
        """, (tenant_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return {"subscription": None, "message": "No active subscription"}
        
        columns = ['stripe_customer_id', 'stripe_subscription_id', 'plan', 'status',
                   'current_period_start', 'current_period_end', 'trial_end',
                   'cancel_at', 'canceled_at']
        
        subscription = dict(zip(columns, result))
        
        return {"subscription": subscription}
        
    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.patch("/subscriptions")
async def update_subscription(
    request: SubscriptionUpdateRequest,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    ✏️ Update subscription plan
    """
    try:
        billing = StripeBillingManager(api_key=settings.stripe_api_key)
        
        # Get current subscription
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_subscription_id FROM tenant_subscriptions WHERE tenant_id = %s",
            (tenant_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="No active subscription")
        
        subscription_id = result[0]
        
        # Update subscription
        updated = await billing.update_subscription(
            subscription_id=subscription_id,
            new_plan=request.new_plan
        )
        
        # Update database
        cursor.execute("""
            UPDATE tenant_subscriptions
            SET plan = %s, status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE tenant_id = %s
        """, (request.new_plan.value, updated['status'], tenant_id))
        
        cursor.execute(
            "UPDATE tenants SET plan = %s WHERE tenant_id = %s",
            (request.new_plan.value, tenant_id)
        )
        
        db.commit()
        cursor.close()
        
        logger.info(f"Updated subscription for tenant {tenant_id} to {request.new_plan}")
        
        return {
            "success": True,
            "subscription": updated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription update failed: {str(e)}"
        )


@router.delete("/subscriptions")
async def cancel_subscription(
    immediately: bool = False,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    🚫 Cancel subscription
    
    Args:
        immediately: If True, cancel immediately; otherwise at period end
    """
    try:
        billing = StripeBillingManager(api_key=settings.stripe_api_key)
        
        # Get subscription ID
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_subscription_id FROM tenant_subscriptions WHERE tenant_id = %s",
            (tenant_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="No active subscription")
        
        subscription_id = result[0]
        
        # Cancel subscription
        canceled = await billing.cancel_subscription(
            subscription_id=subscription_id,
            immediately=immediately
        )
        
        # Update database
        cursor.execute("""
            UPDATE tenant_subscriptions
            SET status = %s, cancel_at = %s, canceled_at = CURRENT_TIMESTAMP
            WHERE tenant_id = %s
        """, (canceled['status'], canceled.get('cancel_at'), tenant_id))
        
        db.commit()
        cursor.close()
        
        logger.info(f"Canceled subscription for tenant {tenant_id}")
        
        return {
            "success": True,
            "message": "Subscription canceled",
            "cancellation": canceled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription cancellation failed: {str(e)}"
        )


# ============================================================================
# Invoice Endpoints
# ============================================================================

@router.get("/invoices")
async def get_invoices(
    limit: int = 10,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📄 Get invoice history with PDF download links
    """
    try:
        if not settings.stripe_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe billing not configured"
            )
        
        billing = StripeBillingManager(api_key=settings.stripe_api_key)
        
        # Get Stripe customer ID
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_customer_id FROM tenant_subscriptions WHERE tenant_id = %s",
            (tenant_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if not result or not result[0]:
            return {"invoices": [], "total": 0}
        
        customer_id = result[0]
        
        # Get invoices from Stripe
        invoices = await billing.get_invoices(customer_id=customer_id, limit=limit)
        
        return {
            "invoices": invoices,
            "total": len(invoices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get invoices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get invoices"
        )


@router.post("/invoices/{invoice_id}/generate")
async def generate_invoice(
    invoice_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📄 Generate/download invoice PDF
    
    Returns invoice PDF download link and hosted URL
    """
    try:
        if not settings.stripe_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe billing not configured"
            )
        
        import stripe
        stripe.api_key = settings.stripe_api_key
        
        # Verify tenant owns this invoice
        cursor = db.cursor()
        cursor.execute(
            "SELECT stripe_customer_id FROM tenant_subscriptions WHERE tenant_id = %s",
            (tenant_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Tenant subscription not found")
        
        customer_id = result[0]
        
        # Retrieve invoice
        invoice = stripe.Invoice.retrieve(invoice_id)
        
        if invoice.customer != customer_id:
            raise HTTPException(status_code=403, detail="Invoice not found for this tenant")
        
        # Invoice PDF is automatically generated by Stripe
        return {
            "invoice_id": invoice.id,
            "invoice_pdf": invoice.invoice_pdf,
            "hosted_invoice_url": invoice.hosted_invoice_url,
            "status": invoice.status,
            "amount_due": invoice.amount_due / 100,  # Convert from cents
            "amount_paid": invoice.amount_paid / 100,
            "currency": invoice.currency.upper()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate invoice: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invoice"
        )


# ============================================================================
# Usage Endpoints
# ============================================================================

@router.get("/usage")
async def get_usage(
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📈 Get usage statistics
    """
    try:
        redis_gen = get_redis()
        redis_client = next(redis_gen)
        metering = UsageMetering(db, redis_client)
        
        # Get usage limits
        limits = await metering.check_limits(tenant_id)
        
        # Get overage charges
        overage = await metering.calculate_overage_charges(tenant_id)
        
        return {
            "usage": limits,
            "overage_charges": overage
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage statistics"
        )


@router.get("/usage/history")
async def get_usage_history(
    months: int = 3,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres)
):
    """
    📊 Get usage history
    """
    try:
        redis_gen = get_redis()
        redis_client = next(redis_gen)
        metering = UsageMetering(db, redis_client)
        
        history = await metering.get_usage_report(tenant_id, months=months)
        
        return {"usage_history": history}
        
    except Exception as e:
        logger.error(f"Failed to get usage history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage history"
        )


# ============================================================================
# Webhook Endpoint
# ============================================================================

@router.post("/webhooks")
async def stripe_webhook(request: Request, db=Depends(get_postgres)):
    """
    🔔 Stripe webhook handler
    
    Receives events from Stripe (payment_succeeded, payment_failed, etc.)
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        billing = StripeBillingManager(api_key=settings.stripe_api_key)
        
        # Verify and process webhook
        event = await billing.handle_webhook(
            payload=payload,
            sig_header=sig_header,
            webhook_secret=settings.stripe_webhook_secret
        )
        
        logger.info(f"Processed Stripe webhook: {event['event_type']}")
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )

