"""
Payment Gateway Webhook Integration
Handles real-time transaction events from payment processors
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Header, status
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
from decimal import Decimal
import logging
import hmac
import hashlib
import json

from ingestion.realtime_api import RealtimeTransactionAPI, TransactionCreate
from middleware import get_current_tenant
from deps import get_postgres, get_redis
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# ============================================================================
# Stripe Webhook
# ============================================================================

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres),
    redis_client=Depends(get_redis)
):
    """
    Handle Stripe payment events
    
    Webhook events:
    - charge.succeeded: Completed payment
    - charge.failed: Failed payment
    - payment_intent.succeeded: Successful payment intent
    - payment_intent.payment_failed: Failed payment intent
    
    Returns fraud score and recommendation
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Verify webhook signature (if Stripe secret is configured)
        if settings.stripe_webhook_secret:
            try:
                import stripe
                event = stripe.Webhook.construct_event(
                    body, sig_header, settings.stripe_webhook_secret
                )
            except ValueError as e:
                logger.error(f"Invalid Stripe payload: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payload"
                )
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid Stripe signature: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid signature"
                )
        else:
            # In development, parse without verification
            event = json.loads(body.decode('utf-8'))
            logger.warning("Stripe webhook signature verification disabled (no secret configured)")
        
        # Initialize ingestion API
        api = RealtimeTransactionAPI(db, redis_client)
        
        # Handle different event types
        event_type = event.get('type', '')
        event_data = event.get('data', {}).get('object', {})
        
        if event_type == 'charge.succeeded':
            return await _handle_stripe_charge(api, tenant_id, event_data)
        elif event_type == 'payment_intent.succeeded':
            return await _handle_stripe_payment_intent(api, tenant_id, event_data)
        elif event_type in ['charge.failed', 'payment_intent.payment_failed']:
            return await _handle_stripe_failed(api, tenant_id, event_data, event_type)
        else:
            logger.info(f"Unhandled Stripe event type: {event_type}")
            return {"status": "received", "event_type": event_type}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


async def _handle_stripe_charge(
    api: RealtimeTransactionAPI,
    tenant_id: str,
    charge: dict
) -> dict:
    """Handle Stripe charge.succeeded event"""
    # Extract transaction data
    customer_id = charge.get('customer', 'unknown')
    amount = charge.get('amount', 0) / 100  # Stripe uses cents
    currency = charge.get('currency', 'usd').upper()
    
    # Get billing details
    billing = charge.get('billing_details', {})
    address = billing.get('address', {})
    
    # Get payment method details
    payment_method = charge.get('payment_method_details', {})
    card = payment_method.get('card', {})
    
    # Create transaction
    transaction = TransactionCreate(
        account_id=customer_id,
        amount=Decimal(str(amount)),
        currency=currency,
        merchant=charge.get('description', 'Unknown Merchant') or 'Unknown Merchant',
        merchant_id=charge.get('merchant', None),
        channel='ONLINE',
        city=address.get('city'),
        country=address.get('country'),
        ip_address=charge.get('metadata', {}).get('ip_address'),
        device_id=charge.get('source', {}).get('fingerprint'),
        transaction_time=datetime.fromtimestamp(charge.get('created', 0)),
        reference_id=charge.get('id'),
        metadata={
            'stripe_charge_id': charge.get('id'),
            'payment_method': payment_method.get('type'),
            'card_brand': card.get('brand'),
            'card_last4': card.get('last4'),
            'source': 'stripe_webhook',
            'receipt_url': charge.get('receipt_url')
        }
    )
    
    # Ingest transaction and get fraud score
    result = await api.ingest_transaction(tenant_id, transaction)
    
    # If high risk, recommend action
    action = "approved"
    recommendation = None
    if result['fraud_score'] > 0.7:
        action = "blocked"
        recommendation = "High fraud risk detected. Consider refunding this charge."
    elif result['fraud_score'] > 0.5:
        action = "review"
        recommendation = "Medium fraud risk. Review before fulfillment."
    
    return {
        "status": "processed",
        "transaction_id": result['transaction_id'],
        "fraud_score": result['fraud_score'],
        "action": action,
        "recommendation": recommendation,
        "stripe_charge_id": charge.get('id')
    }


async def _handle_stripe_payment_intent(
    api: RealtimeTransactionAPI,
    tenant_id: str,
    payment_intent: dict
) -> dict:
    """Handle Stripe payment_intent.succeeded event"""
    # Similar to charge but from payment intent
    customer_id = payment_intent.get('customer', 'unknown')
    amount = payment_intent.get('amount', 0) / 100
    
    transaction = TransactionCreate(
        account_id=customer_id,
        amount=Decimal(str(amount)),
        currency=payment_intent.get('currency', 'usd').upper(),
        merchant='Payment Intent',
        channel='ONLINE',
        transaction_time=datetime.fromtimestamp(payment_intent.get('created', 0)),
        reference_id=payment_intent.get('id'),
        metadata={
            'stripe_payment_intent_id': payment_intent.get('id'),
            'source': 'stripe_webhook'
        }
    )
    
    result = await api.ingest_transaction(tenant_id, transaction)
    
    return {
        "status": "processed",
        "transaction_id": result['transaction_id'],
        "fraud_score": result['fraud_score'],
        "stripe_payment_intent_id": payment_intent.get('id')
    }


async def _handle_stripe_failed(
    api: RealtimeTransactionAPI,
    tenant_id: str,
    event_data: dict,
    event_type: str
) -> dict:
    """Handle failed payment events"""
    logger.info(f"Stripe {event_type} event received - payment failed")
    return {
        "status": "received",
        "event_type": event_type,
        "action": "log_failure"
    }


# ============================================================================
# PayPal Webhook
# ============================================================================

@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    db=Depends(get_postgres),
    redis_client=Depends(get_redis)
):
    """
    Handle PayPal webhook events
    
    Supported events:
    - PAYMENT.CAPTURE.COMPLETED: Payment captured
    - PAYMENT.CAPTURE.DENIED: Payment denied
    - CHECKOUT.ORDER.COMPLETED: Order completed
    """
    try:
        body = await request.json()
        event_type = body.get('event_type', '')
        resource = body.get('resource', {})
        
        # Verify webhook signature (PayPal provides verification endpoint)
        # TODO: Implement PayPal webhook verification
        
        api = RealtimeTransactionAPI(db, redis_client)
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            return await _handle_paypal_payment(api, tenant_id, resource)
        elif event_type == 'CHECKOUT.ORDER.COMPLETED':
            return await _handle_paypal_order(api, tenant_id, resource)
        else:
            logger.info(f"Unhandled PayPal event: {event_type}")
            return {"status": "received", "event_type": event_type}
            
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


async def _handle_paypal_payment(
    api: RealtimeTransactionAPI,
    tenant_id: str,
    capture: dict
) -> dict:
    """Handle PayPal payment capture"""
    amount_info = capture.get('amount', {})
    payer_info = capture.get('payer', {})
    
    transaction = TransactionCreate(
        account_id=payer_info.get('payer_id', 'unknown'),
        amount=Decimal(str(amount_info.get('value', 0))),
        currency=amount_info.get('currency_code', 'USD'),
        merchant=capture.get('merchant_id', 'PayPal Merchant'),
        channel='ONLINE',
        transaction_time=datetime.fromisoformat(
            capture.get('create_time', datetime.utcnow().isoformat()).replace('Z', '+00:00')
        ),
        reference_id=capture.get('id'),
        metadata={
            'paypal_capture_id': capture.get('id'),
            'paypal_order_id': capture.get('supplementary_data', {}).get('related_ids', {}).get('order_id'),
            'source': 'paypal_webhook'
        }
    )
    
    result = await api.ingest_transaction(tenant_id, transaction)
    
    return {
        "status": "processed",
        "transaction_id": result['transaction_id'],
        "fraud_score": result['fraud_score'],
        "paypal_capture_id": capture.get('id')
    }


async def _handle_paypal_order(
    api: RealtimeTransactionAPI,
    tenant_id: str,
    order: dict
) -> dict:
    """Handle PayPal order completion"""
    purchase_units = order.get('purchase_units', [])
    if not purchase_units:
        return {"status": "skipped", "reason": "No purchase units"}
    
    # Process first purchase unit
    unit = purchase_units[0]
    amount = unit.get('amount', {})
    payer = order.get('payer', {})
    
    transaction = TransactionCreate(
        account_id=payer.get('payer_id', 'unknown'),
        amount=Decimal(str(amount.get('value', 0))),
        currency=amount.get('currency_code', 'USD'),
        merchant=unit.get('payee', {}).get('email_address', 'PayPal Merchant'),
        channel='ONLINE',
        transaction_time=datetime.fromisoformat(
            order.get('create_time', datetime.utcnow().isoformat()).replace('Z', '+00:00')
        ),
        reference_id=order.get('id'),
        metadata={
            'paypal_order_id': order.get('id'),
            'source': 'paypal_webhook'
        }
    )
    
    result = await api.ingest_transaction(tenant_id, transaction)
    
    return {
        "status": "processed",
        "transaction_id": result['transaction_id'],
        "fraud_score": result['fraud_score'],
        "paypal_order_id": order.get('id')
    }


# ============================================================================
# Webhook Health Check
# ============================================================================

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {
        "status": "healthy",
        "webhooks": {
            "stripe": "enabled",
            "paypal": "enabled"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

