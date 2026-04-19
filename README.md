# RevOps Data Writer 🚀

[![Production Ready](https://img.shields.io/badge/status-production--ready-success)](https://github.com/farrux05-ai/saas-simulation)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional-grade **B2B SaaS Data Ingestion Pipeline**. This tool populates your Modern Data Stack (MDS) sandbox accounts with high-fidelity, integrated test data covering the full customer lifecycle: **Marketing → Sales → Finance → Product Analytics → Support**.

---

## 💎 Professional Features

This isn't just a mock data generator; it’s a **System Simulator** designed for data engineers and analysts:

*   **💳 Financial High-Fidelity (Stripe)**: Generates **12 months of historical invoices** per subscription. Perfect for testing MRR Waterfall models, churn analytics, and billing cohort analysis.
*   **📅 Data Warehouse Built-ins (Supabase)**: Automatically populates a full `dim_date` (Calendar dimension) table. Ready-to-join for all your time-series dbt models.
*   **🛡️ Smart Clock-Drift Protection (Analytics)**: Implementations for Mixpanel and PostHog include automated timestamp buffers to prevent "Future Time" API rejection—a common pitfall in data simulation.
*   **🔄 SCD Type 2 Ready (HubSpot)**: Simulates deal progression and company status updates on every run, allowing you to stress-test your **dbt snapshots** and historical lineage.
*   **🎭 Full-Funnel Attribution**: Simulates marketing touchpoints (anonymous Page Views, Demo Requests) *before* a user exists in the CRM, creating a realistic Join-key for attribution modeling.

---

## 🎯 Use Cases

1.  **Modern Data Stack Practice**: Connect Fivetran, Airbyte, or Meltano to professional-grade source data.
2.  **dbt Analytics Engineering**: Build production-level models for **MRR**, **LTV**, **CAC**, and **Funnel Conversion**.
3.  **Visualization Dashboards**: Create stunning Looker, Sigma, or Streamlit dashboards with data that actually "makes sense."

---

## 🛠️ Setup & Execution

### 1. Initialize Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Create a `.env` file based on `.env.example`. You will need access tokens for:
- HubSpot (Private App)
- Stripe (Test Secret Key)
- Supabase (Project URL & Service Key)
- Mixpanel/PostHog (Project Tokens)
- Freshdesk (API Key)

### 3. Run the Pipeline
```bash
# Populate all configured services
python main_revops_writer.py --all

# Target specific services
python main_revops_writer.py --services stripe supabase mixpanel
```

---

## 📊 Data Schema Reference

| Platform | Domain | Simulation Depth |
| :--- | :--- | :--- |
| **HubSpot** | CRM | Contacts, Companies, Deals with Stage History & SCD Deltas. |
| **Stripe** | Billing | Customers, Subscriptions, and **Historical Invoices (1yr back)**. |
| **Supabase** | Warehouse | App Database state + **Professional Date Dimension (`dim_date`)**. |
| **Mixpanel** | Product | Full behavioral funnel (Marketing -> Signup -> Feature Engagement). |
| **PostHog** | Product | Heatmap-ready event streams with user identification logic. |
| **Freshdesk**| Support | Ticket volume correlated with subscription health scores. |

---

## ⚠️ Important Implementation Notes

### Supabase Setup
The `dim_date` and core tables require initial DDL. You can find the required SQL script in the `supabase_setup.sql` artifact or in the `integrations/supabase_writer.py` comments.

### GitHub Actions
Automate your data growth by enabling the included workflow in `.github/workflows/revops_ingest.yml`. This ensures your warehouse "grows" 1% every day, simulating a real SaaS business.

---

> [!IMPORTANT]
> **Privacy Warning**: Only use this tool in **Sandbox/Test** environments. This script performs write operations that could clutter production dashboards if misconfigured.

**Happy Data Engineering! 🚀**
