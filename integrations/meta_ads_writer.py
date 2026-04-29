"""
Meta Ads Data Writer
Sends conversion events and leads to Meta Ads for testing/sandbox
"""

import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class MetaAdsWriter:















    """Writer for Meta Ads Conversions API"""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str, pixel_id: str, test_event_code: Optional[str] = None):
        """
        Initialize Meta Ads writer

        Args:
            access_token: Meta API access token
            pixel_id: Facebook Pixel ID
            test_event_code: Test event code for sandbox testing
        """
        self.access_token = access_token
        self.pixel_id = pixel_id
        self.test_event_code = test_event_code
        self.session = requests.Session()

    def _hash_data(self, data: str) -> str:
        """Hash data with SHA256 for user data"""
        if not data:
            return None
        return hashlib.sha256(data.lower().strip().encode()).hexdigest()

    def send_conversion_event(
        self,
        event_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        value: Optional[float] = None,
        currency: str = "USD",
        event_source_url: Optional[str] = None,
        custom_data: Optional[Dict] = None,
        event_time: Optional[int] = None
    ) -> Dict:
        """
        Send a conversion event to Meta

        Args:
            event_name: Event name (e.g., 'Purchase', 'Lead', 'CompleteRegistration')
            email: User email
            phone: User phone
            first_name: User first name
            last_name: User last name
            value: Conversion value
            currency: Currency code
            event_source_url: Source URL
            custom_data: Additional custom data
            event_time: Unix timestamp (defaults to now)

        Returns:
            API response
        """
        if event_time is None:
            event_time = int(time.time())

        # Build user data
        user_data = {}
        if email:
            user_data['em'] = self._hash_data(email)
        if phone:
            user_data['ph'] = self._hash_data(phone)
        if first_name:
            user_data['fn'] = self._hash_data(first_name)
        if last_name:
            user_data['ln'] = self._hash_data(last_name)

        # Build event data
        event_data = {
            'event_name': event_name,
            'event_time': event_time,
            'action_source': 'website',
            'user_data': user_data
        }

        if event_source_url:
            event_data['event_source_url'] = event_source_url

        # Add custom data
        if value or custom_data:
            custom = {}
            if value:
                custom['value'] = value
                custom['currency'] = currency
            if custom_data:
                custom.update(custom_data)
            event_data['custom_data'] = custom

        # Build request payload
        payload = {
            'data': [event_data],
            'access_token': self.access_token
        }

        # Add test event code if provided
        if self.test_event_code:
            payload['test_event_code'] = self.test_event_code

        url = f"{self.BASE_URL}/{self.pixel_id}/events"

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Sent conversion event '{event_name}' to Meta Ads")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send conversion event: {e}")
            raise

    def send_batch_events(self, events: List[Dict]) -> Dict:
        """
        Send multiple conversion events in batch

        Args:
            events: List of event dictionaries

        Returns:
            API response
        """
        # Process events to hash user data
        processed_events = []
        for event in events:
            user_data = event.get('user_data', {})
            hashed_user_data = {}

            if 'email' in user_data:
                hashed_user_data['em'] = self._hash_data(user_data['email'])
            if 'phone' in user_data:
                hashed_user_data['ph'] = self._hash_data(user_data['phone'])
            if 'first_name' in user_data:
                hashed_user_data['fn'] = self._hash_data(user_data['first_name'])
            if 'last_name' in user_data:
                hashed_user_data['ln'] = self._hash_data(user_data['last_name'])

            processed_event = {
                'event_name': event['event_name'],
                'event_time': event.get('event_time', int(time.time())),
                'action_source': event.get('action_source', 'website'),
                'user_data': hashed_user_data
            }

            if 'event_source_url' in event:
                processed_event['event_source_url'] = event['event_source_url']

            if 'custom_data' in event:
                processed_event['custom_data'] = event['custom_data']

            processed_events.append(processed_event)

        payload = {
            'data': processed_events,
            'access_token': self.access_token
        }

        if self.test_event_code:
            payload['test_event_code'] = self.test_event_code

        url = f"{self.BASE_URL}/{self.pixel_id}/events"

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Sent batch of {len(events)} events to Meta Ads")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send batch events: {e}")
            raise


def generate_sample_b2b_events(num_events: int = 50) -> List[Dict]:
    """
    Generate sample B2B SaaS conversion events

    Args:
        num_events: Number of events to generate

    Returns:
        List of event dictionaries
    """
    companies = ['Acme Corp', 'TechStart Inc', 'DataFlow LLC', 'CloudNine Co', 'DevTools Ltd']
    domains = ['acme.com', 'techstart.io', 'dataflow.co', 'cloudnine.dev', 'devtools.com']
    job_titles = ['CEO', 'CTO', 'VP Engineering', 'Product Manager', 'Engineering Manager']

    first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'Robert', 'Lisa']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']

    event_types = [
        ('ViewContent', 0, 0),  # PageView, no value
        ('Lead', 1, 100),  # Lead form, $100 value
        ('CompleteRegistration', 2, 500),  # Sign up, $500 value
        ('StartTrial', 3, 1000),  # Trial started, $1000 value
        ('Subscribe', 5, 5000),  # Subscription, $5000 value
        ('Purchase', 7, 10000),  # Purchase, $10000 value
    ]

    events = []
    base_time = datetime.now() - timedelta(days=30)

    for i in range(num_events):
        # Progress through funnel over time
        days_offset = (i / num_events) * 30
        event_time = base_time + timedelta(days=days_offset)

        # Select event type (weighted toward top of funnel)
        event_weights = [40, 25, 15, 10, 7, 3]
        event_name, min_val, max_val = random.choices(event_types, weights=event_weights)[0]

        company_idx = random.randint(0, len(companies) - 1)

        event = {
            'event_name': event_name,
            'event_time': int(event_time.timestamp()),
            'action_source': 'website',
            'event_source_url': f'https://www.yourcompany.com/{event_name.lower()}',
            'user_data': {
                'email': f'{first_names[i % len(first_names)].lower()}.{last_names[i % len(last_names)].lower()}@{domains[company_idx]}',
                'first_name': first_names[i % len(first_names)],
                'last_name': last_names[i % len(last_names)],
                'phone': f'+1555{random.randint(1000000, 9999999)}'
            },
            'custom_data': {
                'content_name': f'B2B SaaS - {event_name}',
                'content_category': 'B2B Software',
            }
        }

        if max_val > 0:
            value = random.uniform(min_val, max_val)
            event['custom_data']['value'] = round(value, 2)
            event['custom_data']['currency'] = 'USD'
            event['custom_data']['company'] = companies[company_idx]
            event['custom_data']['job_title'] = random.choice(job_titles)

        events.append(event)

    logger.info(f"Generated {num_events} sample B2B events")
    return events


def write_sample_data_to_meta(
    access_token: str,
    pixel_id: str,
    test_event_code: Optional[str] = None,
    num_events: int = 50,
    batch_size: int = 100
) -> Dict:
    """
    Write sample B2B SaaS data to Meta Ads

    Args:
        access_token: Meta API access token
        pixel_id: Facebook Pixel ID
        test_event_code: Test event code for sandbox
        num_events: Number of events to generate
        batch_size: Batch size for sending events

    Returns:
        Summary of written data
    """
    writer = MetaAdsWriter(access_token, pixel_id, test_event_code)
    events = generate_sample_b2b_events(num_events)

    results = []
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        try:
            result = writer.send_batch_events(batch)
            results.append(result)
            logger.info(f"Sent batch {i//batch_size + 1}, events {i+1}-{i+len(batch)}")
        except Exception as e:
            logger.error(f"Failed to send batch {i//batch_size + 1}: {e}")

    summary = {
        'total_events': len(events),
        'batches_sent': len(results),
        'timestamp': datetime.now().isoformat()
    }

    logger.info(f"Completed Meta Ads data write: {summary}")
    return summary
