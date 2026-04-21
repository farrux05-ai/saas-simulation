"""
HubSpot Data Writer
Writes realistic B2B SaaS data to HubSpot (Contacts, Companies, Deals)
"""

import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING

import requests

from utils.logger import get_logger

if TYPE_CHECKING:
    from utils.simulation_context import SimulationContext, CompanyPersona

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
        except requests.exceptions.HTTPError as e:
            if response.status_code == 409:
                # Handle "Conflict" gracefully by parsing the existing ID
                try:
                    error_data = response.json()
                    msg = error_data.get('message', '')
                    match = re.search(r"Existing ID: (\d+)", msg)
                    if match:
                        existing_id = match.group(1)
                        logger.debug(f"HubSpot 409 Conflict: Extracted existing ID {existing_id}")
                        return {'id': existing_id, 'is_existing': True}
                except Exception:
                    pass
                    
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"HubSpot API request failed: {e.response.status_code} - {e.response.text}")
            else:
                logger.error(f"HubSpot API request failed: {e}")
            raise
        except requests.exceptions.RequestException as e:
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


def generate_sample_companies(
    count: int = 5,
    context: Optional['SimulationContext'] = None
) -> List[Dict]:
    """Generate company data.
    If context is provided, fixed personas are used first (same names every day).
    Extra random companies fill up to `count`.
    """
    from utils.simulation_context import STAGE_AT_RISK, STAGE_CHURNED, STAGE_STALLED

    # Lifecycle → HubSpot lifecyclestage mapping
    _STAGE_MAP = {
        "new_lead": "lead",
        "trial":    "marketingqualifiedlead",
        "active":   "customer",
        "at_risk":  "customer",        # paying but at risk
        "stalled":  "salesqualifiedlead",
        "won":      "customer",
        "churned":  "other",
    }

    companies = []

    if context:
        # Fixed persona companies — same names/stages every run
        for p in context.all_personas:
            companies.append({
                'name':              p.company_name,
                'domain':            p.domain,
                'numberofemployees': p.employee_count,
                'annualrevenue':     str(int(p.mrr * 12)),
                'city':              random.choice(['San Francisco', 'New York', 'Austin', 'Seattle', 'Boston']),
                'state':             random.choice(['CA', 'NY', 'TX', 'WA', 'MA']),
                'country':           'United States',
                'lifecyclestage':    _STAGE_MAP.get(p.lifecycle_stage, 'lead'),
                'type':              'PARTNER' if p.lifecycle_stage in (STAGE_AT_RISK, 'active', 'won') else 'PROSPECT',
                'industry':          'COMPUTER_SOFTWARE',
                '_persona_ref':      p,   # internal reference — stripped before API call
            })
    else:
        # Fallback: original random generation
        company_names = [
            'TechFlow Solutions', 'DataSync Corp', 'CloudVista Inc', 'InnovateLabs',
            'NextGen Systems', 'ScaleUp Technologies', 'AgileWorks', 'QuantumLeap Inc',
            'FusionSoft', 'VelocityData', 'PrismTech', 'NexusCloud', 'ApexSolutions',
            'SynergyTech', 'CatalystSoftware'
        ]
        industries = ['COMPUTER_SOFTWARE', 'RETAIL', 'HOSPITAL_HEALTH_CARE', 'MANUFACTURING', 'FINANCIAL_SERVICES']
        for i in range(count):
            company_name = random.choice(company_names) + f" {random.randint(1, 100)}"
            companies.append({
                'name':              company_name,
                'domain':            f"{company_name.lower().replace(' ', '')}.com",
                'numberofemployees': random.choice([10, 25, 50, 100, 250, 500, 1000]),
                'annualrevenue':     str(random.choice([100000, 500000, 1000000, 5000000])),
                'city':              random.choice(['San Francisco', 'New York', 'Austin', 'Seattle', 'Boston']),
                'state':             random.choice(['CA', 'NY', 'TX', 'WA', 'MA']),
                'country':           'United States',
                'lifecyclestage':    random.choice(['lead', 'marketingqualifiedlead', 'salesqualifiedlead', 'opportunity', 'customer']),
                'type':              random.choice(['PROSPECT', 'PARTNER', 'VENDOR']),
            })

    return companies


def generate_sample_deals(
    count: int = 8,
    companies: List[Dict] = None,
    context: Optional['SimulationContext'] = None
) -> List[Dict]:
    """Generate deal data.
    Fixed personas produce deals with the exact stage matching their lifecycle story.
    """
    deals = []

    if context:
        # Each persona with a persona_ref gets a deal matching their story
        for company in (companies or []):
            persona = company.get('_persona_ref')
            if not persona:
                # Random extra company — generic deal
                amount = random.choice([5000, 10000, 25000, 50000])
                close_date = datetime.now() + timedelta(days=random.randint(15, 90))
                deals.append({
                    'dealname':          f"{company['name']} — Subscription",
                    'amount':            str(amount),
                    'dealstage':         random.choice(['appointmentscheduled', 'qualifiedtobuy', 'closedwon']),
                    'pipeline':          'default',
                    'closedate':         close_date.strftime('%Y-%m-%d'),
                    'deal_currency_code':'USD',
                    'dealtype':          'newbusiness',
                    'hs_priority':       'medium',
                })
                continue

            # Fixed persona — stage and amount are deterministic
            amount = max(int(persona.mrr * 12), 4999)  # annualised
            close_date = datetime.now() + timedelta(days=30)
            deals.append({
                'dealname':          f"{persona.company_name} — {persona.plan_name.title()} Plan",
                'amount':            str(amount),
                'dealstage':         persona.deal_stage,
                'pipeline':          'default',
                'closedate':         close_date.strftime('%Y-%m-%d'),
                'deal_currency_code':'USD',
                'dealtype':          'newbusiness' if persona.lifecycle_stage == 'new_lead' else 'existingbusiness',
                'hs_priority':       'high' if persona.lifecycle_stage in ('at_risk', 'stalled') else 'medium',
            })
    else:
        deal_names = [
            'Annual Subscription', 'Enterprise Plan', 'Growth Package', 'Starter Plan',
            'Professional Services', 'Custom Integration', 'Premium Support', 'Team License'
        ]
        deal_stages = [
            'appointmentscheduled', 'qualifiedtobuy', 'presentationscheduled',
            'decisionmakerboughtin', 'contractsent', 'closedwon', 'closedlost'
        ]
        for i in range(count):
            amount = random.choice([5000, 10000, 25000, 50000, 75000, 100000])
            close_date = datetime.now() + timedelta(days=random.randint(0, 90))
            deals.append({
                'dealname':          f"{random.choice(deal_names)} - Deal {i+1}",
                'amount':            str(amount),
                'dealstage':         random.choice(deal_stages),
                'pipeline':          'default',
                'closedate':         close_date.strftime('%Y-%m-%d'),
                'deal_currency_code':'USD',
                'dealtype':          random.choice(['newbusiness', 'existingbusiness']),
                'hs_priority':       random.choice(['low', 'medium', 'high']),
            })

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
    num_deals: int = 8,
    context: Optional['SimulationContext'] = None,
) -> Dict:
    """
    Write B2B SaaS data to HubSpot.
    When context is provided, company/deal data reflects the shared personas.
    """
    writer = HubSpotWriter(access_token)
    logger.info("Starting HubSpot data write operation")

    results = {'contacts': [], 'companies': [], 'deals': [], 'errors': []}

    try:
        # Generate companies (context-aware)
        logger.info(f"Creating companies...")
        sample_companies = generate_sample_companies(num_companies, context=context)

        for company_data in sample_companies:
            persona = company_data.pop('_persona_ref', None)  # strip internal ref
            try:
                created = writer.create_company(company_data)
                created['_persona_ref'] = persona  # re-attach for deal generation
                results['companies'].append(created)
                if persona:
                    persona.hubspot_deal_id = created.get('id')  # capture for later layers
            except Exception as e:
                logger.error(f"Failed to create company: {e}")
                results['errors'].append({'type': 'company', 'error': str(e)})

        # Generate contacts from persona contact_name / email
        logger.info(f"Creating contacts...")
        sample_contacts = generate_sample_contacts(num_contacts)
        # Overwrite first N contacts with persona contacts for correlation
        if context:
            for i, persona in enumerate(context.fixed_personas):
                if i < len(sample_contacts):
                    sample_contacts[i]['email']     = persona.contact_email
                    sample_contacts[i]['firstname']  = persona.contact_name.split()[0]
                    sample_contacts[i]['lastname']   = persona.contact_name.split()[-1]
                    sample_contacts[i]['jobtitle']   = persona.contact_title

        for idx, contact_data in enumerate(sample_contacts):
            try:
                created_contact = writer.create_contact(contact_data)
                results['contacts'].append(created_contact)
                if results['companies']:
                    company = random.choice(results['companies'])
                    try:
                        writer.associate_objects(
                            'contacts', created_contact['id'],
                            'companies', company['id'], '279'
                        )
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Failed to create contact: {e}")
                results['errors'].append({'type': 'contact', 'error': str(e)})

        # Create deals from persona stages
        logger.info(f"Creating deals...")
        sample_deals = generate_sample_deals(num_deals, results['companies'], context=context)
        for deal_data in sample_deals:
            try:
                created_deal = writer.create_deal(deal_data)
                results['deals'].append(created_deal)
                if results['contacts']:
                    try:
                        writer.associate_objects('deals', created_deal['id'], 'contacts', random.choice(results['contacts'])['id'], '3')
                    except Exception:
                        pass
                if results['companies']:
                    try:
                        writer.associate_objects('deals', created_deal['id'], 'companies', random.choice(results['companies'])['id'], '5')
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Failed to create deal: {e}")
                results['errors'].append({'type': 'deal', 'error': str(e)})

        deals_advanced = advance_deal_stages(writer)
        results['deals_advanced'] = deals_advanced

        logger.info(f"""
HubSpot complete:
  Companies: {len(results['companies'])} | Contacts: {len(results['contacts'])}
  Deals: {len(results['deals'])} | Advanced: {deals_advanced} | Errors: {len(results['errors'])}
        """)
        return results

    except Exception as e:
        logger.error(f"HubSpot data write failed: {e}")
        raise
