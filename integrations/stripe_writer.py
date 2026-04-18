"""
Stripe Data Writer
Creates realistic B2B SaaS customer and payment data for testing/sandbox
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import stripe

from utils.logger import get_logger

logger = get_logger(__name__)


class StripeDataWriter:
    """Write realistic B2B SaaS data to Stripe"""

    # Realistic B2B SaaS company data
    COMPANY_NAMES = [
        "Acme Corp", "TechStart Inc", "DataFlow Solutions", "CloudScale Systems",
        "Innovate Labs", "Digital Ventures", "StreamLine Co", "Nexus Technologies",
        "Quantum Analytics", "Velocity Partners", "Apex Solutions", "Zenith Corp",
        "Fusion Systems", "Catalyst Group", "Pioneer Tech", "Summit Solutions"
    ]

    FIRST_NAMES = [
        "John", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Amanda",
        "James", "Lisa", "William", "Jennifer", "Richard", "Michelle", "Thomas"
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Taylor"
    ]

    # B2B SaaS pricing tiers
    PRICING_PLANS = {
        "starter": {"price": 49, "interval": "month"},
        "professional": {"price": 149, "interval": "month"},
        "business": {"price": 399, "interval": "month"},
        "enterprise": {"price": 999, "interval": "month"},
        "starter_annual": {"price": 490, "interval": "year"},
        "professional_annual": {"price": 1490, "interval": "year"},
        "business_annual": {"price": 3990, "interval": "year"},
    }

    def __init__(self, api_key: str):
        """
        Initialize Stripe writer

        Args:
            api_key: Stripe secret API key
        """
        stripe.api_key = api_key
        self.api_key = api_key
        logger.info("Stripe writer initialized")

    def create_product_and_prices(self) -> Dict[str, str]:
        """
        Create a B2B SaaS product with multiple price points

        Returns:
            Dictionary mapping plan names to price IDs
        """
        logger.info("Creating product and prices in Stripe")

        try:
            # Create main product
            product = stripe.Product.create(
                name="RevOps Analytics Platform",
                description="Complete RevOps analytics and reporting solution for B2B SaaS companies",
                metadata={
                    "category": "saas",
                    "type": "subscription"
                }
            )

            logger.info(f"Created product: {product.id}")

            price_ids = {}

            # Create prices for each plan
            for plan_name, details in self.PRICING_PLANS.items():
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=details["price"] * 100,  # Convert to cents
                    currency="usd",
                    recurring={"interval": details["interval"]},
                    nickname=plan_name.replace("_", " ").title(),
                    metadata={"plan": plan_name}
                )
                price_ids[plan_name] = price.id
                logger.info(f"Created price {plan_name}: {price.id} (${details['price']}/{details['interval']})")

            return price_ids

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create product/prices: {e}")
            raise

    def create_customer(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None
    ) -> stripe.Customer:
        """
        Create a realistic B2B customer

        Args:
            email: Customer email (generated if not provided)
            name: Customer name (generated if not provided)
            company: Company name (generated if not provided)

        Returns:
            Stripe Customer object
        """
        if not name:
            first_name = random.choice(self.FIRST_NAMES)
            last_name = random.choice(self.LAST_NAMES)
            name = f"{first_name} {last_name}"

        if not company:
            company = random.choice(self.COMPANY_NAMES)

        if not email:
            email_name = name.lower().replace(" ", ".")
            email_domain = company.lower().replace(" ", "").replace("corp", "").replace("inc", "")
            email = f"{email_name}@{email_domain}.com"

        try:
            # Create customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                description=f"Customer from {company}",
                metadata={
                    "company": company,
                    "customer_type": "b2b",
                    "source": "sandbox_test"
                },
                address={
                    "city": random.choice(["San Francisco", "New York", "Austin", "Seattle", "Boston"]),
                    "country": "US",
                    "line1": f"{random.randint(100, 9999)} Main Street",
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "state": random.choice(["CA", "NY", "TX", "WA", "MA"])
                },
            )

            # Attach a test payment method to the customer
            # We use a test card token for this purpose
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={"token": "tok_visa"},  # Using a test token
            )

            stripe.PaymentMethod.attach(
                payment_method.id,
                customer=customer.id,
            )

            # Set the attached payment method as the default for the customer
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": payment_method.id},
            )

            logger.info(f"Created customer: {customer.id} ({email}) and attached default payment method {payment_method.id}")
            return customer

        except stripe.error.CardError as e:
            logger.error(f"Stripe card error creating customer: {e.user_message}")
            raise
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer or attach payment method: {e}")
            raise

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0
    ) -> stripe.Subscription:
        """
        Create a subscription for a customer

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Number of trial days (0 for no trial)

        Returns:
            Stripe Subscription object
        """
        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": {
                    "source": "sandbox_test"
                }
            }

            if trial_days > 0:
                params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**params)
            logger.info(f"Created subscription: {subscription.id} for customer {customer_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise

    def create_one_time_payment(
        self,
        customer_id: str,
        amount: int,
        description: str = "One-time service fee"
    ) -> stripe.PaymentIntent:
        """
        Create a one-time payment

        Args:
            customer_id: Stripe customer ID
            amount: Amount in dollars
            description: Payment description

        Returns:
            Stripe PaymentIntent object
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount * 100,  # Convert to cents
                currency="usd",
                customer=customer_id,
                description=description,
                metadata={
                    "source": "sandbox_test"
                },
                # Auto-confirm for testing
                confirm=True,
                payment_method_types=["card"],
                payment_method="pm_card_visa"  # Test card
            )

            logger.info(f"Created payment intent: {payment_intent.id} (${amount})")
            return payment_intent

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise

    def create_invoice_history(
        self,
        customer_id: str,
        subscription_id: str,
        plan_price: int,
        months_back: int = None
    ) -> List[Dict]:
        """
        Create realistic invoice history for a subscription.
        Simulates 3-12 months of past billing with occasional payment failures.

        Real-world patterns modeled:
        - Most invoices are paid on time
        - ~8% of invoices fail (card declined, etc.)
        - Failed invoices are followed by a retry (sometimes successful)

        Args:
            customer_id: Stripe customer ID
            subscription_id: Stripe subscription ID
            plan_price: Monthly price in dollars
            months_back: How many months of history to create (random 3-12 if not set)

        Returns:
            List of created invoice records (as dicts for logging)
        """
        if months_back is None:
            months_back = random.randint(3, 12)

        logger.info(f"Creating {months_back} months of invoice history for sub {subscription_id}")

        invoice_records = []

        for month_offset in range(months_back, 0, -1):
            invoice_date = datetime.now() - timedelta(days=30 * month_offset)

            # 8% chance of payment failure on any given month
            payment_failed = random.random() < 0.08
            status = "open" if payment_failed else "paid"

            # Small amount variation simulates usage overages or discounts
            variation = random.choice([-10, 0, 0, 0, 0, 10, 20, 50])
            amount = max(0, plan_price + variation)

            record = {
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "invoice_date": invoice_date.strftime("%Y-%m-%d"),
                "amount_dollars": amount,
                "status": status,
                "payment_method": "card",
            }
            invoice_records.append(record)

            # After a failure, 70% chance the next retry succeeds
            if payment_failed and random.random() < 0.7:
                retry_date = invoice_date + timedelta(days=3)
                invoice_records.append({
                    "customer_id": customer_id,
                    "subscription_id": subscription_id,
                    "invoice_date": retry_date.strftime("%Y-%m-%d"),
                    "amount_dollars": amount,
                    "status": "paid",
                    "payment_method": "card",
                })

        logger.info(
            f"  → Generated {len(invoice_records)} invoices "
            f"({months_back} months, {sum(1 for r in invoice_records if r['status'] == 'open')} failures)"
        )
        return invoice_records

    def generate_realistic_data_set(
        self,
        num_customers: int = 10,
        subscription_rate: float = 0.7,
        trial_rate: float = 0.3
    ) -> Dict:
        """
        Generate a full realistic dataset

        Args:
            num_customers: Number of customers to create
            subscription_rate: Percentage of customers with active subscriptions
            trial_rate: Percentage of subscriptions that are in trial

        Returns:
            Dictionary with created objects
        """
        logger.info(f"Generating realistic dataset: {num_customers} customers")

        results = {
            "customers": [],
            "subscriptions": [],
            "payments": [],
            "invoice_history": [],
            "price_ids": None
        }

        try:
            # Create product and prices
            price_ids = self.create_product_and_prices()
            results["price_ids"] = price_ids

            # Create customers
            for i in range(num_customers):
                customer = self.create_customer()
                results["customers"].append(customer)

                # Decide if customer should have subscription
                if random.random() < subscription_rate:
                    # Choose random plan (bias toward lower tiers)
                    plan_weights = {
                        "starter": 0.35,
                        "professional": 0.30,
                        "business": 0.20,
                        "enterprise": 0.10,
                        "starter_annual": 0.03,
                        "professional_annual": 0.02
                    }
                    plan = random.choices(
                        list(plan_weights.keys()),
                        weights=list(plan_weights.values())
                    )[0]

                    # Trial or not
                    trial_days = 14 if random.random() < trial_rate else 0

                    subscription = self.create_subscription(
                        customer.id,
                        price_ids[plan],
                        trial_days=trial_days
                    )
                    results["subscriptions"].append(subscription)

                    # Generate invoice history for this subscription
                    plan_price = self.PRICING_PLANS.get(plan, {}).get("price", 99)
                    invoices = self.create_invoice_history(
                        customer_id=customer.id,
                        subscription_id=subscription.id,
                        plan_price=plan_price
                    )
                    results["invoice_history"].extend(invoices)

                # Random chance of one-time payment
                if random.random() < 0.2:
                    payment_types = [
                        ("Implementation fee", random.randint(500, 2000)),
                        ("Training session", random.randint(200, 800)),
                        ("Consulting hours", random.randint(300, 1500)),
                        ("Custom integration", random.randint(1000, 5000))
                    ]
                    desc, amount = random.choice(payment_types)

                    payment = self.create_one_time_payment(
                        customer.id,
                        amount,
                        description=desc
                    )
                    results["payments"].append(payment)

            logger.info("=" * 60)
            logger.info("DATA GENERATION COMPLETE")
            logger.info(f"Customers created:       {len(results['customers'])}")
            logger.info(f"Subscriptions created:   {len(results['subscriptions'])}")
            logger.info(f"Invoice records created: {len(results['invoice_history'])}")
            logger.info(f"One-time payments:       {len(results['payments'])}")
            logger.info("=" * 60)

            return results

        except Exception as e:
            logger.error(f"Failed to generate dataset: {e}")
            raise


def write_stripe_data(api_key: str, num_customers: int = 10) -> Dict:
    """
    Write realistic B2B SaaS data to Stripe

    Args:
        api_key: Stripe secret API key
        num_customers: Number of customers to create

    Returns:
        Dictionary with created data (customers, subscriptions, invoice_history, payments)
    """
    writer = StripeDataWriter(api_key)
    return writer.generate_realistic_data_set(num_customers=num_customers)
