"""
Stripe Billing Integration
Handles subscriptions, payments, and usage-based billing
"""
import stripe
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SubscriptionPlan(str, Enum):
    """Subscription plan tiers"""
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


# Plan pricing (monthly, in cents)
PLAN_PRICING = {
    SubscriptionPlan.STARTER: {
        "price": 19900,  # $199
        "name": "Starter Plan",
        "transactions": 50000,
        "users": 5,
        "features": ["Email support", "Basic ML models", "API access"]
    },
    SubscriptionPlan.PROFESSIONAL: {
        "price": 79900,  # $799
        "name": "Professional Plan",
        "transactions": 500000,
        "users": 25,
        "features": ["Priority support", "SSO", "Custom ML models", "Advanced API"]
    },
    SubscriptionPlan.ENTERPRISE: {
        "price": 299900,  # $2,999
        "name": "Enterprise Plan",
        "transactions": None,  # Unlimited
        "users": None,  # Unlimited
        "features": ["24/7 support", "Dedicated DB", "Custom features", "SLA"]
    }
}


class StripeBillingManager:
    """Manages Stripe billing operations"""
    
    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.api_key = api_key
    
    async def create_customer(
        self,
        tenant_id: str,
        email: str,
        name: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a Stripe customer
        
        Returns: Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "tenant_id": tenant_id,
                    **(metadata or {})
                }
            )
            logger.info(f"Created Stripe customer: {customer.id} for tenant {tenant_id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise
    
    async def create_subscription(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        payment_method_id: Optional[str] = None
    ) -> Dict:
        """
        Create a subscription for a customer
        
        Returns: Subscription details
        """
        try:
            # Get or create price
            price = await self._get_or_create_price(plan)
            
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price.id}],
                "payment_behavior": "default_incomplete",
                "payment_settings": {"save_default_payment_method": "on_subscription"},
                "expand": ["latest_invoice.payment_intent"]
            }
            
            if payment_method_id:
                subscription_params["default_payment_method"] = payment_method_id
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            logger.info(f"Created subscription: {subscription.id} for customer {customer_id}")
            
            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                "status": subscription.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
    
    async def _get_or_create_price(self, plan: SubscriptionPlan) -> stripe.Price:
        """Get existing price or create new one"""
        plan_config = PLAN_PRICING[plan]
        
        # Try to find existing price
        prices = stripe.Price.list(
            product_data={"name": plan_config["name"]},
            active=True,
            limit=1
        )
        
        if prices.data:
            return prices.data[0]
        
        # Create new price
        price = stripe.Price.create(
            unit_amount=plan_config["price"],
            currency="usd",
            recurring={"interval": "month"},
            product_data={
                "name": plan_config["name"],
                "metadata": {"plan": plan.value}
            }
        )
        
        return price
    
    async def update_subscription(
        self,
        subscription_id: str,
        new_plan: SubscriptionPlan
    ) -> Dict:
        """
        Update subscription to a different plan
        
        Returns: Updated subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            price = await self._get_or_create_price(new_plan)
            
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": price.id
                }],
                proration_behavior="create_prorations"
            )
            
            logger.info(f"Updated subscription {subscription_id} to plan {new_plan}")
            
            return {
                "subscription_id": updated_subscription.id,
                "status": updated_subscription.status,
                "current_period_end": updated_subscription.current_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> Dict:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            immediately: If True, cancel immediately; otherwise at period end
        
        Returns: Cancellation details
        """
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            logger.info(f"Cancelled subscription: {subscription_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise
    
    async def record_usage(
        self,
        subscription_id: str,
        quantity: int,
        timestamp: Optional[int] = None
    ) -> Dict:
        """
        Record usage for metered billing
        
        Args:
            subscription_id: Stripe subscription ID
            quantity: Number of transactions/events
            timestamp: Unix timestamp (defaults to now)
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            subscription_item_id = subscription["items"]["data"][0].id
            
            usage_record = stripe.SubscriptionItem.create_usage_record(
                subscription_item_id,
                quantity=quantity,
                timestamp=timestamp or int(datetime.utcnow().timestamp()),
                action="increment"
            )
            
            return {
                "usage_record_id": usage_record.id,
                "quantity": usage_record.quantity,
                "timestamp": usage_record.timestamp
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to record usage: {e}")
            raise
    
    async def get_invoices(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get customer invoices"""
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            
            return [
                {
                    "id": invoice.id,
                    "amount_due": invoice.amount_due,
                    "amount_paid": invoice.amount_paid,
                    "status": invoice.status,
                    "created": invoice.created,
                    "invoice_pdf": invoice.invoice_pdf
                }
                for invoice in invoices.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get invoices: {e}")
            raise
    
    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict:
        """Attach payment method to customer"""
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            return {
                "payment_method_id": payment_method.id,
                "type": payment_method.type,
                "card": payment_method.card
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise
    
    async def handle_webhook(self, payload: bytes, sig_header: str, webhook_secret: str) -> Dict:
        """
        Handle Stripe webhook events
        
        Returns: Event details
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle different event types
            if event.type == "invoice.payment_succeeded":
                # Payment succeeded
                invoice = event.data.object
                logger.info(f"Payment succeeded for invoice: {invoice.id}")
                
            elif event.type == "invoice.payment_failed":
                # Payment failed
                invoice = event.data.object
                logger.warning(f"Payment failed for invoice: {invoice.id}")
                
            elif event.type == "customer.subscription.deleted":
                # Subscription cancelled
                subscription = event.data.object
                logger.info(f"Subscription cancelled: {subscription.id}")
            
            return {"event_type": event.type, "processed": True}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise

