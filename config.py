"""
Configuration management for RevOps Data Ingestion Pipeline
Loads API keys and configuration from environment variables

Stack (A-series B2B SaaS Revenue Engine):
  - Meta Ads     → Demand generation / paid marketing
  - HubSpot      → CRM (contacts, companies, deals)
  - Stripe       → Billing & revenue (subscriptions, invoices)
  - PostHog      → Product analytics (sessions, features, onboarding)
  - Freshdesk    → Customer support (tickets)
  - Supabase     → Product database + data warehouse layer
  - Call Transcripts → Sales intelligence (written to Supabase)
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class MetaAdsConfig:
    """Meta (Facebook) Ads API Configuration"""
    access_token: str
    account_id: str
    app_id: Optional[str] = None
    app_secret: Optional[str] = None


@dataclass
class HubSpotConfig:
    """HubSpot API Configuration"""
    access_token: str
    portal_id: Optional[str] = None


@dataclass
class StripeConfig:
    """Stripe API Configuration"""
    secret_key: str
    webhook_secret: Optional[str] = None


@dataclass
class SupabaseConfig:
    """Supabase Configuration"""
    url: str
    service_key: str
    anon_key: Optional[str] = None


@dataclass
class PostHogConfig:
    """PostHog API Configuration"""
    api_key: str
    host: str = "https://app.posthog.com"
    project_id: Optional[str] = None


@dataclass
class FreshdeskConfig:
    """Freshdesk API Configuration"""
    domain: str  # e.g., yourcompany.freshdesk.com
    api_key: str


class Config:
    """Main configuration class"""

    def __init__(self):
        # Meta Ads
        self.meta_ads: Optional[MetaAdsConfig] = None
        if os.getenv('META_ACCESS_TOKEN') and os.getenv('META_ACCOUNT_ID'):
            self.meta_ads = MetaAdsConfig(
                access_token=os.getenv('META_ACCESS_TOKEN'),
                account_id=os.getenv('META_ACCOUNT_ID'),
                app_id=os.getenv('META_APP_ID'),
                app_secret=os.getenv('META_APP_SECRET')
            )

        # HubSpot
        self.hubspot: Optional[HubSpotConfig] = None
        if os.getenv('HUBSPOT_ACCESS_TOKEN'):
            self.hubspot = HubSpotConfig(
                access_token=os.getenv('HUBSPOT_ACCESS_TOKEN'),
                portal_id=os.getenv('HUBSPOT_PORTAL_ID')
            )

        # Stripe
        self.stripe: Optional[StripeConfig] = None
        if os.getenv('STRIPE_SECRET_KEY'):
            self.stripe = StripeConfig(
                secret_key=os.getenv('STRIPE_SECRET_KEY'),
                webhook_secret=os.getenv('STRIPE_WEBHOOK_SECRET')
            )

        # Supabase
        self.supabase: Optional[SupabaseConfig] = None
        if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_KEY'):
            self.supabase = SupabaseConfig(
                url=os.getenv('SUPABASE_URL'),
                service_key=os.getenv('SUPABASE_SERVICE_KEY'),
                anon_key=os.getenv('SUPABASE_ANON_KEY')
            )

        # PostHog (product analytics — unique session, onboarding, feature-depth data)
        self.posthog: Optional[PostHogConfig] = None
        if os.getenv('POSTHOG_API_KEY'):
            self.posthog = PostHogConfig(
                api_key=os.getenv('POSTHOG_API_KEY'),
                host=os.getenv('POSTHOG_HOST', 'https://app.posthog.com'),
                project_id=os.getenv('POSTHOG_PROJECT_ID')
            )

        # Freshdesk
        self.freshdesk: Optional[FreshdeskConfig] = None
        if os.getenv('FRESHDESK_DOMAIN') and os.getenv('FRESHDESK_API_KEY'):
            self.freshdesk = FreshdeskConfig(
                domain=os.getenv('FRESHDESK_DOMAIN'),
                api_key=os.getenv('FRESHDESK_API_KEY')
            )

        # Database settings
        self.db_path = os.getenv('DB_PATH', 'revops_data.db')

        # Ingestion settings
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.lookback_days = int(os.getenv('LOOKBACK_DAYS', '7'))

    def is_configured(self, service: str) -> bool:
        """Check if a service is configured"""
        return getattr(self, service.lower(), None) is not None

    def get_configured_services(self) -> list:
        """Get list of configured services in funnel order"""
        services = []
        if self.meta_ads:
            services.append('meta_ads')
        if self.hubspot:
            services.append('hubspot')
        if self.stripe:
            services.append('stripe')
        if self.posthog:
            services.append('posthog')
        if self.freshdesk:
            services.append('freshdesk')
        if self.supabase:
            services.append('supabase')
            # call_transcripts depends on supabase being configured
            services.append('call_transcripts')
        return services


# Global config instance
config = Config()
