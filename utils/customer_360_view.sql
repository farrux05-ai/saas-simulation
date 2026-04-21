-- ===============================================================================
-- SCALEFLOW - A-SERIES REVENUE ENGINE REPORTS
-- ===============================================================================
-- 
-- The "Blank Space in the Funnel" Query
-- This SQL view brings together HubSpot (CRM), Stripe (Revenue), PostHog (Product), 
-- Freshdesk (Support), and Call Transcripts (Sales Intel) to find the REAL reason
-- deals are lost or customers churn, rather than relying on generic CRM reasons.

CREATE OR REPLACE VIEW v_customer_360 AS
WITH 

-- 1. Get Support Ticket Volume by Company (Freshdesk Data)
support_health AS (
    -- In a real setup, we extract domains from emails to join to companies
    SELECT 
        substring(email from '@(.*)$') as domain,
        COUNT(id) as total_tickets,
        SUM(CASE WHEN description ILIKE '%export%' OR description ILIKE '%report%' THEN 1 ELSE 0 END) as export_issue_tickets,
        SUM(CASE WHEN priority >= 3 THEN 1 ELSE 0 END) as urgent_tickets
    FROM (
        -- Mocking the tickets table that would come from Airbyte/Fivetran
        SELECT 'user@acmecorp.com' as email, 'URGENT: Report generation timing out' as description, 3 as priority, 1 as id
        UNION ALL SELECT 'user2@acmecorp.com', 'We need custom exports', 3, 2
        UNION ALL SELECT 'dev@cloudnine.com', 'API issue', 2, 3
    ) tickets
    GROUP BY 1
),

-- 2. Get Sales Intel (Why did we really lose the deal?)
sales_intel AS (
    SELECT 
        prospect_company,
        MAX(objection_raised) as primary_objection,
        COUNT(CASE WHEN objection_raised ILIKE '%Jira%' THEN 1 END) as jira_objections,
        COUNT(CASE WHEN objection_raised ILIKE '%SOC 2%' THEN 1 END) as soc2_objections
    FROM call_transcripts
    GROUP BY 1
),

-- 3. Get Product Usage Patterns (PostHog Data)
product_health AS (
    SELECT 
        company_id,
        COUNT(id) as total_events,
        SUM(CASE WHEN event_name = 'export_failed_error' THEN 1 ELSE 0 END) as export_errors,
        MAX(created_at) as last_active_date
    FROM events
    GROUP BY 1
)

-- 4. Combine into a Holistic View
SELECT 
    c.id as company_id,
    c.name as company_name,
    c.status as current_status,
    c.plan_type as current_plan,
    c.mrr as mrr,
    
    -- Support & Product Correlation (The Churn Predictor)
    ph.total_events as past_30d_product_events,
    ph.export_errors as past_30d_export_errors,
    sh.total_tickets as past_30d_support_tickets,
    sh.export_issue_tickets as past_30d_export_tickets,
    
    -- Are they churning because of the 'Reports Export' feature?
    CASE 
        WHEN ph.export_errors > 0 AND sh.export_issue_tickets > 0 THEN 'HIGH RISK: Export Feature Struggle'
        WHEN c.status = 'Churned' AND sh.export_issue_tickets > 0 THEN 'POST-MORTEM: Churned due to Exports'
        ELSE 'Healthy'
    END as churn_risk_assessment,

    -- Sales Intel (The Win/Loss Predictor)
    si.primary_objection as latest_sales_objection,
    CASE
        WHEN si.jira_objections > 0 THEN 'PRODUCT ROADMAP: Needs Jira'
        WHEN si.soc2_objections > 0 THEN 'COMPLIANCE ROADMAP: Needs SOC 2'
        ELSE 'Generic'
    END as roadmap_priority

FROM companies c
LEFT JOIN support_health sh ON c.domain = sh.domain
LEFT JOIN product_health ph ON c.id = ph.company_id
LEFT JOIN sales_intel si ON c.name = si.prospect_company;

-- ===============================================================================
-- EXAMPLE ANALYSIS OUTPUT
-- ===============================================================================
-- Company Name: CloudNine Co
-- Status: Churned     | CRM Reason: "Price too high"
-- REAL REASON:
--   PostHog: 14 'export_failed_error' events in last week
--   Freshdesk: 3 High-Priority tickets about 'Reports Export'
--   Assessment: Churned due to broken Export feature, not price.
-- 
-- Company Name: TechStart Inc
-- Status: Trial (At-Risk)   | CRM Stage: Stalled
-- REAL REASON:
--   Gong/Call Transcripts: "We strictly need a 2-way Jira integration before buying."
--   Assessment: Product feature blocker. Pipeline holds $15k ACV hostage over Jira.
-- ===============================================================================
