"""
RevOps Data Writer — Main Orchestrator
Simulates a production A-series B2B SaaS revenue engine across 7 layers.

Revenue Funnel Covered:
    1. Meta Ads          → Demand generation (paid marketing events)
    2. HubSpot           → CRM (contacts, companies, deals with stage history)
    3. Stripe            → Billing (customers, subscriptions, 12-month invoice history)
    4. PostHog           → Product analytics (sessions, onboarding, feature-depth)
    5. Freshdesk         → Customer support (tickets correlated with subscription health)
    6. Supabase          → Product database + dim_date (warehouse-ready)
    7. Call Transcripts  → Sales intelligence (discovery/demo/closing calls → Supabase)

Design principles:
    - Every layer writes to its real sandbox API — no local mocks
    - Data is cross-referenced where possible (HubSpot deal_id in call_transcripts)
    - Idempotent-friendly: safe to run repeatedly for snapshot/SCD testing

Usage:
    python main_revops_writer.py --all
    python main_revops_writer.py --services hubspot stripe posthog
    python main_revops_writer.py --check-config
    python main_revops_writer.py --dry-run
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, List

from config import config

from integrations.call_transcript_writer import write_call_transcripts
from integrations.freshdesk_writer import write_freshdesk_data
from integrations.hubspot_writer import write_hubspot_data
from integrations.meta_ads_writer import write_sample_data_to_meta
from integrations.posthog_writer import write_posthog_data
from integrations.stripe_writer import write_stripe_data
from integrations.supabase_writer import write_supabase_data
from utils.logger import setup_logger
from utils.simulation_context import SimulationContext, build_simulation_context

# Setup logger
logger = setup_logger('revops_writer', log_file='logs/revops_writer.log')


class RevOpsDataWriter:
    """
    Main orchestrator for the A-series Revenue Engine simulation.
    Writes realistic B2B SaaS data to every configured platform.
    """

    def __init__(self):
        self.config = config
        self.results = {}
        self.errors = {}
        self._hubspot_deal_ids: List[str] = []
        self.context: SimulationContext = None  # set in write_all()

    # ------------------------------------------------------------------
    # Layer 1 — Marketing
    # ------------------------------------------------------------------

    def write_meta_ads(self, num_events: int = 50, pixel_id: str = None, test_code: str = None) -> Dict:
        """Write conversion events to Meta Ads (demand generation layer)"""
        logger.info("=" * 70)
        logger.info("META ADS — Demand Generation")
        logger.info("=" * 70)

        try:
            if not self.config.meta_ads:
                raise ValueError("Meta Ads not configured. Set META_ACCESS_TOKEN and META_ACCOUNT_ID.")

            if not pixel_id:
                logger.warning("No pixel_id provided for Meta Ads. Skipping conversion events.")
                logger.info("Tip: provide --meta-pixel-id to enable this layer.")
                return {'status': 'skipped', 'reason': 'no_pixel_id'}

            result = write_sample_data_to_meta(
                access_token=self.config.meta_ads.access_token,
                pixel_id=pixel_id,
                test_event_code=test_code,
                num_events=num_events
            )

            logger.info(f"✓ Meta Ads complete:")
            logger.info(f"  - Events sent: {result['total_events']}")
            logger.info(f"  - Batches:     {result['batches_sent']}")
            return result

        except Exception as e:
            logger.error(f"✗ Meta Ads failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Layer 2 — CRM
    # ------------------------------------------------------------------

    def write_hubspot(self, num_contacts: int = 15, num_companies: int = 8, num_deals: int = 12) -> Dict:
        """Write CRM data to HubSpot and capture deal IDs for cross-referencing"""
        logger.info("=" * 70)
        logger.info("HUBSPOT — CRM (Contacts / Companies / Deals)")
        logger.info("=" * 70)

        try:
            if not self.config.hubspot:
                raise ValueError("HubSpot not configured. Set HUBSPOT_ACCESS_TOKEN.")

            result = write_hubspot_data(
                access_token=self.config.hubspot.access_token,
                num_contacts=num_contacts,
                num_companies=num_companies,
                num_deals=num_deals,
                context=self.context,
            )

            # Capture deal IDs for call transcript cross-referencing
            self._hubspot_deal_ids = [
                str(d.get('id', '')) for d in result.get('deals', []) if d.get('id')
            ]

            logger.info(f"✓ HubSpot complete:")
            logger.info(f"  - Contacts:  {len(result['contacts'])}")
            logger.info(f"  - Companies: {len(result['companies'])}")
            logger.info(f"  - Deals:     {len(result['deals'])}")
            logger.info(f"  - Errors:    {len(result['errors'])}")
            return result

        except Exception as e:
            logger.error(f"✗ HubSpot failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Layer 3 — Billing
    # ------------------------------------------------------------------

    def write_stripe(self, num_customers: int = 15) -> Dict:
        """Write billing data to Stripe (subscriptions + 12-month invoice history)"""
        logger.info("=" * 70)
        logger.info("STRIPE — Billing (Subscriptions / Invoices)")
        logger.info("=" * 70)

        try:
            if not self.config.stripe:
                raise ValueError("Stripe not configured. Set STRIPE_SECRET_KEY.")

            result = write_stripe_data(
                api_key=self.config.stripe.secret_key,
                num_customers=num_customers,
                context=self.context,
            )

            logger.info(f"✓ Stripe complete:")
            logger.info(f"  - Customers:     {len(result['customers'])}")
            logger.info(f"  - Subscriptions: {len(result['subscriptions'])}")
            logger.info(f"  - Invoices:      {len(result['invoice_history'])}")
            logger.info(f"  - Payments:      {len(result['payments'])}")
            return result

        except Exception as e:
            logger.error(f"✗ Stripe failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Layer 4 — Product Analytics
    # ------------------------------------------------------------------

    def write_posthog(self, num_users: int = 25, days_back: int = 30) -> Dict:
        """Write product analytics to PostHog (sessions, onboarding, feature-depth events)"""
        logger.info("=" * 70)
        logger.info("POSTHOG — Product Analytics (Sessions / Features / Onboarding)")
        logger.info("=" * 70)

        try:
            if not self.config.posthog:
                raise ValueError("PostHog not configured. Set POSTHOG_API_KEY.")

            result = write_posthog_data(
                api_key=self.config.posthog.api_key,
                host=self.config.posthog.host,
                num_users=num_users,
                days_back=days_back,
                context=self.context,
            )

            logger.info(f"✓ PostHog complete:")
            logger.info(f"  - Events sent:      {result['events_sent']}")
            logger.info(f"  - Users identified: {result['users_identified']}")
            logger.info(f"  - Date range:       {result['date_range_days']} days")
            return result

        except Exception as e:
            logger.error(f"✗ PostHog failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Layer 5 — Support
    # ------------------------------------------------------------------

    def write_freshdesk(self, ticket_count: int = 25) -> Dict:
        """Write support tickets to Freshdesk"""
        logger.info("=" * 70)
        logger.info("FRESHDESK — Customer Support (Tickets)")
        logger.info("=" * 70)

        try:
            if not self.config.freshdesk:
                raise ValueError("Freshdesk not configured. Set FRESHDESK_DOMAIN and FRESHDESK_API_KEY.")

            result = write_freshdesk_data(
                domain=self.config.freshdesk.domain,
                api_key=self.config.freshdesk.api_key,
                ticket_count=ticket_count,
                context=self.context,
            )

            logger.info(f"✓ Freshdesk complete:")
            logger.info(f"  - Tickets: {result['successful']}/{result['total_attempted']}")
            logger.info(f"  - Failed:  {result['failed']}")
            return result

        except Exception as e:
            logger.error(f"✗ Freshdesk failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Layer 6 — Product Database / Warehouse
    # ------------------------------------------------------------------

    def write_supabase(self, num_companies: int = 40) -> Dict:
        """Write product DB records to Supabase (companies, users, events, dim_date)"""
        logger.info("=" * 70)
        logger.info("SUPABASE — Product Database + Data Warehouse")
        logger.info("=" * 70)

        try:
            if not self.config.supabase:
                raise ValueError("Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.")

            result = write_supabase_data(
                url=self.config.supabase.url,
                service_key=self.config.supabase.service_key,
                num_companies=num_companies,
                context=self.context,
            )

            logger.info(f"✓ Supabase complete:")
            logger.info(f"  - Companies:     {result['companies']}")
            logger.info(f"  - Users:         {result['users']}")
            logger.info(f"  - Subscriptions: {result['subscriptions']}")
            logger.info(f"  - Events:        {result['events']}")
            logger.info(f"  - dim_date rows: {result['dim_date_rows']}")
            logger.info(f"  - Status deltas: {result.get('companies_updated', 0)}")
            return result

        except Exception as e:
            logger.error(f"✗ Supabase failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Layer 7 — Sales Intelligence
    # ------------------------------------------------------------------

    def write_call_transcripts(self, num_calls: int = 30, days_back: int = 60) -> Dict:
        """
        Write synthetic sales call transcripts to Supabase (call_transcripts table).
        Cross-references HubSpot deal IDs if HubSpot was written in this run.
        """
        logger.info("=" * 70)
        logger.info("CALL TRANSCRIPTS — Sales Intelligence (→ Supabase)")
        logger.info("=" * 70)

        try:
            if not self.config.supabase:
                raise ValueError("Supabase not configured. Call transcripts require Supabase.")

            result = write_call_transcripts(
                url=self.config.supabase.url,
                service_key=self.config.supabase.service_key,
                num_calls=num_calls,
                days_back=days_back,
                hubspot_deal_ids=self._hubspot_deal_ids or None,
                context=self.context,
            )

            logger.info(f"✓ Call transcripts complete:")
            logger.info(f"  - Records inserted: {result['total_inserted']}")
            logger.info(f"  - Call types:       {', '.join(result['call_types'])}")
            logger.info(f"  - Outcomes:         {result['outcome_counts']}")
            logger.info(f"  - Reps simulated:   {', '.join(result['reps_simulated'])}")
            return result

        except Exception as e:
            logger.error(f"✗ Call transcripts failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    def write_all(self, services: List[str] = None, num_random: int = 4, **kwargs) -> Dict:
        """
        Write data to all or specified services.

        Args:
            services:   List of service names (None = all configured)
            num_random: Extra random companies per run (organic growth)
            **kwargs:   meta_pixel_id, meta_test_code
        """
        logger.info("\n")
        logger.info("=" * 70)
        logger.info("A-SERIES REVENUE ENGINE — Simulation Start")
        logger.info("=" * 70)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")

        # Build shared context FIRST — all 7 layers use same company personas
        self.context = build_simulation_context(num_random=num_random)
        logger.info("\n" + self.context.summary())
        logger.info("")

        configured_services = self.config.get_configured_services()
        logger.info(f"Configured layers: {', '.join(configured_services)}")

        if services:
            services_to_write = [s for s in services if s in configured_services]
            if not services_to_write:
                logger.error("None of the specified services are configured.")
                return {}
        else:
            services_to_write = configured_services

        logger.info(f"Writing to: {', '.join(services_to_write)}")
        logger.info("")

        # Scaling factors: base personas + num_random
        total_companies = len(self.context.fixed_personas) + num_random
        total_contacts  = total_companies * 2
        total_deals     = int(total_companies * 1.5)
        total_customers = total_companies
        total_tickets   = total_companies * 3
        total_events    = total_companies * 10

        for service in services_to_write:
            try:
                if service == 'meta_ads':
                    self.results['meta_ads'] = self.write_meta_ads(
                        pixel_id=kwargs.get('meta_pixel_id'),
                        test_code=kwargs.get('meta_test_code'),
                        num_events=num_random * 10
                    )
                elif service == 'hubspot':
                    self.results['hubspot'] = self.write_hubspot(
                        num_companies=total_companies,
                        num_contacts=total_contacts,
                        num_deals=total_deals
                    )
                elif service == 'stripe':
                    self.results['stripe'] = self.write_stripe(
                        num_customers=total_customers
                    )
                elif service == 'posthog':
                    self.results['posthog'] = self.write_posthog(
                        num_users=total_contacts
                    )
                elif service == 'freshdesk':
                    self.results['freshdesk'] = self.write_freshdesk(
                        ticket_count=total_tickets
                    )
                elif service == 'supabase':
                    self.results['supabase'] = self.write_supabase(
                        num_companies=total_companies
                    )
                elif service == 'call_transcripts':
                    self.results['call_transcripts'] = self.write_call_transcripts()

                logger.info("")

            except Exception as e:
                self.errors[service] = str(e)
                logger.error(f"Failed to write to {service}: {e}")
                logger.info("")

        self.print_summary()
        return self.results

    def print_summary(self):
        """Print final run summary"""
        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)

        if self.results:
            logger.info(f"✓ Successfully wrote to {len(self.results)} layer(s):")
            for service in self.results:
                logger.info(f"  • {service.upper()}")

        if self.errors:
            logger.info(f"\n✗ Failed to write to {len(self.errors)} layer(s):")
            for service, error in self.errors.items():
                logger.info(f"  • {service.upper()}: {error}")

        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="A-series B2B SaaS Revenue Engine (v2.0) — Simulation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run the full 7-layer engine
  python main_revops_writer.py --all

  # Run specific layers
  python main_revops_writer.py --services hubspot stripe posthog

  # Include Meta Ads conversion events
  python main_revops_writer.py --all --meta-pixel-id 123456789

  # Check which layers are configured
  python main_revops_writer.py --check-config
        """
    )

    parser.add_argument('--all', action='store_true', help='Run all configured layers')
    parser.add_argument(
        '--services',
        nargs='+',
        choices=['meta_ads', 'hubspot', 'stripe', 'posthog', 'freshdesk', 'supabase', 'call_transcripts'],
        help='Specific layers to run'
    )
    parser.add_argument('--meta-pixel-id', type=str, help='Meta Ads Pixel ID')
    parser.add_argument('--meta-test-code', type=str, help='Meta Ads test event code')
    parser.add_argument('--num-random', type=int, default=4, help='Number of extra random companies to simulate (organic growth)')
    parser.add_argument('--check-config', action='store_true', help='Show configured layers')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without writing data')

    args = parser.parse_args()

    if args.check_config:
        configured = config.get_configured_services()
        if configured:
            logger.info(f"Configured layers ({len(configured)}): {', '.join(configured)}")
        else:
            logger.warning("No layers configured. Set environment variables in .env")
        return

    if args.dry_run:
        logger.info("DRY RUN — No data will be written")
        configured = config.get_configured_services()
        logger.info(f"Would write to: {', '.join(configured)}")
        return

    if not args.all and not args.services:
        parser.error("Must specify either --all or --services")

    writer = RevOpsDataWriter()

    try:
        writer.write_all(
            services=args.services if not args.all else None,
            meta_pixel_id=args.meta_pixel_id,
            meta_test_code=args.meta_test_code,
            num_random=args.num_random
        )

        if writer.errors:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
