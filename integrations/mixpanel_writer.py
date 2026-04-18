"""
Mixpanel Data Writer
Sends product analytics events to Mixpanel for B2B SaaS RevOps
"""

import base64
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class MixpanelWriter:
    """Write events and user profiles to Mixpanel"""

    def __init__(self, project_token: str, api_secret: str):
        """
        Initialize Mixpanel writer

        Args:
            project_token: Mixpanel project token
            api_secret: Mixpanel API secret
        """
        self.project_token = project_token
        self.api_secret = api_secret
        self.import_url = "https://api.mixpanel.com/import"
        self.engage_url = "https://api.mixpanel.com/engage"
        self.session = requests.Session()

    def _get_auth_header(self) -> Dict:
        """Get authorization header"""
        credentials = f"{self.api_secret}:"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    def send_event(self, event_name: str, distinct_id: str, properties: Dict = None) -> bool:
        """
        Send a single event to Mixpanel

        Args:
            event_name: Name of the event
            distinct_id: User identifier
            properties: Event properties

        Returns:
            True if successful
        """
        if properties is None:
            properties = {}

        properties['token'] = self.project_token
        properties['distinct_id'] = distinct_id
        properties['time'] = int(datetime.now().timestamp())

        event = {
            'event': event_name,
            'properties': properties
        }

        try:
            response = self.session.post(
                self.import_url,
                params={'strict': '1'},
                headers=self._get_auth_header(),
                json=[event]
            )
            response.raise_for_status()
            logger.debug(f"Sent event '{event_name}' for user {distinct_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send event to Mixpanel: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response Body: {e.response.text}")
            return False

    def send_events_batch(self, events: List[Dict]) -> bool:
        """
        Send multiple events in batch

        Args:
            events: List of event dictionaries

        Returns:
            True if successful
        """
        formatted_events = []
        for event in events:
            properties = event.get('properties', {})
            properties['token'] = self.project_token

            formatted_events.append({
                'event': event['event'],
                'properties': properties
            })

        try:
            response = self.session.post(
                self.import_url,
                params={'strict': '1'},
                headers=self._get_auth_header(),
                json=formatted_events
            )
            response.raise_for_status()
            logger.info(f"Sent {len(events)} events to Mixpanel")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send batch events: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response Body: {e.response.text}")
            return False

    def update_user_profile(self, distinct_id: str, properties: Dict) -> bool:
        """
        Update user profile properties

        Args:
            distinct_id: User identifier
            properties: Profile properties to set

        Returns:
            True if successful
        """
        profile_update = {
            '$token': self.project_token,
            '$distinct_id': distinct_id,
            '$set': properties
        }

        try:
            response = self.session.post(
                self.engage_url,
                params={'verbose': '1'},
                headers=self._get_auth_header(),
                json=[profile_update]
            )
            response.raise_for_status()
            logger.debug(f"Updated profile for user {distinct_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update user profile: {e}")
            return False


def generate_sample_events(num_users: int = 20, days_back: int = 30) -> List[Dict]:
    """
    Generate realistic B2B SaaS product analytics events

    Args:
        num_users: Number of unique users to simulate
        days_back: Number of days of historical data

    Returns:
        List of event dictionaries
    """
    events = []

    companies = ['Acme Corp', 'TechStart Inc', 'DataFlow LLC', 'CloudNine Co', 'DevOps Pro']
    plans = ['starter', 'professional', 'enterprise']
    features = ['dashboard', 'reports', 'integrations', 'api', 'team_management', 'analytics']

    user_ids = [f"user_{i}@example.com" for i in range(num_users)]

    for user_id in user_ids:
        company = random.choice(companies)
        plan = random.choice(plans)
        signup_date = datetime.now() - timedelta(days=random.randint(1, days_back))

        # --- MARKETING SIGNALS (Pre-Signup behavior) ---
        # Simulate a lead journey before they actually sign up
        marketing_date = signup_date - timedelta(days=random.randint(1, 7))

        # 1. Page Viewed (Discovery)
        events.append({
            'event': 'Page Viewed',
            'properties': {
                'distinct_id': user_id,
                '$insert_id': uuid.uuid4().hex,
                'time': int(marketing_date.timestamp()),
                'path': '/',
                'source': random.choice(['Google', 'LinkedIn', 'Direct', 'Meta Ads']),
                'company': company
            }
        })

        # 2. Pricing Page Viewed (Interest)
        events.append({
            'event': 'Pricing Page Viewed',
            'properties': {
                'distinct_id': user_id,
                '$insert_id': uuid.uuid4().hex,
                'time': int((marketing_date + timedelta(hours=2)).timestamp()),
                'plan_seen': plan,
                'company': company
            }
        })

        # 3. Demo Requested (Intent - The MQL Signal)
        if random.random() > 0.3:  # 70% of our sample users requested a demo
            events.append({
                'event': 'Demo Requested',
                'properties': {
                    'distinct_id': user_id,
                    '$insert_id': uuid.uuid4().hex,
                    'time': int((marketing_date + timedelta(days=1)).timestamp()),
                    'company': company
                }
            })

        # --- PRODUCT DATA (The Signup) ---
        # Ensure signup is at least 1 hour in the past to avoid clock drift issues
        signup_date_safe = signup_date - timedelta(hours=1)

        events.append({
            'event': 'User Signup',
            'properties': {
                'distinct_id': user_id,
                '$insert_id': uuid.uuid4().hex,
                'time': int(signup_date_safe.timestamp()),
                'email': user_id,
                'company': company,
                'plan': plan,
                'signup_source': random.choice(['website', 'referral', 'organic', 'paid_ads']),
                'trial_days': 14
            }
        })

        # Simulate activity over time
        current_date = signup_date_safe
        # End simulation at the end of yesterday to stay far away from 'future time' validation
        end_limit = (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59)

        while current_date < end_limit:
            # Random number of sessions per day (0-5)
            sessions = random.randint(0, 5)

            for _ in range(sessions):
                # Randomize session hour but stay within that day
                session_time = current_date + timedelta(hours=random.randint(0, 23))
                
                # Double check against end_limit to avoid any 'future' drift
                if session_time > end_limit:
                    session_time = end_limit

                # Login
                events.append({
                    'event': 'User Login',
                    'properties': {
                        'distinct_id': user_id,
                        '$insert_id': uuid.uuid4().hex,
                        'time': int(session_time.timestamp()),
                        'company': company,
                        'plan': plan
                    }
                })

                # Feature usage (2-8 per session)
                for _ in range(random.randint(2, 8)):
                    feature = random.choice(features)
                    # Stay within the session window (max 1 hour after login)
                    feature_time = min(
                        int(session_time.timestamp()) + random.randint(60, 3600),
                        int(end_limit.timestamp())
                    )
                    events.append({
                        'event': 'Feature Used',
                        'properties': {
                            'distinct_id': user_id,
                            '$insert_id': uuid.uuid4().hex,
                            'time': feature_time,
                            'feature_name': feature,
                            'company': company,
                            'plan': plan,
                            'duration_seconds': random.randint(30, 600)
                        }
                    })

            current_date += timedelta(days=1)

        # Occasional billing events
        if random.random() > 0.5:
            # Cap billing date to yesterday
            billing_date = min(
                signup_date_safe + timedelta(days=15),
                end_limit
            )
            events.append({
                'event': 'Subscription Created',
                'properties': {
                    'distinct_id': user_id,
                    '$insert_id': uuid.uuid4().hex,
                    'time': int(billing_date.timestamp()),
                    'company': company,
                    'plan': plan,
                    'amount': {'starter': 29, 'professional': 99, 'enterprise': 299}[plan],
                    'currency': 'USD',
                    'billing_interval': 'monthly'
                }
            })

    logger.info(f"Generated {len(events)} sample events for {num_users} users")
    return events


def generate_user_profiles(num_users: int = 20) -> List[Dict]:
    """
    Generate user profile data

    Args:
        num_users: Number of users

    Returns:
        List of profile dictionaries
    """
    profiles = []
    companies = ['Acme Corp', 'TechStart Inc', 'DataFlow LLC', 'CloudNine Co', 'DevOps Pro']
    roles = ['Admin', 'User', 'Manager', 'Developer', 'Analyst']
    plans = ['starter', 'professional', 'enterprise']

    for i in range(num_users):
        user_id = f"user_{i}@example.com"
        profiles.append({
            'distinct_id': user_id,
            'properties': {
                '$email': user_id,
                '$name': f"User {i}",
                '$created': datetime.now().isoformat(),
                'company': random.choice(companies),
                'role': random.choice(roles),
                'plan': random.choice(plans),
                'team_size': random.randint(1, 50),
                'industry': random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing'])
            }
        })

    return profiles


def write_mixpanel_data(
    project_token: str,
    api_secret: str,
    num_users: int = 20,
    days_back: int = 30
) -> Dict:
    """
    Write sample data to Mixpanel

    Args:
        project_token: Mixpanel project token
        api_secret: Mixpanel API secret
        num_users: Number of users to simulate
        days_back: Days of historical data

    Returns:
        Summary statistics
    """
    logger.info("Starting Mixpanel data write")

    writer = MixpanelWriter(project_token, api_secret)

    # Generate and send events
    events = generate_sample_events(num_users, days_back)

    # Send in batches of 50
    batch_size = 50
    successful_events = 0

    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        if writer.send_events_batch(batch):
            successful_events += len(batch)

    # Generate and update user profiles
    profiles = generate_user_profiles(num_users)
    successful_profiles = 0

    for profile in profiles:
        if writer.update_user_profile(profile['distinct_id'], profile['properties']):
            successful_profiles += 1

    summary = {
        'service': 'mixpanel',
        'events_sent': successful_events,
        'profiles_updated': successful_profiles,
        'total_users': num_users,
        'date_range_days': days_back,
        'timestamp': datetime.now().isoformat()
    }

    logger.info(f"Mixpanel data write complete: {successful_events} events, {successful_profiles} profiles")
    return summary
