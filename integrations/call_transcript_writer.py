"""
Call Transcript Writer
Generates realistic B2B SaaS sales call transcripts and writes them to Supabase.

Why this exists:
  At A-series stage, most teams use Gong, Fireflies, or Chorus to record
  demo/discovery calls. This data is the richest "why we won/lost" signal
  in the entire revenue engine — not captured by CRM deal stages alone.

  Table written: call_transcripts (Supabase)
  Linked to:     HubSpot deal_id (string reference)
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING

from supabase import Client, create_client

from utils.logger import get_logger

if TYPE_CHECKING:
    from utils.simulation_context import SimulationContext

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Static data pools — realistic but fully synthetic
# ---------------------------------------------------------------------------

REPS = [
    {"name": "Sarah Kim",    "email": "sarah.kim@company.com"},
    {"name": "James Okafor", "email": "james.okafor@company.com"},
    {"name": "Lena Müller",  "email": "lena.muller@company.com"},
    {"name": "Carlos Ruiz",  "email": "carlos.ruiz@company.com"},
]

PROSPECT_COMPANIES = [
    "Acme Corp", "TechStart Inc", "DataFlow LLC", "CloudNine Co",
    "DevOps Pro", "ScaleUp Ltd", "Buildify", "Helix Analytics",
    "Orion SaaS", "Vectora AI", "Meridian HR", "Apex Logistics",
]

CALL_TYPES = ["discovery", "demo", "follow_up", "negotiation", "closing"]

DEAL_STAGES = {
    "discovery":   "Qualified Lead",
    "demo":        "Demo Scheduled",
    "follow_up":   "Proposal Sent",
    "negotiation": "Negotiation",
    "closing":     "Closed Won",
}

OUTCOMES = {
    "discovery":   ["moved_to_demo", "not_qualified", "follow_up_needed"],
    "demo":        ["moved_to_proposal", "needs_more_time", "competitor_mentioned"],
    "follow_up":   ["proposal_accepted", "stalled", "budget_concern"],
    "negotiation": ["closed_won", "closed_lost", "extended"],
    "closing":     ["closed_won", "closed_lost"],
}

# Objections that come up in real B2B SaaS sales calls
# Business Pattern Injection: We deliberately overweight specific product capability
# objections to demonstrate a disconnect between "generic CRM lost reasons" (e.g. price)
# and "real product feedback" (e.g. Jira integration missing).
OBJECTIONS = [
    "pricing is too high",
    "we are already using a competitor",
    "need to get buy-in from the IT team",
    "not the right time — Q3 budget is locked",
    "we need a SOC 2 certification first",  # Key A-Series blocker
    "our team is too small right now",
    "we don't have bandwidth to onboard",
    "we strictly need GCP environment scanning parity before buying", # The "ScaleFlow" secret churn reason
    "your reporting module doesn't do custom exports" # The churn correlation hint
]

# Positive buying signals
BUYING_SIGNALS = [
    "this solves exactly what we need",
    "can we talk about enterprise pricing?",
    "how quickly can we get started?",
    "our CEO wants to see a demo",
    "we had a bad experience with the current tool",
    "we are growing fast and need to scale",
    "I love the integration with HubSpot",
    "can you do a POC for us?",
]

# Call transcript templates per call type
TRANSCRIPT_TEMPLATES = {
    "discovery": [
        ("{rep}: Hi {prospect_name}, thanks for taking the time today. Can you walk me through your current setup?\n"
         "{prospect_name}: Sure. Right now we are using a mix of spreadsheets and {competitor} — it's getting messy.\n"
         "{rep}: Got it. What's the biggest pain point you're trying to solve?\n"
         "{prospect_name}: Honestly, {pain_point}.\n"
         "{rep}: That's exactly what we hear from companies at your stage. We've helped teams like yours reduce that by 40%. "
         "Would it make sense to schedule a full demo?\n"
         "{prospect_name}: Yeah, let's do that. Oh, one thing — {objection}.\n"
         "{rep}: Totally fair. Let me explain how we handle that..."),
    ],
    "demo": [
        ("{rep}: Great, so today I'll walk you through the three things most relevant to your use case. "
         "First, the revenue dashboard...\n"
         "{prospect_name}: This looks clean. Can it connect to our existing Stripe account?\n"
         "{rep}: Yes, it syncs in real-time via the Stripe webhook. Here's how it looks with live data.\n"
         "{prospect_name}: {buying_signal}\n"
         "{rep}: Exactly. And this is just the out-of-the-box view — you can customize every metric.\n"
         "{prospect_name}: What about {objection}?\n"
         "{rep}: Good question. We have {n} customers who had the same concern — here's how we solved it."),
    ],
    "follow_up": [
        ("{rep}: Following up from our demo last week. Did you get a chance to share it with the team?\n"
         "{prospect_name}: Yes, and the feedback was mostly positive. The main concern is {objection}.\n"
         "{rep}: Understood. I put together a proposal that addresses that directly — did you receive my email?\n"
         "{prospect_name}: I did. The pricing is a bit higher than we expected.\n"
         "{rep}: Let me show you the ROI breakdown. Based on your numbers, you'd recover the cost in {weeks} weeks.\n"
         "{prospect_name}: {buying_signal}. Let me get back to you by Friday."),
    ],
    "negotiation": [
        ("{rep}: Good to connect again. Where are we on the contract review?\n"
         "{prospect_name}: Legal had a few questions about the data processing addendum.\n"
         "{rep}: We can address those. The standard DPA covers GDPR and SOC 2. Do you need annual billing flexibility?\n"
         "{prospect_name}: Actually yes — {objection}.\n"
         "{rep}: We can do quarterly billing for the first year. Would that unblock you?\n"
         "{prospect_name}: That would really help. {buying_signal}."),
    ],
    "closing": [
        ("{rep}: Everything looks good from our side. Contracts are ready to sign.\n"
         "{prospect_name}: We're almost there. One last thing — {objection}.\n"
         "{rep}: We can include that in the onboarding SLA. I'll update the contract now.\n"
         "{prospect_name}: Perfect. {buying_signal}. Let's do it.\n"
         "{rep}: Fantastic! Welcome aboard. I'll introduce you to your CSM today."),
    ],
}

PAIN_POINTS = [
    "we can't see our MRR trend in one place",
    "churn is hard to predict before it happens",
    "our sales and marketing data lives in silos",
    "we don't know which channel is driving real revenue",
    "onboarding takes too long and we're losing free trial users",
    "we have no visibility into product adoption per account",
]

COMPETITORS = ["Salesforce", "HubSpot", "Pipedrive", "Notion", "Monday.com", "spreadsheets"]


# ---------------------------------------------------------------------------
# Transcript generator
# ---------------------------------------------------------------------------

def _generate_transcript(call_type: str, rep: Dict, prospect_company: str) -> tuple[str, str]:
    """Build a realistic transcript string and return (transcript, parsed_objection)."""
    template = random.choice(TRANSCRIPT_TEMPLATES[call_type])
    prospect_name = f"{random.choice(['Alex', 'Jordan', 'Morgan', 'Taylor', 'Casey'])} ({prospect_company})"
    
    # We select the objection here so we can guarantee the 'outcome' correlates later
    objection = random.choice(OBJECTIONS)

    transcript_text = template.format(
        rep=rep["name"],
        prospect_name=prospect_name,
        objection=objection,
        buying_signal=random.choice(BUYING_SIGNALS),
        pain_point=random.choice(PAIN_POINTS),
        competitor=random.choice(COMPETITORS),
        n=random.randint(5, 50),
        weeks=random.randint(4, 16),
    )
    return transcript_text, objection


def generate_call_transcripts(
    num_calls: int = 30,
    days_back: int = 60,
    hubspot_deal_ids: List[str] = None,
    context: Optional['SimulationContext'] = None,
) -> List[Dict]:
    """
    Generate call transcript records.
    Fixed personas get deterministic call records that match their lifecycle story.
    Random extras fill the remainder.
    """
    from utils.simulation_context import (
        SCENARIO_GCP_BLOCKER, SCENARIO_BUDGET_CUT,
        SCENARIO_HAPPY_PATH, SCENARIO_NEW_ONBOARD
    )

    records = []

    # --- FIXED PERSONA CALLS (context-driven) ---
    if context:
        for persona in context.fixed_personas:
            if persona.scenario == SCENARIO_NEW_ONBOARD:
                # DevOps Pro: first discovery call, very early stage
                call_date = datetime.now() - timedelta(days=1)
                transcript = (
                    f"Carlos Ruiz: Hi {persona.contact_name}, thanks for booking this call! "
                    f"Can you tell me more about what's bringing you here today?\n"
                    f"{persona.contact_name}: Sure! We're growing fast and our current setup is getting messy. "
                    f"We heard about you via an ad and wanted to explore.\n"
                    f"Carlos Ruiz: Perfect timing. What tools are you currently using?\n"
                    f"{persona.contact_name}: Mostly spreadsheets and {random.choice(COMPETITORS)}.\n"
                    f"Carlos Ruiz: Got it. {random.choice(PAIN_POINTS).capitalize()} is exactly what we fix. "
                    f"Let me schedule a full demo for your team."
                )
                records.append(_make_record(
                    call_type="discovery", outcome="moved_to_demo",
                    rep=REPS[3], persona=persona,
                    call_date=call_date, transcript=transcript,
                    objection=random.choice(OBJECTIONS[:3]),
                    buying_signal="we are growing fast and need to scale",
                    next_step="Schedule full demo with broader team",
                    hubspot_deal_ids=hubspot_deal_ids,
                ))

            elif persona.scenario == SCENARIO_GCP_BLOCKER:
                # TechStart: follow_up call, stalled on Jira
                call_date = datetime.now() - timedelta(days=5)
                objection = "we strictly need GCP environment scanning parity before buying"
                transcript = (
                    f"Sarah Kim: Following up from our demo, {persona.contact_name}. Any feedback from the team?\n"
                    f"{persona.contact_name}: The platform looks great, honestly. But we hit a wall — {objection}.\n"
                    f"Sarah Kim: Understood. Is this a hard blocker or something we can phase in?\n"
                    f"{persona.contact_name}: Hard blocker for us. Our cloud environment is 50% GCP. Without full scanning we can't adopt this.\n"
                    f"Sarah Kim: I hear you. Let me escalate this to product and come back to you by EOW."
                )
                records.append(_make_record(
                    call_type="follow_up", outcome="stalled",
                    rep=REPS[0], persona=persona,
                    call_date=call_date, transcript=transcript,
                    objection=objection,
                    buying_signal=None,
                    next_step="Escalate GCP scanning request to product team",
                    hubspot_deal_ids=hubspot_deal_ids,
                ))

            elif persona.scenario == SCENARIO_BUDGET_CUT:
                # CloudNine: negotiation call, budget freeze
                call_date = datetime.now() - timedelta(days=14)
                objection = "not the right time — Q3 budget is locked"
                transcript = (
                    f"Lena M\u00fcller: Great to reconnect, {persona.contact_name}. Where are we on the contract?\n"
                    f"{persona.contact_name}: I have bad news. Finance reviewed it and {objection}.\n"
                    f"Lena M\u00fcller: I understand. Is there any flexibility if we offer quarterly billing?\n"
                    f"{persona.contact_name}: Not at this stage. Q3 is frozen. We might revisit in Q4 but no promises.\n"
                    f"Lena M\u00fcller: Completely understood. I'll mark this as paused and check in again in October."
                )
                records.append(_make_record(
                    call_type="negotiation", outcome="closed_lost",
                    rep=REPS[2], persona=persona,
                    call_date=call_date, transcript=transcript,
                    objection=objection,
                    buying_signal=None,
                    next_step="No action — closed lost",
                    hubspot_deal_ids=hubspot_deal_ids,
                ))

            elif persona.scenario == SCENARIO_HAPPY_PATH:
                # DataFlow: closing call, expansion deal
                call_date = datetime.now() - timedelta(days=3)
                transcript = (
                    f"James Okafor: {persona.contact_name}, contracts are ready to go!\n"
                    f"{persona.contact_name}: We've been very happy. The reporting feature alone saved us 5 hours a week.\n"
                    f"James Okafor: Fantastic! Ready to upgrade to the Enterprise plan and add 5 more seats?\n"
                    f"{persona.contact_name}: Absolutely. can we talk about enterprise pricing for next year?\n"
                    f"James Okafor: Of course. I'll loop in your CSM today and we'll get that locked in."
                )
                records.append(_make_record(
                    call_type="closing", outcome="closed_won",
                    rep=REPS[1], persona=persona,
                    call_date=call_date, transcript=transcript,
                    objection=None,
                    buying_signal="can we talk about enterprise pricing?",
                    next_step="Introduce to CSM, send expanded contract",
                    hubspot_deal_ids=hubspot_deal_ids,
                ))
            # Acme Corp (at_risk): no active sales call — they're already a customer struggling silently

    # --- RANDOM / GENERIC CALLS ---
    num_random = max(0, num_calls - len(records))

    for _ in range(num_random):
        call_type = random.choice(CALL_TYPES)
        rep = random.choice(REPS)
        prospect_company = random.choice(PROSPECT_COMPANIES)
        call_date = datetime.now() - timedelta(days=random.randint(0, days_back))
        duration_min = random.randint(12, 62)

        record = {
            "id":               str(uuid.uuid4()),
            "call_type":        call_type,
            "deal_stage":       DEAL_STAGES[call_type],
            "outcome":          random.choice(OUTCOMES[call_type]),
            "rep_name":         rep["name"],
            "rep_email":        rep["email"],
            "prospect_company": prospect_company,
            "duration_minutes": duration_min,
            "call_date":        call_date.isoformat(),
        }
        
        transcript_text, objection = _generate_transcript(call_type, rep, prospect_company)
        
        # --- BUSINESS PATTERN INJECTION: The Correlation Engine ---
        # Force a "closed_lost" or "stalled" outcome if they hit our specific roadmap blockers.
        # This allows Analysts to query: "How many deals did we lose purely because of GCP?"
        outcome = random.choice(OUTCOMES[call_type])
        if "GCP" in objection or "SOC 2" in objection:
            if call_type in ["negotiation", "closing"]:
                outcome = "closed_lost"
            elif call_type in ["discovery", "demo", "follow_up"]:
                outcome = "stalled"
                
        record["outcome"] = outcome
        record["transcript"] = transcript_text
        record["objection_raised"] = objection
        record["buying_signal"] = random.choice(BUYING_SIGNALS) if random.random() > 0.3 else None
        record["next_step"] = random.choice([
            "Send follow-up email",
            "Schedule next call",
            "Send contract",
            "Introduce to CSM",
            "No action — deal lost",
        ])
        
        # Override next_step if explicitly lost
        if outcome == "closed_lost":
            record["next_step"] = "No action — closed lost"

        record["hubspot_deal_id"] = random.choice(hubspot_deal_ids) if hubspot_deal_ids else None
        record["created_at"] = call_date.isoformat()
        
        records.append(record)

    logger.info(f"Generated {len(records)} call transcript records ({len(context.fixed_personas) if context else 0} persona + {num_random} random)")
    return records


def _make_record(
    call_type: str, outcome: str, rep: Dict, persona,
    call_date: datetime, transcript: str,
    objection: Optional[str], buying_signal: Optional[str],
    next_step: str, hubspot_deal_ids: List[str]
) -> Dict:
    """Build a single call transcript record dict."""
    return {
        "id":               str(uuid.uuid4()),
        "call_type":        call_type,
        "deal_stage":       DEAL_STAGES.get(call_type, "Unknown"),
        "outcome":          outcome,
        "rep_name":         rep["name"],
        "rep_email":        rep["email"],
        "prospect_company": persona.company_name,
        "duration_minutes": random.randint(15, 55),
        "call_date":        call_date.isoformat(),
        "transcript":       transcript,
        "objection_raised": objection,
        "buying_signal":    buying_signal,
        "next_step":        next_step,
        "hubspot_deal_id":  random.choice(hubspot_deal_ids) if hubspot_deal_ids else None,
        "created_at":       call_date.isoformat(),
    }


# ---------------------------------------------------------------------------
# Supabase writer
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS call_transcripts (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_type         TEXT NOT NULL,          -- discovery | demo | follow_up | negotiation | closing
    deal_stage        TEXT,                   -- mirrors HubSpot deal stage
    outcome           TEXT,                   -- e.g. moved_to_demo, closed_won, stalled
    rep_name          TEXT NOT NULL,
    rep_email         TEXT,
    prospect_company  TEXT NOT NULL,
    duration_minutes  INTEGER,
    call_date         TIMESTAMP NOT NULL,
    transcript        TEXT,                   -- full synthetic transcript
    objection_raised  TEXT,                   -- primary objection extracted
    buying_signal     TEXT,                   -- positive signal if detected
    next_step         TEXT,
    hubspot_deal_id   TEXT,                   -- soft reference to HubSpot deal
    created_at        TIMESTAMP DEFAULT NOW()
);
"""


def write_call_transcripts(
    url: str,
    service_key: str,
    num_calls: int = 30,
    days_back: int = 60,
    hubspot_deal_ids: List[str] = None,
    context: Optional['SimulationContext'] = None,
) -> Dict:
    """
    Generate and write call transcripts to Supabase.

    Args:
        url:               Supabase project URL
        service_key:       Supabase service role key
        num_calls:         Number of call records to generate
        days_back:         Historical date range
        hubspot_deal_ids:  Optional HubSpot deal IDs to cross-reference

    Returns:
        Summary dict with counts
    """
    logger.info(f"Generating {num_calls} call transcripts (last {days_back} days)...")

    client: Client = create_client(url, service_key)
    records = generate_call_transcripts(num_calls, days_back, hubspot_deal_ids, context=context)

    # Note: run CREATE_TABLE_SQL once in Supabase SQL editor if table doesn't exist
    logger.info("DDL hint: run CREATE_TABLE_SQL in Supabase SQL editor if first run")
    logger.debug(CREATE_TABLE_SQL)

    try:
        batch_size = 50
        inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            client.table("call_transcripts").insert(batch).execute()
            inserted += len(batch)
            logger.info(f"  Inserted batch {i // batch_size + 1}: {len(batch)} records")

        outcome_counts = {}
        for r in records:
            outcome_counts[r["outcome"]] = outcome_counts.get(r["outcome"], 0) + 1

        summary = {
            "total_inserted": inserted,
            "call_types":     list({r["call_type"] for r in records}),
            "outcome_counts": outcome_counts,
            "date_range_days": days_back,
            "reps_simulated": list({r["rep_name"] for r in records}),
        }

        logger.info(f"✓ Call transcripts written: {inserted} records")
        return summary

    except Exception as e:
        logger.error(f"Failed to write call transcripts: {e}")
        raise
