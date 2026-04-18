# RevOps Data Writer 🚀

A realistic B2B SaaS data ingestion pipeline generator. This script populates your sandbox or free trial accounts with realistic test data for common RevOps platforms.

## 📋 Features

The script writes realistic B2B SaaS data to the following platforms:

- **HubSpot**: Contacts, Companies, Deals (CRM data)
- **Stripe**: Customers, Subscriptions, One-time payments
- **Supabase**: Companies, Users, Events, Subscriptions (Database records)
- **Mixpanel**: Product analytics events, User profiles
- **PostHog**: Product analytics events, User profiles
- **Freshdesk**: Support tickets
- **Meta Ads**: Conversion events (Leads, Signups, Purchases)

## 🎯 Objective

Populate each platform with realistic data so you can practice data extraction (ELT), transformation, and building analytics dashboards on top of a "live" system.

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

Create a `.env` file and add the required keys:

```bash
# HubSpot (https://app.hubspot.com/)
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Stripe (https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=[YOUR_STRIPE_SECRET_KEY]

# Supabase (https://supabase.com/dashboard/project/_/settings/api)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Mixpanel (https://mixpanel.com/settings/project/)
MIXPANEL_PROJECT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MIXPANEL_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# PostHog (https://app.posthog.com/project/settings)
POSTHOG_API_KEY=phc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
POSTHOG_PROJECT_ID=12345

# Freshdesk (https://yourcompany.freshdesk.com/a/admin/api_settings)
FRESHDESK_DOMAIN=yourcompany.freshdesk.com
FRESHDESK_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# Meta Ads (https://developers.facebook.com/apps/)
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
META_ACCOUNT_ID=act_123456789
```

## 🚀 Usage

### Write to all configured services

```bash
python main_revops_writer.py --all
```

### Write to specific services

```bash
# HubSpot and Stripe only
python main_revops_writer.py --services hubspot stripe
```

### Check configuration

```bash
python main_revops_writer.py --check-config
```

### Dry run (Simulate without writing)

```bash
python main_revops_writer.py --dry-run --all
```

## 📊 Data Quantities (Default)

- **HubSpot**: 15 contacts, 8 companies, 12 deals
- **Stripe**: 15 customers (~70% with subscriptions)
- **Supabase**: 40 companies, ~200 users, ~2000 events
- **Mixpanel/PostHog**: 25 users, 30 days of activity
- **Freshdesk**: 25 support tickets
- **Meta Ads**: 50 conversion events

## 📁 Project Structure

```
ingestion_practice/
├── main_revops_writer.py    # Main orchestrator script
├── config.py                 # Configuration management
├── utils/
│   └── logger.py             # Logging utility
├── integrations/
│   ├── hubspot_writer.py     # HubSpot CRM writer
│   ├── stripe_writer.py      # Stripe payment writer
│   ├── supabase_writer.py    # Supabase DB writer
│   ├── mixpanel_writer.py    # Mixpanel analytics writer
│   ├── posthog_writer.py     # PostHog analytics writer
│   ├── freshdesk_writer.py   # Freshdesk ticket writer
│   └── meta_ads_writer.py    # Meta Ads conversion writer
├── .env                      # API keys (git-ignored)
└── README.md                 # This file
```

## ⚠️ Important Notes

### 1. Test/Sandbox Environments
ONLY use this script on **test/sandbox** environments. Never use production accounts!

### 2. API Rate Limits
Some platforms have rate limits (e.g., HubSpot 100 requests/10s). The script includes basic batching, but if you hit limits, wait a few minutes and retry.

### 3. Supabase Setup
Ensure you have created the necessary tables (`companies`, `users`, `events`, `subscriptions`) in your Supabase project before running the script.

## 📝 License

This is a learning project. Use at your own risk!

---

**Happy data writing! 🎉**
