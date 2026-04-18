"""
PostHog Data Writer
Sends product analytics events to PostHog for B2B SaaS RevOps
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class PostHogWriter:
    """Writer for PostHog product analytics"""

    def __init__(self, api_key: str, host: str = "https://app.posthog.com"):
        """
        Initialize PostHog writer

        Args:
            api_key: PostHog project API key
            host: PostHog instance host URL
        """
        self.api_key = api_key
        self.host = host.rstrip('/')
        self.batch_url = f"{self.host}/batch/"
        self.capture_url = f"{self.host}/capture/"
        self.session = requests.Session()

    def _make_request(self, url: str, data: Dict) -> bool:
        """
        Make API request to PostHog

        Args:
            url: API endpoint URL
            data: Request payload

        Returns:
            True if successful
        """
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = self.session.post(url, json=data, headers=headers)
            response.raise_for_status()
            logger.debug(f"Successfully sent data to PostHog")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to PostHog: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def capture_event(
        self,
        distinct_id: str,
        event: str,
        properties: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Capture a single event

        Args:
            distinct_id: User identifier
            event: Event name
            properties: Event properties
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if successful
        """
        if properties is None:
            properties = {}

        if timestamp is None:
            timestamp = datetime.now()

        payload = {
            'api_key': self.api_key,
            'event': event,
            'distinct_id': distinct_id,
            'properties': properties,
            'timestamp': timestamp.isoformat()
        }

        logger.debug(f"Capturing event '{event}' for user {distinct_id}")
        return self._make_request(self.capture_url, payload)

    def capture_batch(self, events: List[Dict]) -> bool:
        """
        Capture multiple events in batch

        Args:
            events: List of event dictionaries

        Returns:
            True if successful
        """
        batch_payload = {
            'api_key': self.api_key,
            'batch': events
        }

        logger.info(f"Sending batch of {len(events)} events to PostHog")
        return self._make_request(self.batch_url, batch_payload)

    def identify_user(
        self,
        distinct_id: str,
        properties: Dict
    ) -> bool:
        """
        Set user properties

        Args:
            distinct_id: User identifier
            properties: User properties

        Returns:
            True if successful
        """
        payload = {
            'api_key': self.api_key,
            'event': '$identify',
            'distinct_id': distinct_id,
            'properties': properties,
            'timestamp': datetime.now().isoformat()
        }

        logger.debug(f"Identifying user {distinct_id}")
        return self._make_request(self.capture_url, payload)

    def set_user_properties(
        self,
        distinct_id: str,
        properties: Dict
    ) -> bool:
        """
        Set properties for a user (alias for identify_user)

        Args:
            distinct_id: User identifier
            properties: User properties to set

        Returns:
            True if successful
        """
        # Add $set wrapper for property updates
        properties_with_set = {
            '$set': properties
        }

        payload = {
            'api_key': self.api_key,
            'event': '$identify',
            'distinct_id': distinct_id,
            'properties': properties_with_set,
            'timestamp': datetime.now().isoformat()
        }

        logger.debug(f"Setting properties for user {distinct_id}")
        return self._make_request(self.capture_url, payload)


def generate_sample_posthog_events(num_users: int = 25, days_back: int = 30) -> tuple:
    """
    Generate realistic B2B SaaS product analytics events for PostHog

    Args:
        num_users: Number of unique users to simulate
        days_back: Number of days of historical data

    Returns:
        Tuple of (events list, user properties list)
    """
    events = []
    user_properties = []

    companies = ['Acme Corp', 'TechStart Inc', 'DataFlow LLC', 'CloudNine Co', 'DevOps Pro', 'ScaleUp Ltd']
    plans = ['free', 'starter', 'professional', 'enterprise']
    roles = ['admin', 'user', 'manager', 'developer', 'analyst']

    # Feature categories
    features = {
        'dashboard': ['overview', 'metrics', 'graphs', 'filters'],
        'reports': ['create', 'export', 'schedule', 'share'],
        'integrations': ['connect', 'sync', 'disconnect', 'configure'],
        'team': ['invite', 'remove', 'permissions', 'settings'],
        'api': ['generate_key', 'view_docs', 'test_endpoint', 'rate_limits'],
        'settings': ['profile', 'billing', 'notifications', 'security']
    }

    for user_idx in range(num_users):
        user_id = f"user_{uuid.uuid4()}"
        email = f"user{user_idx}@example{user_idx % 5}.com"
        company = random.choice(companies)
        plan = random.choice(plans)
        role = random.choice(roles)

        signup_date = datetime.now() - timedelta(days=random.randint(1, days_back))

        # User properties
        user_properties.append({
            'distinct_id': user_id,
            'properties': {
                'email': email,
                'name': f'User {user_idx}',
                'company': company,
                'plan': plan,
                'role': role,
                'signup_date': signup_date.isoformat(),
                'team_size': random.randint(1, 50),
                'industry': random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing']),
                'country': random.choice(['US', 'UK', 'CA', 'AU', 'DE'])
            }
        })

        # Signup event
        events.append({
            'event': 'User Signed Up',
            'distinct_id': user_id,
            'properties': {
                'email': email,
                'company': company,
                'plan': plan,
                'signup_source': random.choice(['organic', 'paid_ad', 'referral', 'direct']),
                'trial_days': 14 if plan != 'free' else 0
            },
            'timestamp': signup_date.isoformat()
        })

        # Onboarding events
        if random.random() > 0.3:  # 70% complete onboarding
            onboarding_time = signup_date + timedelta(minutes=random.randint(5, 60))
            events.append({
                'event': 'Onboarding Completed',
                'distinct_id': user_id,
                'properties': {
                    'steps_completed': random.randint(3, 7),
                    'time_taken_minutes': random.randint(5, 60),
                    'skipped_steps': random.randint(0, 2)
                },
                'timestamp': onboarding_time.isoformat()
            })

        # Activity over time
        current_date = signup_date + timedelta(days=1)
        while current_date < datetime.now():
            # Random activity (not every day)
            if random.random() < 0.6:  # 60% chance of activity each day
                sessions_today = random.randint(1, 5)

                for session in range(sessions_today):
                    session_start = current_date + timedelta(
                        hours=random.randint(8, 20),
                        minutes=random.randint(0, 59)
                    )

                    # Session start
                    events.append({
                        'event': 'Session Started',
                        'distinct_id': user_id,
                        'properties': {
                            'company': company,
                            'plan': plan,
                            'device': random.choice(['desktop', 'mobile', 'tablet']),
                            'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                            'os': random.choice(['Windows', 'macOS', 'Linux', 'iOS', 'Android'])
                        },
                        'timestamp': session_start.isoformat()
                    })

                    # Feature usage during session
                    num_actions = random.randint(3, 15)
                    for action_idx in range(num_actions):
                        action_time = session_start + timedelta(minutes=action_idx * 2)

                        # Pick random feature category and action
                        category = random.choice(list(features.keys()))
                        action = random.choice(features[category])

                        events.append({
                            'event': 'Feature Used',
                            'distinct_id': user_id,
                            'properties': {
                                'feature_category': category,
                                'feature_action': action,
                                'feature_name': f"{category}_{action}",
                                'company': company,
                                'plan': plan,
                                'session_duration_minutes': random.randint(5, 45)
                            },
                            'timestamp': action_time.isoformat()
                        })

                    # Occasional specific events
                    if random.random() > 0.7:
                        events.append({
                            'event': 'Report Generated',
                            'distinct_id': user_id,
                            'properties': {
                                'report_type': random.choice(['revenue', 'users', 'engagement', 'retention']),
                                'export_format': random.choice(['pdf', 'csv', 'excel']),
                                'date_range': random.choice(['7d', '30d', '90d', 'custom']),
                                'filters_applied': random.randint(0, 5)
                            },
                            'timestamp': (session_start + timedelta(minutes=random.randint(10, 30))).isoformat()
                        })

            current_date += timedelta(days=1)

        # Subscription events
        if plan != 'free' and random.random() > 0.4:
            sub_date = signup_date + timedelta(days=15)
            events.append({
                'event': 'Subscription Started',
                'distinct_id': user_id,
                'properties': {
                    'plan': plan,
                    'billing_interval': random.choice(['monthly', 'annual']),
                    'amount': {'starter': 49, 'professional': 149, 'enterprise': 499}[plan],
                    'currency': 'USD'
                },
                'timestamp': sub_date.isoformat()
            })

        # Occasional support interactions
        if random.random() > 0.7:
            support_date = signup_date + timedelta(days=random.randint(1, days_back))
            events.append({
                'event': 'Support Ticket Created',
                'distinct_id': user_id,
                'properties': {
                    'category': random.choice(['technical', 'billing', 'feature_request', 'question']),
                    'priority': random.choice(['low', 'medium', 'high']),
                    'channel': random.choice(['email', 'chat', 'phone'])
                },
                'timestamp': support_date.isoformat()
            })

    logger.info(f"Generated {len(events)} PostHog events for {num_users} users")
    return events, user_properties


def write_posthog_data(
    api_key: str,
    host: str = "https://app.posthog.com",
    num_users: int = 25,
    days_back: int = 30
) -> Dict:
    """
    Write sample data to PostHog

    Args:
        api_key: PostHog project API key
        host: PostHog instance host
        num_users: Number of users to simulate
        days_back: Days of historical data

    Returns:
        Summary statistics
    """
    logger.info("Starting PostHog data write")

    writer = PostHogWriter(api_key, host)

    # Generate sample data
    events, user_properties = generate_sample_posthog_events(num_users, days_back)

    # Send user properties first
    successful_users = 0
    for user_prop in user_properties:
        if writer.identify_user(user_prop['distinct_id'], user_prop['properties']):
            successful_users += 1

    logger.info(f"Identified {successful_users}/{len(user_properties)} users")

    # Send events in batches
    batch_size = 100
    successful_events = 0

    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        if writer.capture_batch(batch):
            successful_events += len(batch)
            logger.info(f"Sent batch {i//batch_size + 1}: {len(batch)} events")

    summary = {
        'service': 'posthog',
        'events_sent': successful_events,
        'users_identified': successful_users,
        'total_users': num_users,
        'date_range_days': days_back,
        'timestamp': datetime.now().isoformat()
    }

    logger.info(f"PostHog data write complete: {successful_events} events, {successful_users} users")
    return summary
