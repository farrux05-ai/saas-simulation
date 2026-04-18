"""
Freshdesk Data Writer
Writes support ticket data to Freshdesk for testing/sandbox environments
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class FreshdeskWriter:
    """Writer for Freshdesk support tickets"""

    def __init__(self, domain: str, api_key: str):
        """
        Initialize Freshdesk writer

        Args:
            domain: Freshdesk domain (e.g., yourcompany.freshdesk.com)
            api_key: Freshdesk API key
        """
        self.domain = domain.replace('https://', '').replace('http://', '')
        self.base_url = f"https://{self.domain}/api/v2"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.auth = (api_key, 'X')

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """
        Make API request to Freshdesk

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload

        Returns:
            Response data
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        try:
            if method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            else:
                response = self.session.get(url, headers=headers)

            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Freshdesk API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise

    def create_ticket(self, ticket_data: Dict) -> Dict:
        """
        Create a support ticket

        Args:
            ticket_data: Ticket information

        Returns:
            Created ticket data
        """
        logger.info(f"Creating ticket: {ticket_data.get('subject', 'N/A')}")
        return self._make_request('POST', 'tickets', ticket_data)

    def create_contact(self, contact_data: Dict) -> Dict:
        """
        Create a contact

        Args:
            contact_data: Contact information

        Returns:
            Created contact data
        """
        logger.info(f"Creating contact: {contact_data.get('email', 'N/A')}")
        return self._make_request('POST', 'contacts', contact_data)


# Sample data for realistic B2B SaaS support tickets
TICKET_SUBJECTS = [
    "Cannot access dashboard after login",
    "API rate limit exceeded - need increase",
    "Billing discrepancy on invoice #{}",
    "Feature request: Export to CSV",
    "Integration with {} not working",
    "User permissions not updating",
    "SSO configuration help needed",
    "Data sync delayed by 2+ hours",
    "Mobile app crashing on startup",
    "Webhook delivery failures",
    "Question about enterprise plan features",
    "Need help migrating from competitor",
    "Custom domain setup assistance",
    "Performance issues with large datasets",
    "Email notifications not being sent",
    "Report generation timing out",
    "White label branding not applying",
    "Team member invitation not received",
    "Data export taking too long",
    "Need API documentation for v2",
]

TICKET_DESCRIPTIONS = {
    "technical": [
        "We're experiencing issues with {} functionality. This started approximately {} ago and is affecting {} users in our organization.",
        "Our team is unable to {}. We've tried clearing cache and different browsers but the issue persists. Error code: {}.",
        "The {} feature is not working as expected. Expected behavior: {}. Actual behavior: {}.",
        "We're getting a {} error when trying to {}. This is blocking our workflow. Urgency: High.",
        "Performance degradation noticed in {}. Load times have increased from {}s to {}s over the past week.",
    ],
    "billing": [
        "We noticed a charge of ${} on our account but we expected ${}. Can you please clarify the difference?",
        "Our invoice #{} shows {} seats but we only have {} active users. Please review and adjust.",
        "We'd like to upgrade from {} plan to {} plan. What's the prorated cost for the remainder of this billing cycle?",
        "We were charged twice for the same period. Transaction IDs: {} and {}. Please refund one charge.",
        "Can you provide a breakdown of our current usage? We're seeing higher costs than anticipated.",
    ],
    "feature_request": [
        "It would be great if we could {}. This would help us {} and improve our workflow significantly.",
        "Many of our team members have requested the ability to {}. Is this on your roadmap?",
        "We need {} functionality for our use case. Currently we have to work around this by {}.",
        "Suggestion: Add {} to the {} section. This would make {} much easier.",
        "Are there plans to support {}? This is a must-have for our team.",
    ],
    "question": [
        "What's the difference between {} and {} in your {} plan?",
        "How do we configure {} for our team? The documentation is not clear on this.",
        "Can you explain how {} works with {}? We want to ensure proper setup.",
        "Is it possible to {}? We have a specific use case where this would be helpful.",
        "What are the limits for {} in our current plan? Can these be increased?",
    ],
}

COMPANIES = [
    "Acme Corp", "TechStart Inc", "Global Solutions", "Innovation Labs",
    "DataFlow Systems", "CloudScale", "NextGen Analytics", "Velocity Software",
    "Quantum Digital", "Synergy Partners", "Apex Technologies", "Zenith Corp"
]

CONTACT_NAMES = [
    ("John", "Smith"), ("Sarah", "Johnson"), ("Michael", "Williams"),
    ("Emily", "Brown"), ("David", "Jones"), ("Jessica", "Garcia"),
    ("James", "Miller"), ("Ashley", "Davis"), ("Robert", "Rodriguez"),
    ("Jennifer", "Martinez"), ("Daniel", "Hernandez"), ("Lisa", "Lopez"),
]


def generate_sample_tickets(count: int = 20) -> List[Dict]:
    """
    Generate sample support tickets

    Args:
        count: Number of tickets to generate

    Returns:
        List of ticket dictionaries
    """
    tickets = []

    for i in range(count):
        ticket_type = random.choice(['technical', 'billing', 'feature_request', 'question'])

        # Random subject
        subject = random.choice(TICKET_SUBJECTS)
        if '{}' in subject:
            replacements = {
                'invoice': random.randint(10000, 99999),
                'integration': random.choice(['Salesforce', 'Slack', 'Zapier', 'Stripe']),
            }
            for key, val in replacements.items():
                if key in subject.lower():
                    subject = subject.format(val)
                    break

        # Random description
        description = random.choice(TICKET_DESCRIPTIONS[ticket_type])
        if '{}' in description:
            if ticket_type == 'technical':
                description = description.format(
                    random.choice(['API', 'dashboard', 'export', 'sync', 'report']),
                    random.choice(['2 hours', '1 day', '3 days']),
                    random.randint(5, 50)
                )
            elif ticket_type == 'billing':
                description = description.format(
                    random.randint(100, 1000),
                    random.randint(100, 1000),
                    random.randint(10000, 99999),
                    random.randint(5, 20),
                    random.randint(5, 20)
                )
            else:
                description = description.format(
                    random.choice(['export data', 'custom fields', 'bulk operations']),
                    random.choice(['save time', 'improve accuracy', 'scale better']),
                    random.choice(['manual workarounds', 'external tools'])
                )

        # Contact info
        first_name, last_name = random.choice(CONTACT_NAMES)
        company = random.choice(COMPANIES)
        email = f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com"

        # Priority and status
        priority = random.choice([1, 1, 2, 2, 2, 3, 3, 4])  # Weighted towards medium
        status = random.choice([2, 2, 2, 3, 3, 4, 5])  # 2=Open, 3=Pending, 4=Resolved, 5=Closed

        ticket = {
            'subject': subject,
            'description': description,
            'email': email,
            'priority': priority,
            'status': status,
            'source': random.choice([2, 3, 7, 9]),  # Portal, Phone, Chat, Email
            'name': f"{first_name} {last_name}",
            'tags': [ticket_type, random.choice(['urgent', 'normal', 'low-priority'])],
        }

        tickets.append(ticket)

    return tickets


def write_freshdesk_data(
    domain: str,
    api_key: str,
    ticket_count: int = 20
) -> Dict:
    """
    Write sample data to Freshdesk

    Args:
        domain: Freshdesk domain
        api_key: Freshdesk API key
        ticket_count: Number of tickets to create

    Returns:
        Summary of created data
    """
    writer = FreshdeskWriter(domain, api_key)

    logger.info(f"Starting Freshdesk data write - {ticket_count} tickets")

    # Generate sample tickets
    tickets = generate_sample_tickets(ticket_count)

    created_tickets = []
    failed_tickets = []

    for ticket in tickets:
        try:
            created_ticket = writer.create_ticket(ticket)
            created_tickets.append(created_ticket)
            logger.info(f"Created ticket #{created_ticket.get('id')}: {ticket['subject']}")
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            failed_tickets.append(ticket)

    summary = {
        'total_attempted': ticket_count,
        'successful': len(created_tickets),
        'failed': len(failed_tickets),
        'created_ticket_ids': [t.get('id') for t in created_tickets],
        'timestamp': datetime.now().isoformat()
    }

    logger.info(f"Freshdesk write complete: {summary['successful']}/{summary['total_attempted']} tickets created")

    return summary
