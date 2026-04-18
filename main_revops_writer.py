"""
RevOps Data Writer - Main Orchestrator
Writes realistic B2B SaaS data to all configured platforms for testing/sandbox environments

This script populates your sandbox/free trial accounts with realistic RevOps data:
- HubSpot: Contacts, Companies, Deals
- Stripe: Customers, Subscriptions, Payments
- Supabase: Users, Events, Companies, Subscriptions
- Mixpanel: Product analytics events and user profiles
- PostHog: Product analytics events
- Freshdesk: Support tickets
- Meta Ads: Conversion events (leads, signups, purchases)

Usage:
    python main_revops_writer.py --all
    python main_revops_writer.py --services hubspot stripe
    python main_revops_writer.py --dry-run
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, List

from config import config

from integrations.freshdesk_writer import write_freshdesk_data
from integrations.hubspot_writer import write_hubspot_data
from integrations.meta_ads_writer import write_sample_data_to_meta
from integrations.mixpanel_writer import write_mixpanel_data
from integrations.posthog_writer import write_posthog_data
from integrations.stripe_writer import write_stripe_data
from integrations.supabase_writer import write_supabase_data
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('revops_writer', log_file='logs/revops_writer.log')


class RevOpsDataWriter:
    """Main orchestrator for writing RevOps data to all platforms"""

    def __init__(self):
        self.config = config
        self.results = {}
        self.errors = {}

    def write_hubspot(self, num_contacts: int = 15, num_companies: int = 8, num_deals: int = 12) -> Dict:
        """Write data to HubSpot"""
        logger.info("=" * 70)
        logger.info("HUBSPOT - Writing CRM Data")
        logger.info("=" * 70)

        try:
            if not self.config.hubspot:
                raise ValueError("HubSpot not configured. Set HUBSPOT_ACCESS_TOKEN in environment.")

            result = write_hubspot_data(
                access_token=self.config.hubspot.access_token,
                num_contacts=num_contacts,
                num_companies=num_companies,
                num_deals=num_deals
            )

            logger.info(f"✓ HubSpot write complete:")
            logger.info(f"  - Contacts:   {len(result['contacts'])}")
            logger.info(f"  - Companies:  {len(result['companies'])}")
            logger.info(f"  - Deals:      {len(result['deals'])}")
            logger.info(f"  - Advanced:   {result['deals_advanced']}")
            logger.info(f"  - Activities: {sum(result['activities'].values())} (calls={result['activities']['calls']}, meetings={result['activities']['meetings']}, emails={result['activities']['emails']})")
            logger.info(f"  - Errors:     {len(result['errors'])}")

            return result

        except Exception as e:
            logger.error(f"✗ HubSpot write failed: {e}")
            raise

    def write_stripe(self, num_customers: int = 15) -> Dict:
        """Write data to Stripe"""
        logger.info("=" * 70)
        logger.info("STRIPE - Writing Payment Data")
        logger.info("=" * 70)

        try:
            if not self.config.stripe:
                raise ValueError("Stripe not configured. Set STRIPE_SECRET_KEY in environment.")

            result = write_stripe_data(
                api_key=self.config.stripe.secret_key,
                num_customers=num_customers
            )

            logger.info(f"✓ Stripe write complete:")
            logger.info(f"  - Customers:      {len(result['customers'])}")
            logger.info(f"  - Subscriptions:  {len(result['subscriptions'])}")
            logger.info(f"  - Invoices (new): {len(result['invoice_history'])}")
            logger.info(f"  - Specific PMTs:  {len(result['payments'])}")

            return result

        except Exception as e:
            logger.error(f"✗ Stripe write failed: {e}")
            raise

    def write_supabase(self, num_companies: int = 40) -> Dict:
        """Write data to Supabase"""
        logger.info("=" * 70)
        logger.info("SUPABASE - Writing Database Records")
        logger.info("=" * 70)

        try:
            if not self.config.supabase:
                raise ValueError("Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.")

            result = write_supabase_data(
                url=self.config.supabase.url,
                service_key=self.config.supabase.service_key,
                num_companies=num_companies
            )

            logger.info(f"✓ Supabase write complete:")
            logger.info(f"  - Companies:        {result['companies']}")
            logger.info(f"  - Users:            {result['users']}")
            logger.info(f"  - Subscriptions:    {result['subscriptions']}")
            logger.info(f"  - Events:           {result['events']}")
            logger.info(f"  - Dim Date Rows:    {result['dim_date_rows']}")
            logger.info(f"  - Statuses Updated: {result.get('companies_updated', 0)}")

            return result

        except Exception as e:
            logger.error(f"✗ Supabase write failed: {e}")
            raise

    def write_mixpanel(self, num_users: int = 25, days_back: int = 30) -> Dict:
        """Write data to Mixpanel"""
        logger.info("=" * 70)
        logger.info("MIXPANEL - Writing Analytics Events")
        logger.info("=" * 70)

        try:
            if not self.config.mixpanel:
                raise ValueError("Mixpanel not configured. Set MIXPANEL_PROJECT_TOKEN and MIXPANEL_API_SECRET.")

            result = write_mixpanel_data(
                project_token=self.config.mixpanel.project_token,
                api_secret=self.config.mixpanel.api_secret,
                num_users=num_users,
                days_back=days_back
            )

            logger.info(f"✓ Mixpanel write complete:")
            logger.info(f"  - Events sent: {result['events_sent']}")
            logger.info(f"  - Profiles updated: {result['profiles_updated']}")
            logger.info(f"  - Date range: {result['date_range_days']} days")

            return result

        except Exception as e:
            logger.error(f"✗ Mixpanel write failed: {e}")
            raise

    def write_posthog(self, num_users: int = 25, days_back: int = 30) -> Dict:
        """Write data to PostHog"""
        logger.info("=" * 70)
        logger.info("POSTHOG - Writing Analytics Events")
        logger.info("=" * 70)

        try:
            if not self.config.posthog:
                raise ValueError("PostHog not configured. Set POSTHOG_API_KEY in environment.")

            result = write_posthog_data(
                api_key=self.config.posthog.api_key,
                host=self.config.posthog.host,
                num_users=num_users,
                days_back=days_back
            )

            logger.info(f"✓ PostHog write complete:")
            logger.info(f"  - Events sent: {result['events_sent']}")
            logger.info(f"  - Users identified: {result['users_identified']}")
            logger.info(f"  - Date range: {result['date_range_days']} days")

            return result

        except Exception as e:
            logger.error(f"✗ PostHog write failed: {e}")
            raise

    def write_freshdesk(self, ticket_count: int = 25) -> Dict:
        """Write data to Freshdesk"""
        logger.info("=" * 70)
        logger.info("FRESHDESK - Writing Support Tickets")
        logger.info("=" * 70)

        try:
            if not self.config.freshdesk:
                raise ValueError("Freshdesk not configured. Set FRESHDESK_DOMAIN and FRESHDESK_API_KEY.")

            result = write_freshdesk_data(
                domain=self.config.freshdesk.domain,
                api_key=self.config.freshdesk.api_key,
                ticket_count=ticket_count
            )

            logger.info(f"✓ Freshdesk write complete:")
            logger.info(f"  - Tickets created: {result['successful']}/{result['total_attempted']}")
            logger.info(f"  - Failed: {result['failed']}")

            return result

        except Exception as e:
            logger.error(f"✗ Freshdesk write failed: {e}")
            raise

    def write_meta_ads(self, num_events: int = 50, pixel_id: str = None, test_code: str = None) -> Dict:
        """Write data to Meta Ads"""
        logger.info("=" * 70)
        logger.info("META ADS - Writing Conversion Events")
        logger.info("=" * 70)

        try:
            if not self.config.meta_ads:
                raise ValueError("Meta Ads not configured. Set META_ACCESS_TOKEN and META_ACCOUNT_ID.")

            # For conversion events, we need pixel_id
            if not pixel_id:
                logger.warning("No pixel_id provided for Meta Ads. Skipping conversion events.")
                logger.info("To send conversion events, provide --meta-pixel-id flag")
                return {'status': 'skipped', 'reason': 'no_pixel_id'}

            result = write_sample_data_to_meta(
                access_token=self.config.meta_ads.access_token,
                pixel_id=pixel_id,
                test_event_code=test_code,
                num_events=num_events
            )

            logger.info(f"✓ Meta Ads write complete:")
            logger.info(f"  - Events sent: {result['total_events']}")
            logger.info(f"  - Batches: {result['batches_sent']}")

            return result

        except Exception as e:
            logger.error(f"✗ Meta Ads write failed: {e}")
            raise

    def write_all(self, services: List[str] = None, **kwargs) -> Dict:
        """
        Write data to all or specified services

        Args:
            services: List of service names (if None, writes to all configured)
            **kwargs: Additional arguments for specific services

        Returns:
            Dictionary with results for each service
        """
        logger.info("\n")
        logger.info("=" * 70)
        logger.info("REVOPS DATA WRITER - Starting")
        logger.info("=" * 70)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")

        # Determine which services to write to
        configured_services = self.config.get_configured_services()
        logger.info(f"Configured services: {', '.join(configured_services)}")

        if services:
            services_to_write = [s for s in services if s in configured_services]
            if not services_to_write:
                logger.error("None of the specified services are configured.")
                return {}
        else:
            services_to_write = configured_services

        logger.info(f"Writing to: {', '.join(services_to_write)}")
        logger.info("")

        # Write to each service
        for service in services_to_write:
            try:
                if service == 'hubspot':
                    self.results['hubspot'] = self.write_hubspot()
                elif service == 'stripe':
                    self.results['stripe'] = self.write_stripe()
                elif service == 'supabase':
                    self.results['supabase'] = self.write_supabase()
                elif service == 'mixpanel':
                    self.results['mixpanel'] = self.write_mixpanel()
                elif service == 'posthog':
                    self.results['posthog'] = self.write_posthog()
                elif service == 'freshdesk':
                    self.results['freshdesk'] = self.write_freshdesk()
                elif service == 'meta_ads':
                    pixel_id = kwargs.get('meta_pixel_id')
                    test_code = kwargs.get('meta_test_code')
                    self.results['meta_ads'] = self.write_meta_ads(
                        pixel_id=pixel_id,
                        test_code=test_code
                    )

                logger.info("")

            except Exception as e:
                self.errors[service] = str(e)
                logger.error(f"Failed to write to {service}: {e}")
                logger.info("")

        # Print summary
        self.print_summary()

        return self.results

    def print_summary(self):
        """Print final summary"""
        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)

        if self.results:
            logger.info(f"✓ Successfully wrote to {len(self.results)} service(s):")
            for service, result in self.results.items():
                logger.info(f"  • {service.upper()}")

        if self.errors:
            logger.info(f"\n✗ Failed to write to {len(self.errors)} service(s):")
            for service, error in self.errors.items():
                logger.info(f"  • {service.upper()}: {error}")

        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Write realistic B2B SaaS data to RevOps platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Write to all configured services
  python main_revops_writer.py --all

  # Write to specific services
  python main_revops_writer.py --services hubspot stripe

  # Write to Meta Ads with pixel ID
  python main_revops_writer.py --services meta_ads --meta-pixel-id 123456789 --meta-test-code TEST12345

  # Check which services are configured
  python main_revops_writer.py --check-config
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Write to all configured services'
    )

    parser.add_argument(
        '--services',
        nargs='+',
        choices=['hubspot', 'stripe', 'supabase', 'mixpanel', 'posthog', 'freshdesk', 'meta_ads'],
        help='Specific services to write to'
    )

    parser.add_argument(
        '--meta-pixel-id',
        type=str,
        help='Meta Ads Pixel ID (required for Meta Ads)'
    )

    parser.add_argument(
        '--meta-test-code',
        type=str,
        help='Meta Ads test event code (for sandbox testing)'
    )

    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Check which services are configured'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without actually writing data'
    )

    args = parser.parse_args()

    # Check configuration
    if args.check_config:
        logger.info("Checking configuration...")
        configured = config.get_configured_services()
        if configured:
            logger.info(f"Configured services: {', '.join(configured)}")
        else:
            logger.warning("No services configured. Set environment variables.")
        return

    # Dry run
    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be written")
        configured = config.get_configured_services()
        logger.info(f"Would write to: {', '.join(configured)}")
        return

    # Validate arguments
    if not args.all and not args.services:
        parser.error("Must specify either --all or --services")

    # Create writer and execute
    writer = RevOpsDataWriter()

    try:
        if args.all:
            writer.write_all(
                meta_pixel_id=args.meta_pixel_id,
                meta_test_code=args.meta_test_code
            )
        else:
            writer.write_all(
                services=args.services,
                meta_pixel_id=args.meta_pixel_id,
                meta_test_code=args.meta_test_code
            )

        # Exit with error code if any writes failed
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
