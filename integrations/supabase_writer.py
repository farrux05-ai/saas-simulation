"""
Supabase Data Writer
Populates Supabase with realistic B2B SaaS data for testing
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, TYPE_CHECKING, Optional

from supabase import Client, create_client

from utils.logger import get_logger

if TYPE_CHECKING:
    from utils.simulation_context import SimulationContext

logger = get_logger(__name__)


class SupabaseWriter:
    """Writer for populating Supabase with sample RevOps data"""

    def __init__(self, url: str, service_key: str):
        """
        Initialize Supabase writer

        Args:
            url: Supabase project URL
            service_key: Supabase service key (for admin access)
        """
        self.url = url
        self.service_key = service_key
        self.client: Client = create_client(url, service_key)

    def create_tables(self):
        """Create necessary tables in Supabase"""
        logger.info("Creating Supabase tables...")

        # Note: In production, you'd use SQL migrations
        # This is a simplified approach for sandbox/testing

        tables_sql = """
        -- Companies table
        CREATE TABLE IF NOT EXISTS companies (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name TEXT NOT NULL,
            domain TEXT UNIQUE,
            industry TEXT,
            employee_count INTEGER,
            annual_revenue DECIMAL,
            plan_type TEXT,
            mrr DECIMAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID REFERENCES companies(id),
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            role TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            last_login_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        -- Events table
        CREATE TABLE IF NOT EXISTS events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id),
            company_id UUID REFERENCES companies(id),
            event_name TEXT NOT NULL,
            event_type TEXT,
            properties JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Subscriptions table
        CREATE TABLE IF NOT EXISTS subscriptions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID REFERENCES companies(id),
            plan_name TEXT NOT NULL,
            status TEXT NOT NULL,
            mrr DECIMAL,
            billing_cycle TEXT,
            started_at TIMESTAMP,
            ends_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        -- Calendar dimension table (required for all time-based dbt models)
        CREATE TABLE IF NOT EXISTS dim_date (
            date_day      DATE PRIMARY KEY,
            year          INTEGER,
            month         INTEGER,
            day           INTEGER,
            quarter       INTEGER,
            week_of_year  INTEGER,
            day_of_week   INTEGER,   -- 0=Monday, 6=Sunday
            day_name      TEXT,
            month_name    TEXT,
            is_weekend    BOOLEAN,
            is_month_end  BOOLEAN,
            is_quarter_end BOOLEAN
        );
        """

        try:
            # Execute via RPC or direct SQL
            logger.info("Tables structure defined (execute via Supabase SQL editor)")
            logger.info("SQL for manual execution provided in code comments")
        except Exception as e:
            logger.warning(f"Table creation note: {e}")

    def insert_companies(self, count: int = 50, context: Optional['SimulationContext'] = None) -> List[Dict]:
        """
        Insert sample companies

        Args:
            count: Number of companies to create
            context: Persona definitions

        Returns:
            List of created companies
        """
        logger.info(f"Inserting {count} companies...")

        industries = ['SaaS', 'E-commerce', 'FinTech', 'HealthTech', 'EdTech', 'MarTech']
        plans = ['Free', 'Starter', 'Professional', 'Enterprise']
        statuses = ['Active', 'Trial', 'Churned', 'At Risk']

        companies = []
        
        try:
            existing = self.client.table('companies').select('id, domain').execute()
            domain_to_id = {row['domain']: row['id'] for row in existing.data}
        except Exception:
            domain_to_id = {}
        
        # --- FIXED PERSONAS ---
        if context:
            for p in context.fixed_personas:
                # Map specific lifecycle to Supabase status
                status = 'Active'
                if p.lifecycle_stage == 'at_risk': status = 'At Risk'
                elif p.lifecycle_stage == 'stalled': status = 'Trial'
                elif p.lifecycle_stage == 'churned': status = 'Churned'
                elif p.lifecycle_stage == 'new_lead': status = 'Trial'
                
                companies.append({
                    'id': domain_to_id.get(p.domain) or str(uuid.uuid4()),
                    'name': p.company_name,
                    'domain': p.domain,
                    'industry': random.choice(industries),
                    'employee_count': random.choice([10, 25, 50, 100, 250, 500, 1000]),
                    'annual_revenue': round(random.uniform(100000, 10000000), 2),
                    'plan_type': p.plan_name.capitalize(),
                    'mrr': float(p.mrr),
                    'status': status,
                    'created_at': (datetime.now() - timedelta(days=90)).isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
        
        # --- RANDOM EXTRAS ---
        num_random = max(0, count - len(companies))
        for i in range(num_random):
            domain = f"company{i+1}-{uuid.uuid4().hex[:4]}.com"
            companies.append({
                'id': domain_to_id.get(domain) or str(uuid.uuid4()),
                'name': f"Company {i+1} Inc",
                'domain': domain,
                'industry': random.choice(industries),
                'employee_count': random.choice([10, 25, 50, 100, 250, 500, 1000]),
                'annual_revenue': round(random.uniform(100000, 10000000), 2),
                'plan_type': random.choice(plans),
                'mrr': round(random.uniform(99, 9999), 2),
                'status': random.choice(statuses),
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 730))).isoformat(),
                'updated_at': datetime.now().isoformat()
            })

        try:
            response = self.client.table('companies').upsert(companies, on_conflict='domain').execute()
            logger.info(f"Successfully inserted {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"Failed to insert companies: {e}")
            raise

    def insert_users(self, companies: List[Dict], users_per_company: int = 5) -> List[Dict]:
        """
        Insert sample users

        Args:
            companies: List of companies to create users for
            users_per_company: Average users per company

        Returns:
            List of created users
        """
        logger.info(f"Inserting users for {len(companies)} companies...")

        roles = ['Admin', 'User', 'Manager', 'Developer', 'Analyst']
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Chris', 'Anna']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller']

        try:
            existing = self.client.table('users').select('id, email').execute()
            email_to_id = {row['email']: row['id'] for row in existing.data}
        except Exception:
            email_to_id = {}

        users = []
        for company in companies:
            num_users = random.randint(1, users_per_company * 2)
            for i in range(num_users):
                first = random.choice(first_names)
                last = random.choice(last_names)
                email = f"{first.lower()}.{last.lower()}{i}@{company['domain']}"
                user = {
                    'id': email_to_id.get(email) or str(uuid.uuid4()),
                    'company_id': company['id'],
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': random.choice(roles),
                    'is_active': random.choice([True, True, True, False]),  # 75% active
                    'last_login_at': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    'created_at': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                users.append(user)

        try:
            # Insert in batches to avoid payload limits
            batch_size = 100
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]
                self.client.table('users').upsert(batch, on_conflict='email').execute()
                logger.info(f"Inserted batch {i//batch_size + 1} ({len(batch)} users)")

            logger.info(f"Successfully inserted {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Failed to insert users: {e}")
            raise

    def insert_events(self, users: List[Dict], companies: List[Dict], events_per_user: int = 20) -> List[Dict]:
        """
        Insert sample events

        Args:
            users: List of users
            companies: List of companies
            events_per_user: Average events per user

        Returns:
            List of created events
        """
        logger.info(f"Inserting events for {len(users)} users...")

        event_types = [
            'page_view', 'button_click', 'feature_used', 'report_generated',
            'setting_changed', 'file_uploaded', 'dashboard_viewed', 'search_performed',
            'export_data', 'invite_sent', 'integration_connected', 'api_call'
        ]

        events = []
        for user in users[:100]:  # Limit to avoid too many events
            num_events = random.randint(5, events_per_user)
            for _ in range(num_events):
                event = {
                    'id': str(uuid.uuid4()),
                    'user_id': user['id'],
                    'company_id': user['company_id'],
                    'event_name': random.choice(event_types),
                    'event_type': 'user_action',
                    'properties': {
                        'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                        'platform': random.choice(['Web', 'Mobile', 'Desktop']),
                        'duration_seconds': random.randint(5, 300),
                        'value': round(random.uniform(1, 100), 2)
                    },
                    'created_at': (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat()
                }
                events.append(event)

        try:
            # Insert in batches
            batch_size = 100
            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]
                self.client.table('events').insert(batch).execute()
                logger.info(f"Inserted batch {i//batch_size + 1} ({len(batch)} events)")

            logger.info(f"Successfully inserted {len(events)} events")
            return events
        except Exception as e:
            logger.error(f"Failed to insert events: {e}")
            raise

    def insert_subscriptions(self, companies: List[Dict]) -> List[Dict]:
        """
        Insert sample subscriptions

        Args:
            companies: List of companies

        Returns:
            List of created subscriptions
        """
        logger.info(f"Inserting subscriptions for {len(companies)} companies...")

        plans = [
            {'name': 'Free', 'mrr': 0, 'cycle': 'monthly'},
            {'name': 'Starter', 'mrr': 49, 'cycle': 'monthly'},
            {'name': 'Professional', 'mrr': 199, 'cycle': 'monthly'},
            {'name': 'Enterprise', 'mrr': 999, 'cycle': 'annual'}
        ]
        statuses = ['active', 'trialing', 'past_due', 'canceled']

        subscriptions = []
        for company in companies:
            plan = random.choice(plans)
            status = random.choice(statuses) if company['status'] != 'Churned' else 'canceled'

            subscription = {
                'id': str(uuid.uuid4()),
                'company_id': company['id'],
                'plan_name': plan['name'],
                'status': status,
                'mrr': plan['mrr'],
                'billing_cycle': plan['cycle'],
                'started_at': (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
                'ends_at': (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat() if status == 'active' else None,
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            subscriptions.append(subscription)

        try:
            response = self.client.table('subscriptions').insert(subscriptions).execute()
            logger.info(f"Successfully inserted {len(subscriptions)} subscriptions")
            return subscriptions
        except Exception as e:
            logger.error(f"Failed to insert subscriptions: {e}")
            raise

    def insert_dim_date(self, years_back: int = 2, years_forward: int = 1) -> int:
        """
        Populate a dim_date (calendar) table covering a date range.
        This is a standard fact in every data warehouse — all time-based
        dbt models join against it.

        Args:
            years_back: How many years in the past to cover
            years_forward: How many years in the future to cover

        Returns:
            Number of date rows inserted
        """
        logger.info(f"Populating dim_date ({years_back}y back → {years_forward}y forward)...")

        start_date = datetime.now().date() - timedelta(days=365 * years_back)
        end_date   = datetime.now().date() + timedelta(days=365 * years_forward)

        rows = []
        current = start_date
        while current <= end_date:
            rows.append({
                'date_day':      current.isoformat(),
                'year':          current.year,
                'month':         current.month,
                'day':           current.day,
                'quarter':       (current.month - 1) // 3 + 1,
                'week_of_year':  current.isocalendar()[1],
                'day_of_week':   current.weekday(),          # 0=Mon … 6=Sun
                'day_name':      current.strftime('%A'),
                'month_name':    current.strftime('%B'),
                'is_weekend':    current.weekday() >= 5,
                'is_month_end':  (current + timedelta(days=1)).month != current.month,
                'is_quarter_end': (
                    current.month in (3, 6, 9, 12)
                    and (current + timedelta(days=1)).month != current.month
                ),
            })
            current += timedelta(days=1)

        try:
            # Upsert in batches — safe to run multiple times
            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                self.client.table('dim_date').upsert(batch, on_conflict='date_day').execute()

            logger.info(f"dim_date populated: {len(rows)} rows")
            return len(rows)
        except Exception as e:
            logger.error(f"Failed to populate dim_date: {e}")
            raise

    def populate_all(self, num_companies: int = 50, context: Optional['SimulationContext'] = None) -> Dict[str, int]:
        """
        Run full population workflow

        Args:
            num_companies: Number of companies to generate
            context: Persona context

        Returns:
            Dictionary with counts of created records
        """
        logger.info("Starting Supabase data population...")

        try:
            # Create tables (structure)
            self.create_tables()

            # Populate the date dimension first (idempotent — safe to run every time)
            dim_date_rows = self.insert_dim_date()

            # Insert transactional data
            companies     = self.insert_companies(count=num_companies, context=context)
            users         = self.insert_users(companies, users_per_company=5)
            events        = self.insert_events(users, companies, events_per_user=20)
            subscriptions = self.insert_subscriptions(companies)

            summary = {
                'dim_date_rows': dim_date_rows,
                'companies':     len(companies),
                'users':         len(users),
                'events':        len(events),
                'subscriptions': len(subscriptions),
            }

            logger.info(f"Successfully populated Supabase: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Failed to populate Supabase: {e}")
            raise

    def update_company_statuses(self) -> int:
        """
        Randomly advance statuses of existing companies to simulate real-world churn
        and upgrades. This creates meaningful deltas for dbt snapshot (SCD Type 2) testing.

        Returns:
            Number of companies updated
        """
        logger.info("Updating existing company statuses...")

        # Status lifecycle: Trial → Active → At Risk → Churned
        transitions = {
            'Trial':    ['Active', 'Churned'],
            'Active':   ['Active', 'Active', 'Active', 'At Risk'],  # 75% stay active
            'At Risk':  ['At Risk', 'Churned', 'Active'],
            'Churned':  ['Churned'],  # Terminal state
        }

        plan_upgrades = {
            'Free':         'Starter',
            'Starter':      'Professional',
            'Professional': 'Enterprise',
            'Enterprise':   'Enterprise',
        }

        try:
            response = self.client.table('companies').select('id,status,plan_type').execute()
            companies = response.data

            if not companies:
                logger.info("No existing companies found to update")
                return 0

            # Update ~30% of companies
            to_update = random.sample(companies, max(1, len(companies) // 3))

            updated = 0
            for company in to_update:
                current_status = company.get('status', 'Active')
                current_plan = company.get('plan_type', 'Starter')

                new_status = random.choice(transitions.get(current_status, ['Active']))

                # 20% chance of plan upgrade
                new_plan = plan_upgrades.get(current_plan, current_plan) \
                    if random.random() < 0.2 else current_plan

                self.client.table('companies').update({
                    'status':     new_status,
                    'plan_type':  new_plan,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', company['id']).execute()

                updated += 1

            logger.info(f"Updated {updated} company statuses")
            return updated

        except Exception as e:
            logger.error(f"Failed to update company statuses: {e}")
            raise



def write_supabase_data(url: str, service_key: str, num_companies: int = 30, context: Optional['SimulationContext'] = None) -> Dict[str, int]:
    """
    Main function to write data to Supabase.
    Inserts new records AND updates existing company statuses for snapshot testing.

    Args:
        url: Supabase URL
        service_key: Supabase service key
        num_companies: Number of new companies to create each run
        context: Simulation personas

    Returns:
        Summary of created and updated records
    """
    writer = SupabaseWriter(url, service_key)
    result = writer.populate_all(num_companies, context=context)

    # Also update existing statuses to generate snapshot deltas
    updated = writer.update_company_statuses()
    result['companies_updated'] = updated

    return result
