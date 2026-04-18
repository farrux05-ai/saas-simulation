"""
HubSpot Data Writer
Writes realistic B2B SaaS data to HubSpot (Contacts, Companies, Deals)
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class HubSpotWriter:
    """Writer for HubSpot CRM data"""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, access_token: str):
        """
        Initialize HubSpot writer

        Args:
            access_token: HubSpot private app access token
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to HubSpot"""
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            if method == 'POST':
                response = self.session.post(url, json=data)
            elif method == 'PATCH':
                response = self.session.patch(url, json=data)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'GET':
                response = self.session.get(url)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"HubSpot API request failed: {e.response.status_code} - {e.response.text}")
            else:
                logger.error(f"HubSpot API request failed: {e}")
            raise

    def create_contact(self, contact_data: Dict) -> Dict:
        """
        Create a contact in HubSpot

        Args:
            contact_data: Contact properties

        Returns:
            Created contact data
        """
        endpoint = "crm/v3/objects/contacts"
        payload = {"properties": contact_data}

        logger.info(f"Creating contact: {contact_data.get('email')}")
        result = self._make_request('POST', endpoint, payload)
        return result

    def create_company(self, company_data: Dict) -> Dict:
        """
        Create a company in HubSpot

        Args:
            company_data: Company properties

        Returns:
            Created company data
        """
        endpoint = "crm/v3/objects/companies"
        payload = {"properties": company_data}

        logger.info(f"Creating company: {company_data.get('name')}")
        result = self._make_request('POST', endpoint, payload)
        return result

    def create_deal(self, deal_data: Dict) -> Dict:
        """
        Create a deal in HubSpot

        Args:
            deal_data: Deal properties

        Returns:
            Created deal data
        """
        endpoint = "crm/v3/objects/deals"
        payload = {"properties": deal_data}

        logger.info(f"Creating deal: {deal_data.get('dealname')}")
        result = self._make_request('POST', endpoint, payload)
        return result

    def associate_objects(self, from_object_type: str, from_object_id: str,
                         to_object_type: str, to_object_id: str,
                         association_type: str) -> Dict:
        """
        Associate two objects in HubSpot

        Args:
            from_object_type: Source object type (contact, company, deal)
            from_object_id: Source object ID
            to_object_type: Target object type
            to_object_id: Target object ID
            association_type: Association type ID

        Returns:
            Association result
        """
        endpoint = f"crm/v3/objects/{from_object_type}/{from_object_id}/associations/{to_object_type}/{to_object_id}/{association_type}"

        logger.debug(f"Associating {from_object_type}:{from_object_id} -> {to_object_type}:{to_object_id}")
        result = self._make_request('PUT', endpoint)
        return result

    def create_activity(self, activity_type: str, deal_id: str, contact_id: str, days_ago: int) -> Dict:
        """
        Create a single CRM activity (call, meeting, or email) linked to a deal and contact.

        Activity types represent the real sales process:
        - call:    Sales rep phones the prospect to qualify or follow-up
        - meeting: Demo, discovery call recorded as a structured meeting
        - email:   Follow-up email, proposal sent, etc.

        Args:
            activity_type: 'calls', 'meetings', or 'emails'
            deal_id: HubSpot Deal ID to associate with
            contact_id: HubSpot Contact ID to associate with
            days_ago: How many days ago this activity happened

        Returns:
            Created activity object
        """
        timestamp_ms = int((datetime.now() - timedelta(days=days_ago)).timestamp() * 1000)

        if activity_type == 'calls':
            properties = {
                'hs_call_title':    random.choice(['Discovery Call', 'Follow-up Call', 'Demo Call', 'Closing Call']),
                'hs_call_duration': str(random.choice([5, 10, 15, 20, 30, 45, 60]) * 60 * 1000),  # ms
                'hs_call_status':   random.choice(['COMPLETED', 'COMPLETED', 'COMPLETED', 'NO_ANSWER']),
                'hs_call_direction': random.choice(['OUTBOUND', 'OUTBOUND', 'INBOUND']),
                'hs_timestamp':     str(timestamp_ms),
                'hs_call_body':     random.choice([
                    'Discussed pricing and next steps.',
                    'Prospect requested a product demo.',
                    'Left voicemail, will follow up via email.',
                    'Call went well, deal moving forward.',
                ]),
            }
        elif activity_type == 'meetings':
            properties = {
                'hs_meeting_title':   random.choice(['Product Demo', 'Discovery Meeting', 'Technical Review', 'Contract Review']),
                'hs_meeting_outcome': random.choice(['COMPLETED', 'COMPLETED', 'NO_SHOW', 'RESCHEDULED']),
                'hs_timestamp':       str(timestamp_ms),
                'hs_meeting_start_time': str(timestamp_ms),
                'hs_meeting_end_time':   str(timestamp_ms + random.choice([30, 45, 60]) * 60 * 1000),
                'hs_meeting_body':    random.choice([
                    'Walked through the platform. Prospect liked the reporting features.',
                    'Discussed integration requirements and timeline.',
                    'Technical team joined. Questions about API and data security.',
                    'Agreement on scope. Awaiting legal review.',
                ]),
            }
        else:  # emails
            properties = {
                'hs_email_subject': random.choice([
                    'Following up on our conversation',
                    'Proposal attached — next steps',
                    'Quick question re: your timeline',
                    'Resources from today\'s demo',
                ]),
                'hs_email_direction': random.choice(['EMAIL', 'FORWARDED_EMAIL']),
                'hs_email_status':    'SENT',
                'hs_timestamp':       str(timestamp_ms),
            }

        endpoint = f"crm/v3/objects/{activity_type}"
        payload  = {'properties': properties}

        try:
            result = self._make_request('POST', endpoint, payload)

            # Associate activity with the deal and contact
            for obj_type, obj_id, assoc_type in [
                ('deals',    deal_id,    'activity_to_deal'),
                ('contacts', contact_id, 'activity_to_contact'),
            ]:
                try:
                    self.associate_objects(activity_type, result['id'], obj_type, obj_id, assoc_type)
                except Exception:
                    pass  # Association is best-effort

            return result
        except Exception as e:
            logger.warning(f"Failed to create {activity_type} activity: {e}")
            return {}

    def create_deal_activities(self, deal_id: str, contact_id: str, deal_stage: str) -> Dict[str, int]:
        """
        Generate a realistic sequence of activities for a deal based on its current stage.
        Earlier-stage deals have fewer touchpoints; later-stage deals have more.

        Real-world pattern:
            appointmentscheduled  → 1-2 activities (just starting)
            qualifiedtobuy        → 2-3 activities (qualification calls)
            presentationscheduled → 3-5 activities (demo + follow-ups)
            decisionmakerboughtin → 4-6 activities (stakeholder meetings)
            contractsent          → 5-8 activities (legal review, negotiation)
            closedwon/closedlost  → 6-10 activities (full history)

        Args:
            deal_id:     HubSpot Deal ID
            contact_id:  Primary Contact ID for this deal
            deal_stage:  Current deal stage (determines activity volume)

        Returns:
            Dict with counts per activity type
        """
        stage_activity_count = {
            'appointmentscheduled':  (1, 2),
            'qualifiedtobuy':        (2, 3),
            'presentationscheduled': (3, 5),
            'decisionmakerboughtin': (4, 6),
            'contractsent':          (5, 8),
            'closedwon':             (6, 10),
            'closedlost':            (4, 7),
        }
        low, high = stage_activity_count.get(deal_stage, (2, 4))
        total_activities = random.randint(low, high)

        # Weight: more calls early, more meetings mid, emails throughout
        activity_types = random.choices(
            ['calls', 'meetings', 'emails'],
            weights=[0.40, 0.30, 0.30],
            k=total_activities
        )

        counts = {'calls': 0, 'meetings': 0, 'emails': 0}
        for i, atype in enumerate(activity_types):
            days_ago = total_activities - i + random.randint(0, 3)
            result = self.create_activity(atype, deal_id, contact_id, days_ago)
            if result:
                counts[atype] += 1

        logger.debug(
            f"Deal {deal_id} ({deal_stage}): "
            f"{counts['calls']} calls, {counts['meetings']} meetings, {counts['emails']} emails"
        )
        return counts


def generate_sample_contacts(count: int = 10) -> List[Dict]:
    """Generate sample contact data"""

    first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'James', 'Lisa', 'Robert', 'Jennifer',
                   'William', 'Linda', 'Richard', 'Patricia', 'Thomas', 'Maria', 'Charles', 'Susan', 'Daniel', 'Karen']

    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

    job_titles = [
        'CEO', 'CTO', 'VP of Engineering', 'VP of Sales', 'VP of Marketing',
        'Head of Product', 'Engineering Manager', 'Product Manager', 'Sales Director',
        'Marketing Director', 'Operations Manager', 'Customer Success Manager',
        'Account Executive', 'Solutions Architect', 'DevOps Lead'
    ]

    contacts = []

    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"

        contact = {
            'email': email,
            'firstname': first_name,
            'lastname': last_name,
            'jobtitle': random.choice(job_titles),
            'phone': f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'lifecyclestage': random.choice(['lead', 'marketingqualifiedlead', 'salesqualifiedlead', 'opportunity', 'customer']),
            'hs_lead_status': random.choice(['NEW', 'OPEN', 'IN_PROGRESS', 'OPEN_DEAL', 'UNQUALIFIED', 'CONNECTED']),
        }

        contacts.append(contact)

    return contacts


def generate_sample_companies(count: int = 5) -> List[Dict]:
    """Generate sample company data"""

    company_names = [
        'TechFlow Solutions', 'DataSync Corp', 'CloudVista Inc', 'InnovateLabs',
        'NextGen Systems', 'ScaleUp Technologies', 'AgileWorks', 'QuantumLeap Inc',
        'FusionSoft', 'VelocityData', 'PrismTech', 'NexusCloud', 'ApexSolutions',
        'SynergyTech', 'CatalystSoftware'
    ]

    industries = [
        'Other', 'Technology', 'Software', 'Retail', 'Healthcare', 'Manufacturing', 'Finance'
    ]

    companies = []

    for i in range(count):
        company_name = random.choice(company_names) + f" {random.randint(1, 100)}"

        company = {
            'name': company_name,
            'domain': f"{company_name.lower().replace(' ', '')}.com",
            'numberofemployees': random.choice([10, 25, 50, 100, 250, 500, 1000]),
            'annualrevenue': str(random.choice([100000, 500000, 1000000, 5000000, 10000000, 50000000])),
            'city': random.choice(['San Francisco', 'New York', 'Austin', 'Seattle', 'Boston', 'Denver', 'Chicago']),
            'state': random.choice(['CA', 'NY', 'TX', 'WA', 'MA', 'CO', 'IL']),
            'country': 'United States',
            'lifecyclestage': random.choice(['lead', 'marketingqualifiedlead', 'salesqualifiedlead', 'opportunity', 'customer']),
            'type': random.choice(['PROSPECT', 'PARTNER', 'RESELLER', 'VENDOR', 'OTHER'])
        }

        companies.append(company)

    return companies


def generate_sample_deals(count: int = 8, companies: List[Dict] = None) -> List[Dict]:
    """Generate sample deal data"""

    deal_names = [
        'Annual Subscription', 'Enterprise Plan', 'Growth Package', 'Starter Plan',
        'Professional Services', 'Custom Integration', 'Premium Support', 'Team License'
    ]

    deal_stages = [
        'appointmentscheduled', 'qualifiedtobuy', 'presentationscheduled',
        'decisionmakerboughtin', 'contractsent', 'closedwon', 'closedlost'
    ]

    pipelines = ['default']  # Can be customized based on HubSpot setup

    deals = []

    for i in range(count):
        amount = random.choice([5000, 10000, 25000, 50000, 75000, 100000, 150000, 250000])
        close_date = datetime.now() + timedelta(days=random.randint(0, 90))

        deal = {
            'dealname': f"{random.choice(deal_names)} - Deal {i+1}",
            'amount': str(amount),
            'dealstage': random.choice(deal_stages),
            'pipeline': random.choice(pipelines),
            'closedate': close_date.strftime('%Y-%m-%d'),
            'deal_currency_code': 'USD',
            'dealtype': random.choice(['newbusiness', 'existingbusiness']),
            'hs_priority': random.choice(['low', 'medium', 'high']),
        }

        deals.append(deal)

    return deals


def advance_deal_stages(writer: 'HubSpotWriter') -> int:
    """
    Fetch recent open deals and advance ~30% of them to the next pipeline stage.
    This generates realistic SCD deltas for dbt snapshot testing.

    Returns:
        Number of deals advanced
    """
    # Ordered pipeline stages (open stages only — closedwon/closedlost are terminal)
    stage_progression = [
        'appointmentscheduled',
        'qualifiedtobuy',
        'presentationscheduled',
        'decisionmakerboughtin',
        'contractsent',
        'closedwon',   # terminal — won't advance further
    ]

    try:
        response = writer._make_request(
            'GET',
            'crm/v3/objects/deals?limit=50&properties=dealstage,dealname'
        )
        deals = response.get('results', [])

        if not deals:
            logger.info("No existing deals found to advance")
            return 0

        # Pick ~30% of deals
        open_deals = [
            d for d in deals
            if d.get('properties', {}).get('dealstage') not in ('closedwon', 'closedlost')
        ]
        to_advance = random.sample(open_deals, max(1, len(open_deals) // 3))

        advanced = 0
        for deal in to_advance:
            current_stage = deal['properties'].get('dealstage', 'appointmentscheduled')
            if current_stage in stage_progression:
                idx = stage_progression.index(current_stage)
                next_stage = stage_progression[min(idx + 1, len(stage_progression) - 1)]
                if next_stage != current_stage:
                    writer._make_request(
                        'PATCH',
                        f"crm/v3/objects/deals/{deal['id']}",
                        {'properties': {'dealstage': next_stage}}
                    )
                    logger.debug(f"Advanced deal {deal['id']}: {current_stage} → {next_stage}")
                    advanced += 1

        logger.info(f"Advanced {advanced} deal(s) to next stage")
        return advanced

    except Exception as e:
        logger.error(f"Failed to advance deal stages: {e}")
        return 0  # Non-fatal — don't block the rest of the run


def write_hubspot_data(
    access_token: str,
    num_contacts: int = 10,
    num_companies: int = 5,
    num_deals: int = 8
) -> Dict:
    """
    Write sample B2B SaaS data to HubSpot

    Args:
        access_token: HubSpot access token
        num_contacts: Number of contacts to create
        num_companies: Number of companies to create
        num_deals: Number of deals to create

    Returns:
        Summary of created records
    """
    writer = HubSpotWriter(access_token)

    logger.info("Starting HubSpot data write operation")

    results = {
        'contacts': [],
        'companies': [],
        'deals': [],
        'activities': {'calls': 0, 'meetings': 0, 'emails': 0},
        'errors': []
    }

    try:
        # Create companies
        logger.info(f"Creating {num_companies} companies...")
        sample_companies = generate_sample_companies(num_companies)

        for company_data in sample_companies:
            try:
                created_company = writer.create_company(company_data)
                results['companies'].append(created_company)
            except Exception as e:
                logger.error(f"Failed to create company: {e}")
                results['errors'].append({'type': 'company', 'error': str(e)})

        # Create contacts and associate with companies
        logger.info(f"Creating {num_contacts} contacts...")
        sample_contacts = generate_sample_contacts(num_contacts)

        for idx, contact_data in enumerate(sample_contacts):
            try:
                created_contact = writer.create_contact(contact_data)
                results['contacts'].append(created_contact)

                # Associate contact with a company
                if results['companies']:
                    company = random.choice(results['companies'])
                    try:
                        writer.associate_objects(
                            'contacts', created_contact['id'],
                            'companies', company['id'],
                            '279'  # Standard contact-to-company association
                        )
                        logger.debug(f"Associated contact {created_contact['id']} with company {company['id']}")
                    except Exception as e:
                        logger.warning(f"Failed to associate contact with company: {e}")

            except Exception as e:
                logger.error(f"Failed to create contact: {e}")
                results['errors'].append({'type': 'contact', 'error': str(e)})

        # Create deals and associate with contacts and companies
        logger.info(f"Creating {num_deals} deals...")
        sample_deals = generate_sample_deals(num_deals)

        for deal_data in sample_deals:
            try:
                created_deal = writer.create_deal(deal_data)
                results['deals'].append(created_deal)

                # Associate deal with a contact
                if results['contacts']:
                    contact = random.choice(results['contacts'])
                    try:
                        writer.associate_objects(
                            'deals', created_deal['id'],
                            'contacts', contact['id'],
                            '3'  # Standard deal-to-contact association
                        )
                    except Exception as e:
                        logger.warning(f"Failed to associate deal with contact: {e}")

                # Associate deal with a company
                if results['companies']:
                    company = random.choice(results['companies'])
                    try:
                        writer.associate_objects(
                            'deals', created_deal['id'],
                            'companies', company['id'],
                            '5'  # Standard deal-to-company association
                        )
                    except Exception as e:
                        logger.warning(f"Failed to associate deal with company: {e}")

                # Generate realistic activity history for this deal
                if results['contacts']:
                    contact = random.choice(results['contacts'])
                    deal_stage = deal_data.get('dealstage', 'appointmentscheduled')
                    try:
                        activity_counts = writer.create_deal_activities(
                            deal_id=created_deal['id'],
                            contact_id=contact['id'],
                            deal_stage=deal_stage
                        )
                        results['activities']['calls']    += activity_counts.get('calls', 0)
                        results['activities']['meetings'] += activity_counts.get('meetings', 0)
                        results['activities']['emails']   += activity_counts.get('emails', 0)
                    except Exception as e:
                        logger.warning(f"Failed to create activities for deal: {e}")

            except Exception as e:
                logger.error(f"Failed to create deal: {e}")
                results['errors'].append({'type': 'deal', 'error': str(e)})

        # Advance existing deal stages (for snapshot delta testing)
        deals_advanced = advance_deal_stages(writer)
        results['deals_advanced'] = deals_advanced

        total_activities = sum(results['activities'].values())

        # Summary
        logger.info(f"""
HubSpot Data Write Complete:
- Companies created:  {len(results['companies'])}
- Contacts created:   {len(results['contacts'])}
- Deals created:      {len(results['deals'])}
- Deals advanced:     {deals_advanced}
- Activities logged:  {total_activities} (calls={results['activities']['calls']}, meetings={results['activities']['meetings']}, emails={results['activities']['emails']})
- Errors:             {len(results['errors'])}
        """)

        return results

    except Exception as e:
        logger.error(f"HubSpot data write operation failed: {e}")
        raise
