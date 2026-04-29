# SentinelGuard AI — Business Model & Go-To-Market Playbook

> **Document purpose:** This is the operational blueprint for SentinelGuard AI — a simulated
> Cloud Security Posture Management (CSPM) company. Every data point, persona, and funnel stage
> described here is reflected in live sandbox API data (HubSpot, Stripe, PostHog, Freshdesk,
> Meta Ads). The goal is to model a real B2B SaaS company with enough fidelity that the revenue
> signals, churn signals, and sales pipeline look indistinguishable from production data.

---

## 1. What SentinelGuard AI Actually Does

SentinelGuard AI is a **Cloud Security Posture Management (CSPM)** platform. It connects to a
customer's cloud environment (AWS, Azure, GCP) using a read-only IAM role and, within minutes,
produces a full inventory of misconfigurations, exposed credentials, and exploitable attack paths.

The key product insight: **security teams are drowning in alerts**. Every existing tool (AWS
Security Hub, Wiz, Prisma Cloud) produces thousands of findings per week. SentinelGuard
differentiates by doing three things differently:

1. **Contextual Risk Scoring** — A public S3 bucket containing only static HTML is not the same
   risk as a public S3 bucket containing database backups. SentinelGuard maps *what is exposed*
   and *who can reach it* before assigning severity. This removes 80% of false-positive noise.

2. **Attack Path Graphs** — Instead of reporting "IAM role has excessive permissions", SentinelGuard
   draws the full exploit chain: `Public Internet → S3 prod-user-data (Public ACL) → Lambda
   data-sync (AdminAccess role) → RDS production-db (PII)`. The buyer sees *exactly* what a
   real attacker would do, step by step.

3. **Auto-Remediation Pull Requests** — When a misconfiguration is found, SentinelGuard generates
   the corrected Infrastructure-as-Code (Terraform/CloudFormation) and opens a GitHub PR
   automatically. The engineer reviews and merges — no manual fix required.

### Why This Is Hard to Build (and Why Customers Pay for It)

The naive version of this product is a rules engine that checks 200 CIS benchmark controls.
That exists everywhere and is free. The defensible, paid version requires:

- A **graph database** that models cloud resources as nodes and permissions as edges, so attack
  paths can be traversed programmatically.
- **ML-based data classification** to identify PII, credentials, and secrets inside storage
  buckets and databases (DSPM layer).
- A **policy-as-code engine** that can generate correct remediation code across 6 cloud providers
  and dozens of IaC frameworks.

This explains the pricing. You are not paying for a checklist. You are paying for a security
analyst who works 24 hours a day and never makes a mistake.

---

## 2. Revenue Model

### 2.1 How Money Is Made

SentinelGuard charges on a **value metric**: the number of cloud assets scanned per month. An
"asset" is any billable cloud resource — EC2 instance, S3 bucket, Lambda function, RDS instance,
IAM role, Kubernetes pod.

This is intentional. The customer's cloud grows as their company grows. Revenue expands
automatically without requiring the sales team to renegotiate contracts. This is called
**Net Revenue Retention (NRR)** and it is the single most important metric in B2B SaaS.

| Tier | Price | Asset Limit | Billing | GTM Motion |
|---|---|---|---|---|
| **Free Audit** | $0 | 500 assets, one-time | N/A | Self-serve |
| **Starter** | $1,000 / month | 500 assets | Stripe (card) | Self-serve |
| **Pro** | $5,000 / month | 5,000 assets | Stripe (card) | Self-serve + Sales-touch |
| **Enterprise** | $120,000+ / year | Unlimited | Invoice (Net-30) | Sales-led (HubSpot) |

**What the Free Audit does:** A prospect connects their AWS account, the scan runs in 5 minutes,
and they see their 3 most critical findings. The "Fix Issue" button and the full Attack Path graph
are paywalled. This is not generosity — it is the most efficient sales motion that exists. The
customer has already confirmed the product works in *their* environment before speaking to a
salesperson. The sales team never wastes time proving value; they only negotiate terms.

### 2.2 Revenue Expansion (The "Land and Expand" Model)

An Enterprise customer signs a contract for 10,000 assets at $120,000/year. Six months later
their engineering team deploys a new Kubernetes cluster with 800 pods. Each pod counts as an
asset. The account now has 12,400 assets. At their contracted rate, that triggers a $28,800
overage bill — automatically, without a sales call.

This is why NRR at CSPM companies like Wiz exceeds 130%. Every dollar of ARR (Annual Recurring
Revenue) from existing customers grows by 30% per year on its own. The sales team's job is to
acquire *new* logos, not re-sell existing ones.

### 2.3 What the Stripe Simulation Models

The sandbox Stripe account contains:

- **Customers** mapped 1:1 to company personas (Acme Corp, TechStart Inc, DataFlow LLC, etc.)
- **Subscriptions** at the correct plan tier for each persona's lifecycle stage
- **Invoice history** with realistic payment failures (≈8% failure rate) and retry patterns
- **One-time payments** for Professional Services (onboarding, training, custom integrations)

The invoice failure rate is not cosmetic. An account with two consecutive failed invoices is a
churn signal that Customer Success should act on within 48 hours. This cross-signal (Stripe
failure → Freshdesk escalation → HubSpot task) is what the simulation is designed to produce.

---

## 3. Ideal Customer Profile (ICP)

### 3.1 Who Buys and Who Uses

In B2B SaaS, the person who uses the product and the person who signs the check are almost always
different. Getting this wrong is the most common reason enterprise sales deals stall.

| Dimension | The User | The Buyer |
|---|---|---|
| **Title** | Security Engineer, DevOps Engineer, Cloud Architect | CISO, VP of Engineering, VP of Infrastructure |
| **Pain** | Too many alerts, no remediation workflow, agents break CI/CD | Compliance failures, board-level risk reporting, audit findings |
| **Success Metric** | MTTR (Mean Time to Remediate) reduced from days to hours | SOC 2 Type II passed, zero critical findings at audit time |
| **Decision Power** | Strong influence on tool selection, weak signing authority | Full budget authority, often not technical |
| **Entry Point** | Free Audit (self-serve), GitHub repo, Hacker News | Analyst report, CISO peer referral, Enterprise RFP |

The implication for the sales motion: **the Engineer starts the trial, the CISO signs the contract**.
A deal that only has engineer champions and no CISO engagement will not close. The HubSpot pipeline
tracks both contacts, and the deal stage gates on whether a "CISO Engaged" property has been set.

### 3.2 Target Firmographics

| Signal | Why It Matters |
|---|---|
| **200–5,000 employees** | Large enough to have dedicated security headcount, small enough that the CISO still cares about tooling decisions |
| **Multi-cloud or AWS-heavy** | Single-cloud, on-prem companies are not the target; their attack surface is too simple |
| **Fintech, Healthcare, SaaS** | Regulatory pressure (PCI-DSS, HIPAA, SOC 2) creates a *mandatory* spend category for security |
| **Kubernetes / Terraform users** | Indicates modern DevOps culture; these teams value agentless scanning and IaC remediation |
| **Recent Series B or C funding** | Post-funding, security becomes a board topic; CISO is often hired at this stage |

### 3.3 Disqualifying Signals (Who We Should Not Pursue)

- Companies with fewer than 50 employees. Their cloud footprint is too small to justify the price.
- Companies still on physical servers or a single data center. CSPM is a cloud-native problem.
- Companies where security is "handled by IT". They will not have a budget line for a dedicated CSPM tool.
- Government / defense. Procurement cycles are 18+ months and require FedRAMP authorization we do not have.

---

## 4. Customer Lifecycle & Simulated Personas

The simulation generates five archetypes that represent every meaningful state in a SaaS revenue
funnel. Each persona drives correlated signals across all six API layers.

### Persona 1 — Acme Corp (`at_risk`)

**Reality:** Acme Corp is a 450-person Fintech company, 18 months into their Pro subscription.
They were a model customer — high engagement, two referrals given — until the report export
feature started timing out 6 weeks ago. The bug has not been fixed. Their CISO is presenting
board-level risk metrics next week and cannot export the required PDF. An executive sponsor is
quietly evaluating Wiz.

**What the data shows:**
- PostHog: 14 consecutive days of `export_failed_error` events, load times >8,000ms
- Freshdesk: 3 open Urgent tickets tagged `report_export`, `at_risk_customer`
- HubSpot: Deal stage `decisionmakerboughtin`, Priority `high`, Note from CS rep added 5 days ago
- Stripe: Subscription current, next invoice in 12 days — but NPS score is 4/10

**The correct business response:** Customer Success escalates to Engineering (P0 bug). Account
Executive schedules a call with the CISO within 24 hours and offers a 2-month credit. If resolved,
Acme becomes an expansion candidate (Azure account not yet connected).

---

### Persona 2 — TechStart Inc (`stalled`)

**Reality:** TechStart is a 180-person SaaS company in a 14-day free trial. They signed up
after a LinkedIn ad, completed onboarding in 45 minutes, and connected their AWS account. The
product genuinely impressed their Security Engineer — until he tried to connect Jira and found
the integration does not exist yet. He filed a feature request ticket and went quiet. The trial
expires in 4 days.

**What the data shows:**
- PostHog: Strong onboarding engagement (days 1–10), then zero sessions for 10 days
- Freshdesk: 1 open ticket, Priority Low, tagged `feature_question`
- HubSpot: Deal stage `appointmentscheduled`, no CISO contact record, Priority `medium`
- Stripe: Trial customer, no payment method on file

**The correct business response:** Sales Development Rep (SDR) sends a manual outreach email
with a 7-day trial extension offer. Product team adds Jira to the integration roadmap with an
ETA. If TechStart extends and integrates, they convert within 30 days — their AWS account has
2,400 assets, putting them solidly in Pro territory.

---

### Persona 3 — DataFlow LLC (`happy_path`)

**Reality:** DataFlow is a 320-person data infrastructure company, 8 months into their Pro
subscription. Their DevOps team uses SentinelGuard daily. They have connected all three cloud
providers. The Security Engineering Lead was promoted last month partly because her team achieved
SOC 2 Type II with zero audit findings — she credits SentinelGuard in the report. She has
already mentioned the platform to two CISO peers at a conference.

**What the data shows:**
- PostHog: Daily sessions, `reports_export` events every 3 days, zero errors
- Freshdesk: 1 closed Low-priority ticket ("how to schedule weekly reports?")
- HubSpot: Deal `closedwon`, existing account, expansion deal opened for GCP connection
- Stripe: 8 months of clean payment history, last invoice paid within 1 hour of generation

**The correct business response:** Account Executive sends a quarterly business review (QBR)
request. The expansion play: DataFlow has 5,000 assets on Pro. If they add GCP (estimated 800
additional assets), they cross the Enterprise threshold. AE prepares a custom Enterprise quote
with a 3-year prepaid option (15% discount) that saves DataFlow $54,000/year while locking in
$324,000 of ARR for SentinelGuard.

---

### Persona 4 — CloudNine Co (`churned`)

**Reality:** CloudNine was a Starter plan customer — 90 employees, 420 cloud assets, $1,000/month.
They canceled 50 days ago. Post-mortem: they hired an in-house security engineer who built a
custom AWS Config rules set. The tool was "good enough" for their current scale. They also felt
the product was overpriced for a company their size.

**What the data shows:**
- PostHog: Last event was 50 days ago. One `Session Started` event, then silence.
- Freshdesk: No tickets (they never had a problem, they just left)
- HubSpot: Deal `closedlost`, Reason: "Built in-house alternative", Lifecycle: `other`
- Stripe: Subscription canceled, no outstanding invoices

**The correct business response:** No immediate action. This account goes into a 6-month re-engagement
sequence. The trigger to re-engage: when CloudNine grows past 500 employees (monitored via LinkedIn
Sales Navigator), the in-house tool becomes inadequate and SentinelGuard's outreach will land differently.

---

### Persona 5 — DevOps Pro (`new_lead`)

**Reality:** DevOps Pro is a 95-person platform engineering consultancy. Their CTO saw a
SentinelGuard post on LinkedIn today, clicked through, landed on the pricing page, read the
attack path documentation, and started the Free Audit 20 minutes ago. They have not connected
a cloud account yet. The CTO is the likely buyer and the likely user — this is common at
sub-100-person companies.

**What the data shows:**
- PostHog: `User Signed Up` (signup_source: `paid_ad`), `Onboarding Started`, `Pricing Page Viewed`
- Meta Ads: `CompleteRegistration` conversion event fired against the LinkedIn retargeting pixel
- Freshdesk: No tickets
- HubSpot: Contact created, Lifecycle `lead`, no company record yet, no deal
- Stripe: No customer record

**The correct business response:** Marketing automation (HubSpot workflow) sends a welcome email
immediately with the "Getting Started in 5 Minutes" guide. If DevOps Pro connects a cloud account
within 24 hours, the workflow escalates them to MQL (Marketing Qualified Lead) and routes them
to an SDR for a light-touch outbound call. The SDR's job is not to pitch — it is to remove
friction (help with IAM role setup, answer technical questions).

---

## 5. The Full Revenue Funnel (End-to-End)

```
Meta Ads (Paid)
LinkedIn Organic
SEO / Hacker News
        │
        ▼
Landing Page (Free Audit CTA)
  ─ PostHog: Page Viewed, Pricing Page Viewed
  ─ Meta Pixel: ViewContent → Lead
        │
        ▼
Sign-Up Form (Name, Work Email, Company)
  ─ PostHog: User Signed Up
  ─ Meta Pixel: CompleteRegistration
  ─ HubSpot: Contact Created (Lifecycle: lead)
        │
        ▼
Onboarding (Cloud Provider → IAM Role → Scan)
  ─ PostHog: Onboarding Started / Completed
  ─ HubSpot: Lifecycle → MQL (if cloud connected)
  ─ Meta Pixel: StartTrial
        │
        ▼
First Value Moment (Attack Path Report Delivered)
  ─ PostHog: Session Started, Feature Used (dashboard)
  ─ HubSpot: Deal Created (stage: appointmentscheduled)
        │
        ▼
Paywall Hit (Auto-Remediate / Full Report clicked)
  ─ PostHog: Upgrade Prompt Viewed
  ─ HubSpot: Deal stage → qualifiedtobuy
        │
   ┌────┴────┐
   │         │
Self-Serve  Sales-Led
(Stripe)    (HubSpot Enterprise)
   │         │
   ▼         ▼
Subscription  Contract Signed
  ─ Stripe: Customer + Subscription Created
  ─ PostHog: Subscription Started
  ─ HubSpot: Deal → closedwon
  ─ Meta Pixel: Subscribe / Purchase
        │
        ▼
Post-Sale (Customer Success)
  ─ PostHog: Daily feature usage, Report Generated
  ─ Freshdesk: Support tickets (health signal)
  ─ Stripe: Monthly invoice paid
  ─ HubSpot: Expansion deal opened (new cloud / more assets)
```

---

## 6. Key Business Metrics (What We Measure)

These are the metrics a real CSPM company's board would review monthly. The simulation generates
the raw events needed to compute each one.

| Metric | Definition | Healthy Range | Source |
|---|---|---|---|
| **MRR** | Monthly Recurring Revenue (sum of all active subscriptions) | Growing ≥15% MoM in early stage | Stripe |
| **NRR** | Net Revenue Retention: (MRR this month / MRR last month) including expansions and churns | >110% is excellent, >130% is world-class | Stripe |
| **CAC** | Customer Acquisition Cost: total sales + marketing spend / new customers acquired | <12 months of customer ACV | Meta Ads, HubSpot |
| **Payback Period** | Months to recover CAC from gross margin | <18 months for self-serve, <24 for enterprise | Stripe + CAC |
| **Activation Rate** | % of sign-ups who connect a cloud account within 7 days | >40% is healthy | PostHog |
| **Trial-to-Paid** | % of free trials that convert to a paid plan | 15–25% is industry standard | PostHog + Stripe |
| **Churn Rate** | % of MRR lost to cancellations per month | <2% monthly (=<22% annually) | Stripe |
| **CSAT / NPS** | Customer satisfaction score | NPS >40 is strong | Freshdesk |
| **Time-to-Value** | Minutes from sign-up to first attack path report delivered | <10 minutes | PostHog |
| **PQL Rate** | % of free users who qualify as Product Qualified Leads | >5% of free sign-ups | PostHog (engagement score) |

---

## 7. How the Simulation Stack Works

Each API layer captures a different signal from a real customer's journey. The same company
persona writes consistent, cross-referenced data to every platform simultaneously.

| Layer | Platform | What It Captures | How It Maps to Revenue |
|---|---|---|---|
| **1. Demand** | Meta Ads (Conversions API) | Website visits, form fills, sign-ups, purchases sent as hashed server-side events | Measures paid marketing ROI. `Lead → CompleteRegistration → Subscribe` funnel efficiency. |
| **2. CRM** | HubSpot | Contacts, Companies, Deals with stage history | Tracks the full B2B pipeline. Deal stages reflect each persona's exact lifecycle state. |
| **3. Billing** | Stripe | Customers, Subscriptions, Invoice history (3–12 months), One-time payments | Single source of truth for MRR, churn, and expansion revenue. |
| **4. Product** | PostHog | Sign-up, onboarding, feature usage, session depth, error events | Measures activation, engagement, and churn risk. PQL scoring happens here. |
| **5. Support** | Freshdesk | Tickets correlated to persona health. At-risk customers generate Urgent tickets. | Ticket volume and severity are leading churn indicators. |

### Cross-Layer Correlation Example

When `Acme Corp` runs:
- HubSpot creates a company record and a deal at `decisionmakerboughtin` stage
- Stripe has an active Pro subscription with 8 months of clean invoice history
- PostHog sends 14 days of `export_failed_error` events with high `load_time_ms`
- Freshdesk creates 3 Urgent tickets tagged `report_export`, `at_risk_customer`

All four signals point to the same truth: a high-value customer is about to churn because of
a product bug. A real CS team would catch this in their weekly at-risk customer review by
joining the Stripe MRR data with the PostHog error rate and the Freshdesk ticket volume.
That is exactly the analysis this simulation is built to support.

---

## 8. What "Real" Looks Like vs. This Simulation

| Aspect | Real Company | This Simulation |
|---|---|---|
| **Data source** | Live user actions | Scripted personas with deterministic + random signals |
| **Scale** | Thousands of customers | 5 fixed personas + 4–8 random companies per run |
| **HubSpot** | Sales reps manually log calls, set follow-up tasks | API writes contacts, companies, deals, and advances deal stages on a schedule |
| **Stripe** | Webhooks fire on real payment events | Invoice history is written directly as records; no real money moves |
| **PostHog** | JavaScript SDK embedded in the product | Python script sends batch events with realistic timestamps and properties |
| **Freshdesk** | Customers submit tickets through the portal | API creates tickets with persona-appropriate subject lines and priorities |
| **Meta Ads** | Pixel fires on page load; CAPI fires server-side | CAPI events sent for synthetic lead/signup/purchase conversions |
| **What is identical** | Data schema, API calls, cross-system IDs, business logic | Everything above |

The simulation is a skeleton. Every integration is real, every API call is real, every schema
field is production-valid. Adding real user traffic to this infrastructure requires connecting
the frontend HTML pages to the same backend writers — nothing else changes.
