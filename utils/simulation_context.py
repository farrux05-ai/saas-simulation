"""
SimulationContext — Shared data "seed" for the A-Series Revenue Engine.

WHY THIS EXISTS
===============
Without a shared context, every integration writes independently:
  - HubSpot creates "TechFlow Solutions"
  - Stripe creates "Acme Corp"
  - Freshdesk creates "CloudScale"
  → Zero cross-layer correlation. Useless for analytics engineering.

WITH this context, every daily run uses the SAME set of company personas
across all 7 layers. The result is a Warehouse where you can actually JOIN
HubSpot deal stages to Stripe invoice history to PostHog feature errors — 
because they're all about the same companies.

DESIGN
======
5 fixed "scenario" personas run every day (these are your "story" companies)
+ N random companies are also added to simulate organic growth

Fixed personas model these real-world B2B SaaS lifecycle stages:
  1. acme_corp        → at_risk   (Reports export fails → churn signal)
  2. techstart_inc    → stalled   (Jira integration blocker in sales funnel)
  3. dataflow_llc     → won       (Happy path: trial → paid → expanding)
  4. cloudnine_co     → churned   (Budget cut: Q3 freeze → lost deal)
  5. devops_pro       → new_lead  (Fresh top-of-funnel, onboarding started)
"""

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


# ---------------------------------------------------------------------------
# Lifecycle stages (matches HubSpot + Supabase status values)
# ---------------------------------------------------------------------------
STAGE_NEW_LEAD   = "new_lead"
STAGE_TRIAL      = "trial"
STAGE_ACTIVE     = "active"
STAGE_AT_RISK    = "at_risk"
STAGE_STALLED    = "stalled"
STAGE_WON        = "won"
STAGE_CHURNED    = "churned"

# Scenario tags drive which *patterns* get injected into each layer
SCENARIO_REPORTS_BLOCKER = "reports_export_blocker"   # Acme: export errors
SCENARIO_JIRA_BLOCKER    = "jira_integration_blocker" # TechStart: sales stall
SCENARIO_HAPPY_PATH      = "happy_path"               # DataFlow: expanding
SCENARIO_BUDGET_CUT      = "budget_cut"               # CloudNine: churned
SCENARIO_NEW_ONBOARD     = "new_onboard"              # DevOps: new lead


@dataclass
class CompanyPersona:
    """
    A single company profile shared across all 7 integration layers.
    Every field here is referenced by at least two different writers.
    """
    # Identity (used by HubSpot, Stripe, Supabase, Freshdesk, PostHog)
    company_name:    str
    domain:          str
    industry:        str
    employee_count:  int

    # Lifecycle state (drives HubSpot stage, Stripe status, Supabase status)
    lifecycle_stage: str                   # e.g. "at_risk"
    scenario:        str                   # e.g. "reports_export_blocker"
    is_fixed:        bool = True           # False = randomly generated extra

    # Billing (drives Stripe plan + Supabase MRR)
    mrr:             float = 199.0
    billing_cycle:   str   = "monthly"
    plan_name:       str   = "professional"

    # Primary contact (used by HubSpot contact, Freshdesk, PostHog user)
    contact_name:    str   = ""
    contact_email:   str   = ""
    contact_title:   str   = "VP of Operations"

    # Deal state (drives HubSpot deal stage and call transcript call_type)
    deal_stage:      str   = "qualifiedtobuy"

    # Unique IDs (set after creation — populated by writers and passed along)
    hubspot_deal_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    # Derived fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def __post_init__(self):
        if not self.contact_email:
            first = self.contact_name.lower().split()[0] if self.contact_name else "admin"
            self.contact_email = f"{first}@{self.domain}"


# ---------------------------------------------------------------------------
# The 5 Fixed Personas
# (Same companies, same stories — every daily run)
# ---------------------------------------------------------------------------

FIXED_PERSONAS: List[CompanyPersona] = [

    # 1. ACME CORP — The "Churn In Progress" story
    #    AT RISK because the Reports Export feature keeps failing.
    #    PostHog:   export_failed_error events with high load_time_ms
    #    Freshdesk: "URGENT: Report generation timing out"
    #    HubSpot:   Lifecycle = At Risk, deal = closed_won (paying) but health declining
    #    Stripe:    Active Professional subscription, no missed payments YET
    CompanyPersona(
        company_name    = "Acme Corp",
        domain          = "acmecorp.com",
        industry        = "FinTech",
        employee_count  = 120,
        lifecycle_stage = STAGE_AT_RISK,
        scenario        = SCENARIO_REPORTS_BLOCKER,
        mrr             = 399.0,
        plan_name       = "business",
        billing_cycle   = "monthly",
        contact_name    = "Sarah Johnson",
        contact_title   = "Head of Finance",
        deal_stage      = "closedwon",
    ),

    # 2. TECHSTART INC — The "Sales Stall" story
    #    In trial, sales discovery call done. Deal stalled because
    #    they NEED a 2-way Jira integration that doesn't exist yet.
    #    HubSpot:   deal_stage = stalled (not closedlost — still hope)
    #    Call Transcript: objection = "we strictly need Jira integration"
    #    Stripe:    No subscription (still trial via Supabase)
    #    PostHog:   Normal onboarding, then low engagement (feature not found)
    CompanyPersona(
        company_name    = "TechStart Inc",
        domain          = "techstart.io",
        industry        = "DevOps",
        employee_count  = 35,
        lifecycle_stage = STAGE_STALLED,
        scenario        = SCENARIO_JIRA_BLOCKER,
        mrr             = 0.0,
        plan_name       = "trial",
        billing_cycle   = "trial",
        contact_name    = "Mike Williams",
        contact_title   = "CTO",
        deal_stage      = "presentationscheduled",
    ),

    # 3. DATAFLOW LLC — The "Happy Path / Expansion" story
    #    Started on Starter, now upgrading to Professional.
    #    This is the success case: good onboarding → engaged user → expand.
    #    HubSpot:   closedwon, existingbusiness deal (upsell)
    #    Stripe:    Plan upgrade event, consistent paid invoices
    #    PostHog:   High session count, Report Generated events, no errors
    #    Freshdesk: Only 1-2 low priority tickets (normal healthy state)
    CompanyPersona(
        company_name    = "DataFlow LLC",
        domain          = "dataflow.co",
        industry        = "SaaS",
        employee_count  = 60,
        lifecycle_stage = STAGE_ACTIVE,
        scenario        = SCENARIO_HAPPY_PATH,
        mrr             = 149.0,
        plan_name       = "professional",
        billing_cycle   = "annual",
        contact_name    = "Emily Brown",
        contact_title   = "CEO",
        deal_stage      = "closedwon",
    ),

    # 4. CLOUDNINE CO — The "Lost Deal / Churned" story
    #    Q3 budget freeze. Deal reached negotiation stage but finance said no.
    #    HubSpot:   closedlost (reason: budget_cut)
    #    Call Transcript: outcome = closed_lost, objection = "Q3 budget is locked"
    #    Stripe:    No subscription (or cancelled if existed)
    #    PostHog:   Last active 45+ days ago → zero recent events
    #    Freshdesk: No new tickets
    CompanyPersona(
        company_name    = "CloudNine Co",
        domain          = "cloudnine.dev",
        industry        = "E-commerce",
        employee_count  = 80,
        lifecycle_stage = STAGE_CHURNED,
        scenario        = SCENARIO_BUDGET_CUT,
        mrr             = 0.0,
        plan_name       = "free",
        billing_cycle   = "none",
        contact_name    = "David Jones",
        contact_title   = "VP of Engineering",
        deal_stage      = "closedlost",
    ),

    # 5. DEVOPS PRO — The "New Lead" story
    #    Just came in via a Meta Ad (LinkedIn-style). Booked a discovery call.
    #    Meta Ads:  Lead + CompleteRegistration events today
    #    HubSpot:   New contact + company, deal = appointmentscheduled
    #    PostHog:   Signup event + Onboarding Started (first session today)
    #    Freshdesk: No tickets yet
    #    Stripe:    No subscription yet
    CompanyPersona(
        company_name    = "DevOps Pro",
        domain          = "devopspro.com",
        industry        = "Technology",
        employee_count  = 15,
        lifecycle_stage = STAGE_NEW_LEAD,
        scenario        = SCENARIO_NEW_ONBOARD,
        mrr             = 0.0,
        plan_name       = "free",
        billing_cycle   = "none",
        contact_name    = "James Garcia",
        contact_title   = "Founder",
        deal_stage      = "appointmentscheduled",
    ),
]


# ---------------------------------------------------------------------------
# Random persona generator (organic growth — 3–5 per day)
# ---------------------------------------------------------------------------

_RANDOM_COMPANIES = [
    ("Helix Analytics",  "helixanalytics.io",  "MarTech",    45),
    ("Orion SaaS",       "orionsaas.com",       "SaaS",       22),
    ("Vectora AI",       "vectora.ai",          "AI/ML",      30),
    ("Meridian HR",      "meridianhr.com",      "HRTech",     70),
    ("Apex Logistics",   "apexlogistics.co",    "Logistics",  200),
    ("Buildify",         "buildify.dev",        "DevTools",   12),
    ("ScaleUp Ltd",      "scaleup.io",          "FinTech",    55),
    ("Prism Tech",       "prismtech.com",       "EdTech",     40),
    ("Zephyr Cloud",     "zephyrcloud.io",      "Cloud",      18),
    ("Forge Systems",    "forgesystems.com",    "Security",   90),
]

_RANDOM_FIRST  = ["Alex", "Jordan", "Morgan", "Taylor", "Casey", "Sam", "Riley"]
_RANDOM_LAST   = ["Lee", "Kim", "Park", "Patel", "Chen", "Singh", "Okafor"]
_RANDOM_TITLES = ["CEO", "CTO", "VP of Sales", "Head of Product", "COO"]


def _make_random_persona() -> CompanyPersona:
    company_name, domain, industry, emp = random.choice(_RANDOM_COMPANIES)
    first = random.choice(_RANDOM_FIRST)
    last  = random.choice(_RANDOM_LAST)
    plan  = random.choice(["starter", "professional", "business"])
    mrr_map = {"starter": 49.0, "professional": 149.0, "business": 399.0}
    stage = random.choice([STAGE_TRIAL, STAGE_ACTIVE, STAGE_AT_RISK])
    deal  = random.choice([
        "appointmentscheduled", "qualifiedtobuy",
        "presentationscheduled", "closedwon"
    ])
    return CompanyPersona(
        company_name    = f"{company_name} {uuid.uuid4().hex[:4].upper()}",
        domain          = f"{uuid.uuid4().hex[:6]}.{domain}",
        industry        = industry,
        employee_count  = emp,
        lifecycle_stage = stage,
        scenario        = SCENARIO_HAPPY_PATH,    # random extras = generic
        is_fixed        = False,
        mrr             = mrr_map[plan],
        plan_name       = plan,
        billing_cycle   = random.choice(["monthly", "annual"]),
        contact_name    = f"{first} {last}",
        contact_title   = random.choice(_RANDOM_TITLES),
        deal_stage      = deal,
    )


# ---------------------------------------------------------------------------
# SimulationContext — the shared seed for a single daily run
# ---------------------------------------------------------------------------

@dataclass
class SimulationContext:
    """
    Single source of truth for one daily Engine run.
    Build once in main_revops_writer.py, pass to every integration layer.
    """
    run_date:         str
    fixed_personas:   List[CompanyPersona]
    random_personas:  List[CompanyPersona]

    @property
    def all_personas(self) -> List[CompanyPersona]:
        return self.fixed_personas + self.random_personas

    def personas_by_scenario(self, scenario: str) -> List[CompanyPersona]:
        return [p for p in self.fixed_personas if p.scenario == scenario]

    def personas_by_stage(self, stage: str) -> List[CompanyPersona]:
        return [p for p in self.all_personas if p.lifecycle_stage == stage]

    def summary(self) -> str:
        lines = [
            f"SimulationContext — {self.run_date}",
            f"  Fixed personas:  {len(self.fixed_personas)}",
            f"  Random extras:   {len(self.random_personas)}",
            f"  Total companies: {len(self.all_personas)}",
            "",
        ]
        for p in self.fixed_personas:
            lines.append(
                f"  [{p.lifecycle_stage.upper():12s}] {p.company_name} "
                f"| {p.scenario} | MRR ${p.mrr:.0f}"
            )
        return "\n".join(lines)


def build_simulation_context(num_random: int = 4) -> SimulationContext:
    """
    Build the SimulationContext for today's run.
    Stamp each fixed persona with today's run_date.

    Args:
        num_random: How many extra (non-story) companies to add

    Returns:
        SimulationContext ready to pass to all 7 integration layers
    """
    run_date = datetime.now().strftime("%Y-%m-%d")

    # Clone fixed personas so mutations don't persist across runs
    fixed = []
    for p in FIXED_PERSONAS:
        clone = CompanyPersona(**{
            k: v for k, v in p.__dict__.items()
        })
        clone.run_date = run_date
        fixed.append(clone)

    randoms = [_make_random_persona() for _ in range(num_random)]

    return SimulationContext(
        run_date        = run_date,
        fixed_personas  = fixed,
        random_personas = randoms,
    )
