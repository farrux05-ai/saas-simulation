# SentinelGuard AI — Business Model & Revenue Logic

> This document explains the **"why"** behind every data point in the simulation.
> Every HubSpot deal stage, every Stripe invoice, every Freshdesk ticket exists
> because a real business event would trigger it. Read this first.

---

## 🏢 What is SentinelGuard AI?

**SentinelGuard AI** is a Cloud Security Posture Management (CSPM) platform.

It continuously scans cloud infrastructure (AWS, GCP, Azure) for:
- Misconfigured S3 buckets, IAM roles, and network policies
- Compliance gaps (SOC 2, ISO 27001, CIS Benchmarks)
- Active attack paths between misconfigured resources
- Auto-remediation of critical vulnerabilities (Pro tier)

**The business problem it solves:** Engineering teams at B2B SaaS companies
are drowning in cloud alerts. SentinelGuard cuts through the noise by
**prioritizing findings by business impact**, not just severity score.

---

## 🎯 ICP — Ideal Customer Profile

The simulation generates exactly **2 types of buyers** matching real B2B SaaS ICP criteria:

### Primary ICP (High ACV)
| Attribute | Value |
|---|---|
| **Company Stage** | Series A / Series B |
| **Headcount** | 50–500 employees |
| **Cloud Spend** | $20k–$200k/month |
| **Geography** | North America, Western Europe |
| **Industry** | FinTech, HealthTech, Developer Tools, B2B SaaS |
| **Compliance Pressure** | SOC 2 Type II, ISO 27001, HIPAA |

### Buyer Personas (who signs the contract)
| Persona | Title | Pain Point | Decision Trigger |
|---|---|---|---|
| **Champion** | DevOps Lead / Security Eng | Drowning in Alerts | Engineering productivity lost |
| **Economic Buyer** | CTO / VP Engineering | Compliance deadline | SOC 2 audit in 90 days |
| **Influencer** | CISO | Board reporting | Need board-ready security metrics |

> **In the simulation:** `jobtitle` fields in HubSpot contacts map directly to these personas.
> `CISO` persona triggers a higher `hubspotscore` and faster `dealstage` progression.

---

## 💰 Pricing Model

SentinelGuard uses **seat-independent, asset-based pricing** — the industry standard for CSPM.
The customer pays based on the number of **cloud assets** (EC2 instances, S3 buckets, Lambda functions) being scanned, not the number of users.

### Pricing Tiers

| Tier | Assets Covered | Price | ACV | Target |
|---|---|---|---|---|
| **Starter** | Up to 500 assets | $1,000/month | $12,000 | Seed-stage, small eng teams |
| **Pro** | Up to 5,000 assets | $5,000/month | $60,000 | Series A, compliance-focused |
| **Enterprise** | Unlimited assets | Custom | $120k–$300k | Series B+, multi-cloud |

### Why asset-based pricing?
- Scales naturally with customer growth (more infra = more revenue).
- Aligns cost with value — bigger companies pay more because they get more protection.
- Predictable for the customer — no per-seat surprises as the team grows.

### Revenue composition in the simulation
The Stripe layer generates realistic billing data:
```
Plan       → Stripe Price ID  → Monthly MRR contribution
Starter    → price_starter    → $1,000/mo  ← "DataFlow LLC" (active)
Pro        → price_pro        → $5,000/mo  ← "Acme Corp" (at-risk, auto_remediation_fail)
Enterprise → price_enterprise → Custom     → Contract outside Stripe (simulated via HubSpot deal)
```

---

## 🚀 GTM Motion — Go-To-Market Strategy

SentinelGuard uses a **hybrid PLG + Sales-Assisted** motion, common for A-series security tools.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GTM FUNNEL (End-to-End)                          │
├──────────┬──────────────────────────────────────────────────────────┤
│  Stage   │  What Happens                          │ System          │
├──────────┼──────────────────────────────────────────────────────────┤
│ TOFU     │ LinkedIn Thought Leadership + G2 Reviews│ Meta Ads        │
│ Lead     │ "Free Security Audit" CTA on landing    │ HubSpot → Lead  │
│ MQL      │ Onboarding completed (4 steps)          │ HubSpot → MQL   │
│ PQL      │ "Upgrade" button clicked in dashboard   │ PostHog signal  │
│ SQL      │ AE reaches out after PQL signal         │ HubSpot → SQL   │
│ Demo     │ 30-min discovery + live scan demo       │ call_transcripts │
│ Close    │ Contract signed → Stripe subscription   │ Stripe → MRR    │
│ Expand   │ Asset growth → automatic tier upgrade   │ Stripe upsell   │
│ Churn    │ Competitor displacement / budget cut    │ Freshdesk signals│
└──────────┴──────────────────────────────────────────────────────────┘
```

### Demand Generation Channels

| Channel | Type | Attribution in Data |
|---|---|---|
| LinkedIn Ads | Paid Social | `hs_analytics_source = PAID_SOCIAL` |
| Google Search | Paid Search | `hs_analytics_source = PAID_SEARCH` |
| G2 / Capterra Reviews | Referral | `hs_analytics_source = REFERRALS` |
| Security blog (SEO) | Organic | `hs_analytics_source = ORGANIC_SEARCH` |
| Newsletter (Pragmatic Eng.) | Email | `hs_analytics_source = EMAIL_MARKETING` |
| Developer community (word-of-mouth) | Direct | `hs_analytics_source = DIRECT_TRAFFIC` |

### PLG Motion (Product-Led Growth)
The "Free Security Audit" hook drives PLG:
1. Prospect enters email on landing page → **HubSpot Contact (Lead)**
2. Completes 4-step onboarding wizard → **HubSpot Contact (MQL)**
3. Sees dashboard with real findings — but "Fix Issue" is paywalled.
4. Clicks "Fix Issue" / "One-Click Remediation" → **PQL Signal to Sales**
5. AE reaches out within 24 hours (SLA for PQL).

> **In the simulation:** The `showPaywall()` function in `dashboard.html`
> calls `/api/upgrade-intent` which promotes the contact to `salesqualifiedlead`
> in HubSpot and fires a `Upgrade Prompt Clicked` event to PostHog.
> This is **exactly** how PLG SaaS tools capture intent.

---

## 📊 Revenue Metrics — What Gets Measured

These are the KPIs any A-series RevOps team tracks. Every metric maps to the data the simulation generates.

### North Star Metrics
| Metric | Formula | Source |
|---|---|---|
| **MRR** | Sum of active subscription MRR | Stripe subscriptions |
| **ARR** | MRR × 12 | Stripe |
| **Net Revenue Retention (NRR)** | (Start MRR + Expansion - Churn) / Start MRR | Stripe cohort analysis |
| **Churn Rate** | Canceled MRR / Start MRR | Stripe `status = canceled` |
| **CAC** | Marketing Spend / New Customers | Meta Ads → Stripe join |
| **LTV** | ARPU / Churn Rate | Stripe |
| **LTV:CAC Ratio** | LTV / CAC | Target: >3x for A-series |

### Funnel Velocity Metrics
| Metric | Source |
|---|---|
| Lead → MQL Conversion | HubSpot `lifecyclestage` transitions |
| MQL → SQL Time (Days) | HubSpot deal `createdate` vs `hs_date_entered_salesqualifiedlead` |
| SQL → Close Rate | HubSpot `dealstage = closedwon` / total SQLs |
| Average Deal Size | HubSpot `amount` |
| Sales Cycle Length | HubSpot deal open date → close date |

### Product Health Metrics (PLG signals)
| Metric | Source |
|---|---|
| Onboarding Completion Rate | PostHog `onboarding_completed` |
| Feature Adoption (DAU) | PostHog `feature_used` events |
| Support Ticket Rate | Freshdesk tickets per company |
| Churn Prediction Score | PostHog `latency_alert` + `export_failed_error` frequency |

---

## 🔗 How Business Events Drive Data

Every "business event" in the real world creates a chain reaction across systems.
This is what makes the simulation realistic:

### Event Chain: "New Customer Signs Up"
```
1. Meta Ads     → Lead conversion event (CAPI)
2. HubSpot      → Contact (Lead) + Company + Association
3. Stripe       → Customer record created (no subscription yet)
4. PostHog      → $identify + "User Signed Up" event
```

### Event Chain: "Free Trial → Upgrade"
```
1. PostHog      → "Upgrade Prompt Clicked" (PQL signal)
2. HubSpot      → Contact promoted to SQL
3. HubSpot      → Deal stage → "qualifiedtobuy"
4. Stripe       → Checkout Session created → Subscription activated
5. Stripe       → First invoice generated
```

### Event Chain: "Customer At Risk (Churn Signal)"
```
1. PostHog      → High frequency "latency_alert" events (>5 in 7 days)
2. Freshdesk    → URGENT ticket auto-generated from the same company
3. HubSpot      → AE note added (best-effort)
4. call_transcripts → Discovery call logged with objection_raised field
```
> **In the simulation:** "Acme Corp" is the `AT_RISK` persona.
> It generates PostHog error events AND Freshdesk tickets with priority=4 (Urgent).
> A dbt model can join these to predict churn **before** the renewal date.

### Event Chain: "Customer Churns"
```
1. HubSpot      → Deal marked "closedlost"
2. Stripe       → Subscription status → "canceled"
3. Stripe       → Final invoice (prorated)
4. call_transcripts → Closing call with outcome="churned", objection="budget_cut"
```
> **In the simulation:** "CloudNine Co" is the `CHURNED` persona.
> Its Stripe subscription has `status=canceled` and its call transcript
> has `objection_raised = "budget_cut"`.

---

## 🧠 Why This Architecture Mirrors Real A-Series Companies

| Real Company Decision | Simulated With |
|---|---|
| "We use HubSpot not Salesforce" | A-series can't afford Salesforce licenses at scale |
| "We use Stripe not custom billing" | Fastest time to revenue, PLG-friendly |
| "We track product with PostHog" | Open-source first, privacy-compliant, EU-friendly |
| "Support on Freshdesk" | Cost-efficient, Zendesk alternative for <$5M ARR |
| "Supabase as our app DB" | Postgres-native, DWH-ready, no separate data layer needed |
| "Meta/LinkedIn for demand gen" | B2B SaaS at A-series lives on LinkedIn ads + G2 reviews |

---

*This document is part of the SentinelGuard AI RevOps Engine Simulator.*
*For technical data flow details, see [data_lifecycle.md](./data_lifecycle.md).*
*For setup instructions, see the [main README](../README.md).*
