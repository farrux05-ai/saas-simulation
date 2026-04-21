"""
RevOps Data Writers — Integration modules for the A-series Revenue Engine

Layer order (mirrors revenue funnel):
  1. meta_ads_writer      → Marketing / demand generation
  2. hubspot_writer       → CRM (contacts, companies, deals)
  3. stripe_writer        → Billing (subscriptions, invoices)
  4. posthog_writer       → Product analytics (sessions, onboarding, features)
  5. freshdesk_writer     → Support (tickets)
  6. supabase_writer      → Product DB + data warehouse layer
  7. call_transcript_writer → Sales intelligence (Gong-style transcripts → Supabase)
"""

from .call_transcript_writer import write_call_transcripts
from .freshdesk_writer import write_freshdesk_data
from .hubspot_writer import write_hubspot_data
from .meta_ads_writer import write_sample_data_to_meta
from .posthog_writer import write_posthog_data
from .stripe_writer import write_stripe_data
from .supabase_writer import write_supabase_data

__all__ = [
    'write_sample_data_to_meta',
    'write_hubspot_data',
    'write_stripe_data',
    'write_posthog_data',
    'write_freshdesk_data',
    'write_supabase_data',
    'write_call_transcripts',
]
