# Data Lifecycle & Correlation Logic

> **Target Audience:** Analytics Engineers, RevOps Engineers, or anyone looking to understand the architecture of this project.  
> **Purpose:** Not just "What did we build?" but **"Why did we build it this way, and how does it map to the real world?"**

---

## 1. The Problem: Why Simple Random Data is Not Enough

Most data pipeline simulations operate like this:

```
HubSpot → n random contacts, n random deals
Stripe  → n random customers, n random subscriptions
PostHog → n random events
```

The result? Nothing joins in your data warehouse. "TechFlow Solutions" exists in HubSpot but is missing in Stripe. "Acme Corp" exists in Stripe but never logged into PostHog. This is practically useless for learning Analytics Engineering or presenting a portfolio project, because you can't build any meaningful cross-platform metrics.

**Our Approach:** A GitHub Actions script runs daily, pushing data across all 7 layers for the *exact same companies* experiencing *specific business scenarios*.

---

## 2. Architecture: `SimulationContext`

The `SimulationContext` class lives in `utils/simulation_context.py`. During every daily run (`python main_revops_writer.py --all`), this is the first thing that gets initialized:

```python
# main_revops_writer.py → write_all()
self.context = build_simulation_context(num_random=4)
```

This `context` object is then passed into all 7 integrations:

```
SimulationContext
├── fixed_personas   → 5 "story-driven" companies (fixed every day)
└── random_personas  → 4 random new companies (simulating organic growth daily)
```

---

## 3. The 5 "Story-Driven" Companies (Fixed Personas)

Each persona represents a common lifecycle stage in a real B2B SaaS startup.

### 🔴 Acme Corp — "The Silent At-Risk Customer" (`at_risk` / `remediation_fail`)

**Real-world scenario:**  
Acme Corp upgraded to the `Pro` plan 6 months ago, paying $5,000/mo. They strictly need the "Auto-Remediation" feature. However, over the last 14 days, their Terraform PRs for AWS IAM roles have been failing consistently. The CISO is frustrated because they are "paying for automation that doesn't work."

**How it looks in the code:**

*PostHog (Layer 4):*
```python
# posthog_writer.py, scenario == SCENARIO_REMEDIATION_FAIL
events.append({
    'event': 'Feature Used',
    'properties': {
        'feature_category': 'remediation',
        'feature_action':   'remediation_failed_error',
        'load_time_ms':   random.randint(8000, 20000),  # 8-20 seconds!
        'company':        'Acme Corp',
    }
})
# Inject this pattern consistently over a 14-day history
```

*Freshdesk (Layer 5):*
```python
# freshdesk_writer.py, scenario == SCENARIO_REMEDIATION_FAIL
tickets = [
    ("URGENT: Auto-remediation broke our CI/CD pipeline", priority=4),
    ("remediation_failed_error keeps appearing on AWS IAM roles", priority=3),
    ("Cannot export custom date range to CSV — blank file", priority=3),
]
# Contact email: sarah@acmecorp.com (Identical to their PostHog ID!)
```

*HubSpot (Layer 2):*
```
deal_stage: closedwon (They are currently paying)
lifecyclestage: customer
hs_priority: high (Due to at_risk lifecycle)
```

**What the Analytics Engineer will conclude during analysis:**  
> "Even though Acme Corp looks like a healthy `closedwon` customer in HubSpot, if we can't join their 14-day `export_failed_error` spike in PostHog with the 3 URGENT tickets in Freshdesk, any resulting churn would incorrectly be logged by Sales as 'Pricing Too High' instead of a critical product bug."

---

### 🟡 TechStart Inc — "The Stalled Deal" (`stalled` / `gcp_blocker`)

**Real-world scenario:**  
TechStart is a DevOps-heavy startup. They saw a demo and loved the AWS security features. However, half of their infrastructure is on Google Cloud (GCP). SentinelGuard's GCP scanning is currently in beta. Until full GCP support is parity with AWS, they won't sign the contract.

**How it looks in the code:**

*Call Transcripts (Layer 7):*
```python
# call_transcript_writer.py, scenario == SCENARIO_GCP_BLOCKER
objection  = "we strictly need GCP environment scanning parity"
outcome    = "stalled"
transcript = """
Sarah Kim: Following up from our demo, Mike. Any feedback from the team?
Mike Williams: The platform looks great, honestly. But we hit a wall — 
  we strictly need full GCP support before buying.
Sarah Kim: Understood. Is this a hard blocker or something we can phase in?
Mike Williams: Hard blocker. Our devs live in Jira. Without 2-way sync 
  we can't adopt this.
"""
```

*PostHog (Layer 4):*
```python
# 10-30 days ago: They browsed the GCP integrations page heavily
events = [("integrations_connect_gcp", days_ago=10_to_30)]
# Last 10 days: Zero sessions (Completely disengaged)
```

*HubSpot (Layer 2):*
```
deal_stage:     presentationscheduled (Stuck here)
hs_priority:    high
dealtype:       newbusiness
```

**Analytics Engineer's takeaway:**  
> "In HubSpot, this deal looks 'stalled' without a root cause. But cross-referencing with the Call Transcript data reveals exactly why: 'Revenue lost due to missing GCP support: $60,000 ARR.' This data is exactly what Product needs to prioritize the roadmap."

---

### 🟢 DataFlow LLC — "The Happy Path to Expansion" (`active` / `happy_path`)

**Real-world scenario:**  
DataFlow upgraded to the `Pro` plan last quarter. They use the platform daily to monitor their multi-cloud risk score. They just passed a SOC2 audit using SentinelGuard's compliance reports and now want to expand to the Enterprise tier for custom policy frameworks.

**How it looks in the code:**

*PostHog (Layer 4):*
```python
# Excellent daily engagement
events = [
    ("Session Started", ...),
    ("compliance_run_audit", load_time_ms=200-800),  # Fast, successful audits
]
# Every 3 days: Successfully generates a report
events.append({"event": "Report Generated", "report_type": "compliance", "framework": "SOC2"})
```

*Call Transcripts (Layer 7):*
```python
call_type      = "closing"
outcome        = "closed_won"
buying_signal  = "can we talk about enterprise pricing?"
transcript = """
Emily Brown: We've been very happy. The reporting feature alone saved 
  us 5 hours a week.
James Okafor: Fantastic! Ready to upgrade and add 5 more seats?
Emily Brown: Absolutely. Can we talk about enterprise pricing for next year?
"""
```

*Freshdesk (Layer 5):*
```python
# Only 1 low priority non-technical question
priority = 1   # Low
status   = 5   # Closed
tags     = ["feature_question", "happy_customer"]
```

---

### ⚫ CloudNine Co — "The Silent Loss" (`churned` / `budget_cut`)

**Real-world scenario:**  
CloudNine reached the contract negotiation phase for a `Pro` subscription. Then, at the start of Q3, their parent company enacted a company-wide freeze on all new security software spending. The budget was simply locked, and the account went ghost.

**How it looks in the code:**

*Call Transcripts (Layer 7):*
```python
objection = "not the right time — Q3 budget is locked"
outcome   = "closed_lost"
next_step = "No action — closed lost"
```

*PostHog (Layer 4):*
```python
# Last seen 50 days ago; zero sessions since. (A complete ghost account)
old_date = datetime.now() - timedelta(days=50)
events = [("Session Started", timestamp=old_date)]
```

*Freshdesk (Layer 5):*
```
# Zero tickets generated. They faded away quietly.
```

---

### 🔵 DevOps Pro — "The Brand New Inbound Lead" (`new_lead` / `new_onboard`)

**Real-world scenario:**  
A security engineer at DevOps Pro saw an ad about "Auto-Remediation", clicked it, signed up, and started the onboarding process today. No money has changed hands yet.

**How it looks in the code:**

*Meta Ads (Layer 1):*
```python
# TODAY: Lead + CompleteRegistration event triggered
event_name = "Lead"       → value $100
event_name = "CompleteRegistration" → value $500
```

*PostHog (Layer 4):*
```python
# Exactly 3 events today:
events = [
    "User Signed Up"       → signup_source: "paid_ad"
    "Onboarding Started"   → (Today)
    "Pricing Page Viewed"  → plan_seen: "pro"
]
```

*HubSpot (Layer 2):*
```
deal_stage:     appointmentscheduled
dealtype:       newbusiness
lifecyclestage: lead
```

*Call Transcripts (Layer 7):*
```python
call_type = "discovery"
outcome   = "moved_to_demo"
next_step = "Schedule full demo with broader team"
```

---

## 4. The Daily Execution Workflow

```
00:00 UTC — GitHub Actions triggers
    │
    ▼
build_simulation_context(num_random=4)
    │
    ├── 5 fixed_personas (IDENTICAL every day, progressing in time)
    └── 4 random_personas (NEW every day → simulates organic lead growth)
    │
    ▼ Context is passed down to all 7 Writers
    │
Layer 1: Meta Ads      → Injects DevOps Pro lead event
Layer 2: HubSpot       → Injects all 9 companies with accurate deal stages
Layer 3: Stripe        → Injects DataFlow upgrade, Acme subscriptions (Skips leads)
Layer 4: PostHog       → Acme: export errors | DataFlow: healthy | CloudNine: ghost
Layer 5: Freshdesk     → Acme: 3 URGENT tickets | DataFlow: 1 low priority
Layer 6: Supabase      → Base entities for all 9 companies
Layer 7: Transcripts   → TechStart: Jira stall | CloudNine: Q3 lost | DataFlow: won
```

---

## 5. Why Does This Reflect Real-Life Data Engineering?

| Conventional Reality in RevOps | What Our Simulation Does |
|--------------------------------|--------------------------|
| Salesmen logging "Lost - Price" is often lazy/inaccurate | Call Transcripts parse the exact objection via NLP models. |
| Customer Churn is usually a product bug, not a pricing issue | PostHog (Load times/Errors) + Freshdesk correlation isolates product risk. |
| Successful users are the easiest expansion targets | DataFlow produces high feature usage + closing calls for seat upgrades. |
| Top-of-Funnel signals appear across platforms simultaneously | DevOps Pro appears in Meta Ads, HubSpot, and PostHog on the same day. |

---

## 6. The End Goal: The Analytics Engineering Playground

Once you pipe this daily simulation data into BigQuery or Snowflake using Meltano or Airbyte, you can finally write dbt models (and test joins) exactly like this:

```sql
-- Example: Automated At-Risk Customer Detection
SELECT
    h.company_name,
    h.deal_stage,
    COUNT(p.event)         AS export_errors_14d,
    COUNT(f.ticket_id)     AS urgent_support_tickets,
    t.objection_raised     AS real_sales_objection
FROM hubspot_companies h
LEFT JOIN posthog_events p
    ON h.company_domain = p.company
   AND p.feature_action = 'export_failed_error'
   AND p.timestamp >= CURRENT_DATE - 14
LEFT JOIN freshdesk_tickets f
    ON f.email ILIKE '%' || h.company_domain
   AND f.priority >= 3
LEFT JOIN call_transcripts t
    ON t.prospect_company = h.company_name
WHERE h.lifecycle_stage = 'customer'
GROUP BY 1, 2, 5
HAVING COUNT(p.event) > 0 OR COUNT(f.ticket_id) > 0
ORDER BY export_errors_14d DESC;
```

For this query to return rows, `company_domain` and `company_name` must perfectly match across 4 different platforms—which `SimulationContext` legally guarantees for our 5 fixed personas every day.

---

> **Conclusion:** This repository is not a "random data generator." It is a *context-aware B2B SaaS Revenue Engine*. It models precise business problems, guarantees cross-layer primary-key correlation, and naturally simulates organic, daily pipeline growth.
