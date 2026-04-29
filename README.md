# A-Series Revenue Engine Simulator 🚀

[![Status](https://img.shields.io/badge/status-production--ready-success)](https://github.com/farrux05-ai/saas-simulation)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional-grade **B2B SaaS Revenue Engine Simulator** built for Analytics Engineers and Data Professionals who help A-series startups make data-driven decisions.

This tool populates every layer of a real A-series tech stack with high-fidelity, cross-referenced sandbox data — from the first paid ad click to the closed deal call transcript. 

---

## 🔗 How Everything Connects (The Data Flow)

To make realistic analytics possible, data must connect seamlessly across platforms. Here is how our 7 layers talk to each other to create the perfect data warehouse dataset.

### 🎯 1. Where do the Leads come from? (Meta Ads -> PostHog)
When a prospect sees an ad, **Meta Ads** generates a `Lead` conversion event. Simultaneously, **PostHog** records a `User Signed Up` event tracked with a `paid_ad` source. *You can exactly map advertising spend to product signups.*

### 📋 2. How does the CRM work? (HubSpot)
That same user is pushed to **HubSpot** via their `company_domain`. A new Company, Contact, and Deal is created. As the prospect explores the product, Sales moves the deal through lifecycle stages (e.g., `presentationscheduled` -> `closedwon`).

### 💳 3. How are Payments connected? (Stripe)
When the HubSpot deal is marked `closedwon`, **Stripe** kicks in. It creates a Stripe Customer, a recurring Subscription tier, and generates up to 12 months of monthly historical Invoices. *This ties CRM efforts directly to MRR (Monthly Recurring Revenue).*

### 📊 4. Product Health & Support (PostHog -> Freshdesk)
What if the product breaks? If **PostHog** detects that a company is experiencing high latency or `export_failed_error` events, the engine automatically triggers **Freshdesk** to generate URGENT support tickets from the same user. *This allows you to measure how product bugs influence churn.*

### 🗄️ 5. The Underlying Core (Supabase)
All these layers rest on a **Supabase** Postgres database. It stores the core application states (`users`, `companies`) and the groundbreaking **Layer 7**: Sales Intelligence. If a deal is lost, Supabase generates Gong-style Call Transcripts identifying exactly what objections killed the deal (e.g., "Missing Jira Integration").

---

## 🏗️ Architecture — 7-Layer Revenue Funnel

```text
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

> **Why this stack?** This mirrors what real A-series B2B SaaS companies use. Every tool was chosen based on adoption data — not "cool factor."

### 📖 Want to dive deeper into the business cases?
[**Read the Data Lifecycle & Correlation Logic Guide here.**](./docs/data_lifecycle.md)

---

## 💡 What Makes This Different

### 1. Cross-Referenced Data (No Blind Datasets)
Most simulators generate random lists. We use a shared `SimulationContext`. "TechFlow Solutions" in HubSpot has the exact same email domains, company priorities, and histories in Stripe and PostHog. You can build real Joins.

### 2. Sales Intelligence Layer (Layer 7)
Most RevOps pipelines stop at CRM + Stripe. This simulator adds a `call_transcripts` table to Supabase with structured fields extracted from synthetic transcripts:
```text
outcome          → moved_to_demo | closed_won | stalled
objection_raised → "pricing is too high" | "need jira integration"
hubspot_deal_id  → cross-reference to CRM deal
```

### 3. SCD Type 2 & Warehouse Ready
Supabase includes a full `dim_date` calendar dimension. HubSpot deal progressions generate real deltas on every run — perfect for testing `dbt snapshots` and time-series joined modeling.

---

## 🛠️ Setup & Local Installation

### 1. Initialize Environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` and fill in your sandbox credentials:
```bash
cp .env.example .env
```
*(Requires: HubSpot Token, Stripe Secret, PostHog Key, Freshdesk API, Supabase URL/Key, and Meta Ads Token).*

### 3. Initialize Supabase Data
Run the core DDL found in `integrations/supabase_writer.py` -> `create_tables()` inside your Supabase SQL Editor before the very first script run to create your schemas.

---

## 🏗️ Architecture — The Hybrid Model

This simulator operates on a **Hybrid Architecture** combining real-time user actions with background operations:

### 1. Real-Time Event Gateway (`app.py`)
A live Flask backend serving the frontend (Landing Page, Onboarding, Dashboard). It processes real-time user intent:
*   **Signups:** Generates HubSpot Contacts + Meta Leads instantly.
*   **Stripe Checkout:** Handles the "Upgrade" clicks, dynamically creating real Stripe checkout sessions based on the selected plan (Starter/Pro).
*   **Support & Telemetry:** Wires dashboard "Help" buttons directly to Freshdesk and generic actions to PostHog.

### 2. Daily Operations Batch (`main_revops_writer.py`)
The background engine. Real businesses don't just have signups; they have monthly billing cycles, background usage, and churn. This script runs daily to generate:
*   Historical Stripe Invoices (payments, retries, failures).
*   PostHog feature usage (or errors predicting churn).
*   Sales Intelligence transcripts into Supabase.

Both systems use the **exact same** configuration (`config.py`) and integrations, meaning data is perfectly synchronized.

---

## ▶️ Running the Engine

### Option A: The Real-Time Gateway (Interactive UI)
```bash
python3 saas-body/app.py
```
*Go to `http://localhost:5050` to experience the live landing page, onboarding wizard, and interactive dashboard.*

### Option B: The Daily Batch Generator
```bash
# Run the full 7-layer Revenue Engine
python3 main_revops_writer.py --all

# Run specific layers only
python3 main_revops_writer.py --services hubspot stripe posthog

# Simulate without writing (dry run)
python3 main_revops_writer.py --dry-run
```

**Expected output:**
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

## 🚀 Deployment & Safety

### Where to deploy?
If you want to host this live as a portfolio piece to show employers/clients:
1. **Render.com or Railway.app** — Perfect for hosting the `app.py` Flask server. Just set the `Start Command` to `gunicorn -w 2 -b 0.0.0.0:$PORT saas-body.app:app`.
2. **GitHub Actions** — Perfect for hosting the `main_revops_writer.py` daily batch job using cron.

### Is it safe?
> [!WARNING]
> **This is safe ONLY if you strictly use Sandbox/Test API keys.**
> If deployed publicly, anyone who fills out the landing page form will create a record in your CRM. If you use a real HubSpot or Stripe account, you will generate massive amounts of junk data and potentially real charges.
> **Recommendation:** Keep your `.env` variables securely in your hosting provider's Secrets manager and double-check that every key says `test` or `sandbox`.

**Built for Revenue. Designed for Scale. 🚀**
