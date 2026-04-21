# A-Series Revenue Engine Simulator 🚀

[![Status](https://img.shields.io/badge/status-production--ready-success)](https://github.com/farrux05-ai/saas-simulation)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional-grade **B2B SaaS Revenue Engine Simulator** built for Analytics Engineers
who help A-series startups make data-driven decisions or prepare for their B-series raise.

This tool populates every layer of a real A-series tech stack with high-fidelity,
cross-referenced sandbox data — from the first paid ad click to the closed deal call transcript.

---

## 📖 The "ScaleFlow" Use Case (Why this exists)

Imagine **ScaleFlow**, a promising A-Series SaaS. They spend $50k/mo on Meta Ads, their HubSpot is full of leads, but their conversion rate is terrible and churn is spiking. 

**The Analytics Problem (The Blank Space):**
*   **Sales says:** "We lost the deal because the price is too high." (Recorded in HubSpot).
*   **Product says:** "Users are logging in, so they must be active." (Recorded in PostHog).
*   **Support says:** "Ticket volume is up." (Recorded in Freshdesk).

**The Solution (This Engine's Data Generation):**
By orchestrating this 7-layer data pipeline, an Analytics Engineer sends perfectly correlated data to their Warehouse (e.g., BigQuery, Snowflake) to reveal the *real* story:
1.  **Sales Intelligence (Layer 7):** Call transcripts explicitly contain objections like "We strictly need a 2-way Jira integration". The Python generation engine correlates these specific keywords to force `closed_lost` or `stalled` outcomes in the dataset.
2.  **Product / Support Correlation (Layers 4 & 5):** The churn spike isn't random. The PostHog simulator generates specific `export_failed_error` events with high `load_time_ms`. Simultaneously, the Freshdesk simulator generates urgent tickets with subjects like "URGENT: Report generation timing out" for those same profiles.

*This script doesn't just generate random data. It generates exact, correlating business patterns across 7 different platform APIs so you can practice building the Modern Data Stack and the queries that solve the gaps.*

---

## 🏗️ Architecture — 7-Layer Revenue Funnel

```
┌─────────────────────────────────────────────────────────────────────┐
│               A-SERIES REVENUE ENGINE (7 layers)                    │
├────┬────────────────────┬──────────────────────────────────────────┤
│ #  │ Layer              │ Platform           │ What's simulated      │
├────┼────────────────────┼────────────────────┼───────────────────────┤
│ 1  │ 🎯 Marketing       │ Meta Ads           │ Lead & conversion events│
│ 2  │ 📋 CRM             │ HubSpot            │ Contacts, companies, deals│
│ 3  │ 💳 Billing         │ Stripe             │ Subscriptions + 12-mo invoices│
│ 4  │ 📊 Product         │ PostHog            │ Sessions, onboarding, features│
│ 5  │ 🎫 Support         │ Freshdesk          │ Tickets vs subscription health│
│ 6  │ 🗄️  Database       │ Supabase           │ App DB + dim_date (DWH-ready)│
│ 7  │ 📞 Sales Intel     │ Supabase           │ Call transcripts (Gong-style)│
└────┴────────────────────┴────────────────────┴───────────────────────┘
```

> **Why this stack?** This mirrors what real A-series B2B SaaS companies use.
> Every tool was chosen based on adoption data — not "cool factor."

---

## 🔑 Stack Decisions (with rationale)

| Tool | Decision | Reason |
|------|----------|--------|
| **HubSpot** | ✅ Kept | Standard CRM at A-series (Salesforce comes at B-series when ACV > $30k) |
| **Stripe** | ✅ Kept | Default billing for SaaS; generates richest revenue time-series data |
| **PostHog** | ✅ Kept | Open-source friendly, unique session/onboarding/feature-depth events not in Supabase |
| **Freshdesk** | ✅ Kept | Support layer for health scoring (ticket volume vs MRR) |
| **Supabase** | ✅ Kept | Product DB + warehouse (dim_date, SCD-ready, dbt-compatible) |
| **Meta Ads** | ✅ Kept | Demand generation + attribution layer |
| **Call Transcripts** | ✅ New | The "why we won/lost" layer — missing from most RevOps setups |
| **Mixpanel** | ❌ Removed | 80% overlap with Supabase events; PostHog covers unique analytics needs |
| **Salesforce** | ❌ Not added | A-series standard is HubSpot; Salesforce is a B-series migration signal |

---

## 💡 What Makes This Different

### 1. Cross-Referenced Data (Layer 2 → Layer 7)
HubSpot deal IDs are captured during the CRM write and injected into call transcript
records — so you can do real attribution analysis: `call outcome → deal closed?`

### 2. Sales Intelligence Layer (New)
Most RevOps pipelines stop at CRM + Stripe. This simulator adds a `call_transcripts`
table to Supabase with structured fields extracted from synthetic transcripts:

```
call_type       → discovery | demo | follow_up | negotiation | closing
outcome         → moved_to_demo | closed_won | stalled | budget_concern
objection_raised→ "pricing is too high" | "not the right time" ...
buying_signal   → "can we talk enterprise pricing?" | "how fast can we start?" ...
hubspot_deal_id → cross-reference to CRM deal
transcript      → full synthetic conversation
```

### 3. Warehouse-Ready from Day 1
Supabase includes a full `dim_date` calendar dimension — every time-series
dbt model can join it without extra setup.

### 4. SCD Type 2 Ready
HubSpot deal progressions and Supabase company status updates generate
real deltas on every run — perfect for testing dbt snapshots.

---

## 🛠️ Setup

### 1. Initialize Environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`
Copy `.env.example` and fill in your sandbox credentials:

```bash
cp .env.example .env
```

Required variables:

| Service | Variables |
|---------|-----------|
| HubSpot | `HUBSPOT_ACCESS_TOKEN`, `HUBSPOT_PORTAL_ID` |
| Stripe | `STRIPE_SECRET_KEY` |
| Supabase | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` |
| PostHog | `POSTHOG_API_KEY` |
| Freshdesk | `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY` |
| Meta Ads | `META_ACCESS_TOKEN`, `META_ACCOUNT_ID` (+ pixel for events) |

### 3. Supabase — First-Run Table Setup
Run the DDL below once in your **Supabase SQL Editor** before the first run:

```sql
-- Core tables (companies, users, events, subscriptions, dim_date)
-- Defined in integrations/supabase_writer.py → create_tables()

-- Sales intelligence layer (Layer 7)
CREATE TABLE IF NOT EXISTS call_transcripts (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_type         TEXT NOT NULL,
    deal_stage        TEXT,
    outcome           TEXT,
    rep_name          TEXT NOT NULL,
    rep_email         TEXT,
    prospect_company  TEXT NOT NULL,
    duration_minutes  INTEGER,
    call_date         TIMESTAMP NOT NULL,
    transcript        TEXT,
    objection_raised  TEXT,
    buying_signal     TEXT,
    next_step         TEXT,
    hubspot_deal_id   TEXT,
    created_at        TIMESTAMP DEFAULT NOW()
);
```

---

## ▶️ Running the Engine

```bash
# Run the full 7-layer Revenue Engine
python main_revops_writer.py --all

# Run specific layers only
python main_revops_writer.py --services hubspot stripe posthog

# Include Meta Ads conversion events (requires pixel ID)
python main_revops_writer.py --all --meta-pixel-id YOUR_PIXEL_ID

# Check which layers are configured
python main_revops_writer.py --check-config

# Simulate without writing (dry run)
python main_revops_writer.py --dry-run
```

Expected output:
```
✓ META ADS        → 50 conversion events
✓ HUBSPOT         → 15 contacts, 8 companies, 12 deals
✓ STRIPE          → 15 customers, subscriptions, invoices
✓ POSTHOG         → sessions, onboarding, feature events
✓ FRESHDESK       → 25 support tickets
✓ SUPABASE        → 40 companies, users, events, dim_date
✓ CALL_TRANSCRIPTS→ 30 discovery/demo/closing call records
```

---

## 📊 Data Schema Reference

| Platform | Layer | Key Tables / Objects |
|----------|-------|----------------------|
| **Meta Ads** | Marketing | Conversion events (Lead, ViewContent, Purchase) |
| **HubSpot** | CRM | Contacts, Companies, Deals (with stage history) |
| **Stripe** | Billing | Customers, Subscriptions, Invoices (12-mo history) |
| **PostHog** | Product | Events: Session Started, Onboarding Completed, Feature Used, Report Generated |
| **Freshdesk** | Support | Tickets with priority, category, and status |
| **Supabase** | Database | `companies`, `users`, `events`, `subscriptions`, `dim_date` |
| **Supabase** | Sales Intel | `call_transcripts` (Layer 7 — cross-ref'd with HubSpot) |

---

## 🔄 GitHub Actions — Automated Data Growth

The included workflow (`.github/workflows/revops_ingest.yml`) runs the engine
daily, growing your sandbox data ~1% per day — simulating a real SaaS business
without manual intervention.

---

## 📁 Project Structure

```
ingestion_practice/
├── main_revops_writer.py          # Main orchestrator (7-layer engine)
├── config.py                      # Platform configuration (env-based)
├── requirements.txt
├── .env                           # Your sandbox credentials (never commit)
├── .env.example                   # Template for onboarding
├── integrations/
│   ├── meta_ads_writer.py         # Layer 1 — Marketing
│   ├── hubspot_writer.py          # Layer 2 — CRM
│   ├── stripe_writer.py           # Layer 3 — Billing
│   ├── posthog_writer.py          # Layer 4 — Product Analytics
│   ├── freshdesk_writer.py        # Layer 5 — Support
│   ├── supabase_writer.py         # Layer 6 — Database / Warehouse
│   └── call_transcript_writer.py  # Layer 7 — Sales Intelligence
└── utils/
    └── logger.py
```

---

> [!IMPORTANT]
> **Sandbox only.** All integrations use test/sandbox API keys. Never run this
> against production credentials — write operations will appear in live dashboards.

> [!NOTE]
> **Analytics Engineering context.** This simulator is designed for Analytics
> Engineers helping A-series startups build their Revenue Engine before a B-series
> raise. Each tool in the stack was chosen based on real adoption patterns at the
> $2M–$15M ARR stage, not convention.

**Built for Revenue. Designed for Scale. 🚀**
