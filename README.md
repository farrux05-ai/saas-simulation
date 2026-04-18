# RevOps Data Writer 🚀

A professional-grade B2B SaaS data ingestion pipeline generator. This script populates your sandbox or free trial accounts with realistic, integrated test data across the entire customer lifecycle (Marketing -> Sales -> Finance -> Support).

## 📋 Professional Features

This isn't just a "mock data" script; it simulates a **living, breathing B2B SaaS system**:

- **Real-Time Funnel Simulation**: Generates Marketing signals (Page Views, Demo Requests) in Mixpanel/PostHog before a user even signs up.
- **Advanced CRM Workflow**: HubSpot interaction with Deal Stage advancement and CRM Activities (Calls, Meetings, Emails) linked to the pipeline.
- **Financial Modeling**: Full Stripe Invoice history (3-12 months back) for every subscription, including payment failures and retries for MRR Waterfall testing.
- **SCD Type 2 Ready**: Random status updates (e.g., Company Churn, Plan Upgrades) on every run, enabling dbt Snapshot testing.
- **Data Warehouse Built-ins**: Automatically populates a `dim_date` (Calendar dimension) in Supabase for professional time-series modeling.

## 🎯 Objectives

1. **Practice ELT/ETL**: Connect Fivetran, Airbyte, or Meltano to real APIs.
2. **Build dbt Models**: Use professional schemas to build MRR Waterfalls, Attribution models, and Sales Velocity dashboards.
3. **Data Orchestration**: Schedule the pipeline via GitHub Actions to simulate daily data growth.

## 🛠️ Setup

### 1. Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 2. Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file and add the required keys (see `.env.example` for details):

```bash
HUBSPOT_ACCESS_TOKEN=...
STRIPE_SECRET_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
# ... etc
```

## 🚀 Usage

### Write to all configured services
```bash
python main_revops_writer.py --all
```

### Write to specific services
```bash
python main_revops_writer.py --services hubspot stripe
```

### Dry run (Simulate without writing)
```bash
python main_revops_writer.py --dry-run --all
```

## 📊 Simulated Data Schema

| Platform | Objects/Tables | Simulation Detail |
| :--- | :--- | :--- |
| **HubSpot** | Contacts, Companies, Deals, Activities | Stage Progression, Sales Touchpoints |
| **Stripe** | Customers, Subs, Invoices | 3-12mo Billing History, Retries |
| **Supabase** | Companies, Users, Subs, Events, dim_date | Real DB primary/foreign key relationships |
| **Mixpanel** | Profiles, Actions, Marketing Signals | Demo Request -> Signup -> Usage funnel |
| **Freshdesk**| Tickets, Customers | Support volume vs. Subscription status |
| **Meta Ads** | Conversions | Lead/Signup attribution signals |

## ⚠️ Important Notes

### 1. Test/Sandbox Environments
ONLY use this script on **test/sandbox** environments. NEVER use production accounts!

### 2. Supabase Table Creation
The `supabase_writer.py` includes a commented-out SQL block for the required table DDLs (Companies, Users, Subscriptions, Events, dim_date). Ensure these exist before running.

### 3. Automated Scheduling
This project includes a `.github/workflows/revops_ingest.yml` to automate daily data generation using GitHub Actions.

---

**Happy data modeling! 🎉**
