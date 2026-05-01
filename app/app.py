"""
SentinelGuard AI — Real-Time Event Gateway (app.py)
====================================================
This is the LIVE WEBHOOK layer of the Revenue Engine.

Architecture:
  main_revops_writer.py   → Daily batch job  → writes historical/simulation data
  app/app.py        → Real-time events → writes triggered by actual user actions

Both use the SAME config.py and integrations/ layer.
Both produce data the analytics warehouse can join.

Endpoints
---------
  POST /api/signup               Landing page CTA → HubSpot lead + PostHog + Meta
  POST /api/onboarding-complete  Onboarding done  → HubSpot MQL + Deal + PostHog
  POST /api/support-ticket       Help button      → Freshdesk ticket + PostHog
  POST /api/upgrade-intent       Paywall click    → HubSpot deal stage + PostHog
  POST /api/track                Generic event    → PostHog only
  GET  /api/health               Integration status check

Run:
  cd /home/farrux/saas-simulation
  python3 app/app.py
"""

import os
import sys
import hashlib
import time
from datetime import datetime

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Path setup: import from project root ─────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import config                                        # noqa: E402
from utils.logger import get_logger                             # noqa: E402

logger = get_logger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('sentinelguard-landing.html')


# ══════════════════════════════════════════════════════════════════════════════
# Low-level helpers (keep HTTP calls out of route handlers)
# ══════════════════════════════════════════════════════════════════════════════

def _sha256(value: str) -> str:
    return hashlib.sha256(value.lower().strip().encode()).hexdigest() if value else ""


# ─── PostHog ──────────────────────────────────────────────────────────────────

def _ph_capture(distinct_id: str, event: str, props: dict) -> bool:
    if not config.posthog:
        return False
    try:
        payload = {
            "api_key":     config.posthog.api_key,
            "event":       event,
            "distinct_id": distinct_id,
            "properties":  props,
            "timestamp":   datetime.utcnow().isoformat(),
        }
        r = requests.post(
            f"{config.posthog.host}/capture/",
            json=payload, timeout=5
        )
        return r.status_code in (200, 204)
    except Exception as exc:
        logger.warning(f"[PostHog] capture failed: {exc}")
        return False


def _ph_identify(distinct_id: str, props: dict) -> bool:
    if not config.posthog:
        return False
    try:
        payload = {
            "api_key":     config.posthog.api_key,
            "event":       "$identify",
            "distinct_id": distinct_id,
            "properties":  {"$set": props},
            "timestamp":   datetime.utcnow().isoformat(),
        }
        r = requests.post(
            f"{config.posthog.host}/capture/",
            json=payload, timeout=5
        )
        return r.status_code in (200, 204)
    except Exception as exc:
        logger.warning(f"[PostHog] identify failed: {exc}")
        return False


# ─── HubSpot ──────────────────────────────────────────────────────────────────

def _hs_headers() -> dict:
    return {
        "Authorization": f"Bearer {config.hubspot.access_token}",
        "Content-Type":  "application/json",
    }


def _hs_post(endpoint: str, data: dict) -> dict:
    """POST to HubSpot CRM v3. Returns response dict. Handles 409 (already exists)."""
    r = requests.post(
        f"https://api.hubapi.com/{endpoint}",
        json=data, headers=_hs_headers(), timeout=8
    )
    if r.status_code == 409:
        # Object already exists — extract ID from error message
        import re
        m = re.search(r"Existing ID: (\d+)", r.text)
        return {"id": m.group(1), "_existed": True} if m else r.json()
    r.raise_for_status()
    return r.json()


def _hs_patch(object_type: str, object_id: str, props: dict) -> bool:
    r = requests.patch(
        f"https://api.hubapi.com/crm/v3/objects/{object_type}/{object_id}",
        json={"properties": props}, headers=_hs_headers(), timeout=8
    )
    return r.ok


def _hs_search_contact(email: str) -> str | None:
    """Return HubSpot contact ID for this email, or None."""
    r = requests.post(
        "https://api.hubapi.com/crm/v3/objects/contacts/search",
        json={
            "filterGroups": [{"filters": [
                {"propertyName": "email", "operator": "EQ", "value": email}
            ]}],
            "properties": ["email"],
            "limit": 1,
        },
        headers=_hs_headers(), timeout=8
    )
    results = r.json().get("results", [])
    return results[0]["id"] if results else None


def _hs_associate(from_type: str, from_id: str, to_type: str, to_id: str, assoc_type: str):
    requests.put(
        f"https://api.hubapi.com/crm/v3/objects/{from_type}/{from_id}"
        f"/associations/{to_type}/{to_id}/{assoc_type}",
        headers=_hs_headers(), timeout=8
    )


# ─── Freshdesk ────────────────────────────────────────────────────────────────

def _fd_create_ticket(ticket: dict) -> dict | None:
    """Create a ticket in Freshdesk. Returns ticket dict or None on failure."""
    if not config.freshdesk:
        return None
    try:
        domain = config.freshdesk.domain.replace("https://", "").replace("http://", "")
        r = requests.post(
            f"https://{domain}/api/v2/tickets",
            json=ticket,
            auth=(config.freshdesk.api_key, "X"),
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning(f"[Freshdesk] ticket failed: {exc}")
        return None


# ─── Meta CAPI ────────────────────────────────────────────────────────────────

def _meta_event(event_name: str, email: str, value: float = 0.0) -> bool:
    if not config.meta_ads:
        return False
    pixel_id = os.getenv("META_PIXEL_ID", "")
    test_code = os.getenv("META_TEST_EVENT_ID", "")
    if not pixel_id:
        return False
    try:
        event = {
            "event_name":   event_name,
            "event_time":   int(time.time()),
            "action_source": "website",
            "user_data":    {"em": _sha256(email)},
        }
        if value:
            event["custom_data"] = {"value": value, "currency": "USD"}
        payload = {"data": [event], "access_token": config.meta_ads.access_token}
        if test_code:
            payload["test_event_code"] = test_code
        r = requests.post(
            f"https://graph.facebook.com/v18.0/{pixel_id}/events",
            json=payload, timeout=6
        )
        return r.status_code == 200
    except Exception as exc:
        logger.warning(f"[Meta] event failed: {exc}")
        return False


# ─── Stripe ───────────────────────────────────────────────────────────────────

def _stripe_get_or_create_customer(email: str, name: str, company: str) -> str | None:
    """Return Stripe customer ID, creating one if needed."""
    if not config.stripe:
        return None
    import stripe as _stripe
    _stripe.api_key = config.stripe.secret_key
    try:
        existing = _stripe.Customer.search(query=f'email:"{email}"').data
        if existing:
            return existing[0].id
        customer = _stripe.Customer.create(
            email=email,
            name=name,
            metadata={"company": company, "source": "landing_page"},
        )
        return customer.id
    except Exception as exc:
        logger.warning(f"[Stripe] customer lookup/create failed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Route 1 — Signup  (Landing page → "Start Free Audit")
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/signup", methods=["POST"])
def signup():
    """
    User fills the landing-page form and hits Submit.

    Real-business wiring:
      HubSpot  → Contact (lifecycle: lead) + Company + association
      Stripe   → Customer record created (no subscription yet)
      PostHog  → $identify + "User Signed Up" event
      Meta     → "Lead" CAPI event

    Body: { name, email, company, source? }
    """
    body    = request.get_json(silent=True) or {}
    name    = body.get("name", "").strip()
    email   = body.get("email", "").strip().lower()
    company = body.get("company", "").strip()
    source  = body.get("source", "organic")

    if not email:
        return jsonify({"ok": False, "error": "email required"}), 400

    results, errors = {}, {}
    first = name.split()[0] if name else ""
    last  = name.split()[-1] if len(name.split()) > 1 else ""
    domain = email.split("@")[-1] if "@" in email else ""

    # 1. HubSpot — Contact ────────────────────────────────────────────────────
    contact_id = None
    if config.hubspot:
        try:
            contact = _hs_post("crm/v3/objects/contacts", {"properties": {
                "email":          email,
                "firstname":      first,
                "lastname":       last,
                "company":        company,
                "lifecyclestage": "lead",
            }})
            contact_id = contact.get("id")
            results["hubspot_contact_id"] = contact_id
            logger.info(f"[HubSpot] Contact: {contact_id} ({email})")
        except Exception as exc:
            errors["hubspot_contact"] = str(exc)
            logger.warning(f"[HubSpot] Contact failed: {exc}")

    # 2. HubSpot — Company + Association ──────────────────────────────────────
    if config.hubspot and company:
        try:
            co = _hs_post("crm/v3/objects/companies", {"properties": {
                "name":           company,
                "domain":         domain,
                "lifecyclestage": "lead",
            }})
            company_id = co.get("id")
            results["hubspot_company_id"] = company_id
            if contact_id and company_id:
                _hs_associate("contacts", contact_id, "companies", company_id, "279")
            logger.info(f"[HubSpot] Company: {company_id} ({company})")
        except Exception as exc:
            errors["hubspot_company"] = str(exc)
            logger.warning(f"[HubSpot] Company failed: {exc}")

    # 3. Stripe — Customer record (no subscription yet) ───────────────────────
    stripe_id = _stripe_get_or_create_customer(email, name, company)
    if stripe_id:
        results["stripe_customer_id"] = stripe_id
        logger.info(f"[Stripe] Customer: {stripe_id}")
    else:
        errors["stripe"] = "unavailable"

    # 4. PostHog — Identify + Signed Up ───────────────────────────────────────
    try:
        _ph_identify(email, {
            "name":        name,
            "email":       email,
            "company":     company,
            "plan":        "free",
            "signup_date": datetime.utcnow().isoformat(),
            "source":      source,
        })
        _ph_capture(email, "User Signed Up", {
            "email":         email,
            "company":       company,
            "signup_source": source,
            "plan":          "free",
        })
        results["posthog"] = "ok"
    except Exception as exc:
        errors["posthog"] = str(exc)

    # 5. Meta CAPI — Lead event ───────────────────────────────────────────────
    results["meta"] = "ok" if _meta_event("Lead", email) else "skipped"

    resp = {"ok": len(errors) == 0, "email": email, "results": results}
    if errors:
        resp["errors"] = errors
    return jsonify(resp), 200


# ══════════════════════════════════════════════════════════════════════════════
# Route 2 — Onboarding Complete  (Step 4 → "Launch Dashboard")
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/onboarding-complete", methods=["POST"])
def onboarding_complete():
    """
    User finishes the onboarding wizard and clicks "Launch Dashboard".

    Real-business wiring:
      HubSpot  → Contact upgraded to MQL + Deal created (stage: appointmentscheduled)
      PostHog  → "Onboarding Completed" + "Pricing Page Viewed"
      Meta     → "CompleteRegistration" ($500 estimated LTV)

    Body: { name, email, company, cloud, role, tool, source? }
    """
    body    = request.get_json(silent=True) or {}
    name    = body.get("name", "").strip()
    email   = body.get("email", "").strip().lower()
    company = body.get("company", "Acme Corp").strip()
    cloud   = body.get("cloud", "aws")
    role    = body.get("role", "engineer")
    tool    = body.get("tool", "none")
    source  = body.get("source", "organic")

    if not email:
        return jsonify({"ok": False, "error": "email required"}), 400

    results, errors = {}, {}

    # 1. HubSpot — Upgrade Contact to MQL ─────────────────────────────────────
    contact_id = None
    if config.hubspot:
        try:
            contact_id = _hs_search_contact(email)
            if contact_id:
                _hs_patch("contacts", contact_id, {
                    "lifecyclestage": "marketingqualifiedlead",
                })
                results["hubspot_contact_upgraded"] = contact_id
                logger.info(f"[HubSpot] Contact {contact_id} → MQL")
            else:
                results["hubspot_contact_upgraded"] = "not_found"
        except Exception as exc:
            errors["hubspot_contact_upgrade"] = str(exc)

    # 2. HubSpot — Create Deal ────────────────────────────────────────────────
    if config.hubspot:
        try:
            deal = _hs_post("crm/v3/objects/deals", {"properties": {
                "dealname":           f"{company} — Free Audit",
                "dealstage":          "appointmentscheduled",
                "pipeline":           "default",
                "amount":             "12000",
                "closedate":          datetime.utcnow().strftime("%Y-%m-%d"),
                "deal_currency_code": "USD",
                "dealtype":           "newbusiness",
                "hs_priority":        "medium",
            }})
            deal_id = deal.get("id")
            results["hubspot_deal_id"] = deal_id
            # Associate deal → contact
            if contact_id and deal_id:
                _hs_associate("deals", deal_id, "contacts", contact_id, "3")
            logger.info(f"[HubSpot] Deal {deal_id} created for {company}")
        except Exception as exc:
            errors["hubspot_deal"] = str(exc)

    # 3. PostHog — Onboarding events ──────────────────────────────────────────
    try:
        _ph_capture(email, "Onboarding Completed", {
            "cloud_provider":  cloud,
            "user_role":       role,
            "previous_tool":   tool,
            "signup_source":   source,
            "company":         company,
            "steps_completed": 4,
        })
        _ph_capture(email, "Pricing Page Viewed", {
            "plan_seen": "starter",
            "company":   company,
        })
        results["posthog"] = "ok"
    except Exception as exc:
        errors["posthog"] = str(exc)

    # 4. Meta CAPI ─────────────────────────────────────────────────────────────
    results["meta"] = "ok" if _meta_event("CompleteRegistration", email, 500.0) else "skipped"

    resp = {"ok": len(errors) == 0, "results": results}
    if errors:
        resp["errors"] = errors
    return jsonify(resp), 200


# ══════════════════════════════════════════════════════════════════════════════
# Route 3 — Support Ticket  (Dashboard "Help" / "Report a Bug" button)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/support-ticket", methods=["POST"])
def support_ticket():
    """
    User clicks "Get Support" or "Report Issue" inside the dashboard.

    Real-business wiring:
      Freshdesk → Ticket created (priority driven by plan)
      PostHog   → "Support Ticket Created" event (churn signal for analytics)
      HubSpot   → Note added to contact (optional, best-effort)

    Body: { email, name, company, plan, subject, description, category? }
    """
    body        = request.get_json(silent=True) or {}
    email       = body.get("email", "").strip().lower()
    name        = body.get("name", "User").strip()
    company     = body.get("company", "").strip()
    plan        = body.get("plan", "starter")
    subject     = body.get("subject", "Support request").strip()
    description = body.get("description", subject).strip()
    category    = body.get("category", "technical")

    if not email:
        return jsonify({"ok": False, "error": "email required"}), 400

    results, errors = {}, {}

    # Priority mapping: enterprise/pro get higher priority
    priority_map = {"free": 1, "starter": 2, "pro": 3, "enterprise": 4}
    priority = priority_map.get(plan, 2)

    # 1. Freshdesk — Create Ticket ─────────────────────────────────────────────
    ticket = _fd_create_ticket({
        "subject":     subject,
        "description": description,
        "email":       email,
        "name":        name,
        "priority":    priority,
        "status":      2,       # Open
        "source":      2,       # Portal
        "tags":        [category, plan, "from_dashboard"],
    })
    if ticket:
        results["freshdesk_ticket_id"] = ticket.get("id")
        logger.info(f"[Freshdesk] Ticket #{ticket.get('id')} for {email}")
    else:
        errors["freshdesk"] = "failed"

    # 2. PostHog — Support ticket event (leading churn indicator) ─────────────
    _ph_capture(email, "Support Ticket Created", {
        "category":          category,
        "priority":          priority,
        "plan":              plan,
        "company":           company,
        "ticket_id":         results.get("freshdesk_ticket_id"),
        "is_churn_signal":   priority >= 3,  # high/urgent = churn risk
    })
    results["posthog"] = "ok"

    # 3. HubSpot — Add note to contact (best-effort) ───────────────────────────
    if config.hubspot:
        try:
            contact_id = _hs_search_contact(email)
            if contact_id:
                _hs_post("crm/v3/objects/notes", {"properties": {
                    "hs_note_body":      f"[Support] {subject}",
                    "hs_timestamp":      str(int(datetime.utcnow().timestamp() * 1000)),
                }})
                results["hubspot_note"] = "ok"
        except Exception:
            pass  # note creation is best-effort

    resp = {"ok": len(errors) == 0, "results": results}
    if errors:
        resp["errors"] = errors
    return jsonify(resp), 200


# ══════════════════════════════════════════════════════════════════════════════
# Route 4 — Upgrade Intent  (Dashboard paywall "Upgrade" button)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/upgrade-intent", methods=["POST"])
def upgrade_intent():
    """
    User clicks "Upgrade to Pro" or "Unlock Auto-Remediation" on the dashboard.
    This is the PQL (Product Qualified Lead) signal — the highest-intent action.

    Real-business wiring:
      HubSpot  → Deal stage pushed to "qualifiedtobuy" (SQL signal for Sales)
      PostHog  → "Upgrade Prompt Clicked" event
      Meta     → "StartTrial" ($1000 value) — retargeting signal

    Body: { email, company, plan_clicked, feature_clicked? }
    """
    body     = request.get_json(silent=True) or {}
    email    = body.get("email", "").strip().lower()
    company  = body.get("company", "").strip()
    plan     = body.get("plan_clicked", "starter")
    feature  = body.get("feature_clicked", "paywall")

    if not email:
        return jsonify({"ok": False, "error": "email required"}), 400

    results, errors = {}, {}

    # 1. HubSpot — advance existing deal to qualifiedtobuy ────────────────────
    if config.hubspot:
        try:
            # Search for an open deal associated with this contact
            contact_id = _hs_search_contact(email)
            if contact_id:
                # Patch contact to SQL stage
                _hs_patch("contacts", contact_id, {
                    "lifecyclestage": "salesqualifiedlead",
                })
                results["hubspot_stage"] = "salesqualifiedlead"
                logger.info(f"[HubSpot] {email} → SQL (upgrade intent)")
        except Exception as exc:
            errors["hubspot"] = str(exc)

    # 2. PostHog — highest-intent event ───────────────────────────────────────
    _ph_capture(email, "Upgrade Prompt Clicked", {
        "plan_clicked":      plan,
        "feature_clicked":   feature,
        "company":           company,
        "pql_signal":        True,
    })
    results["posthog"] = "ok"

    # 3. Meta CAPI — StartTrial ($1,000) — for retargeting the close ──────────
    results["meta"] = "ok" if _meta_event("StartTrial", email, 1000.0) else "skipped"

    # 4. Stripe Checkout Session ───────────────────────────────────────────────
    if config.stripe and plan in ("starter", "pro"):
        try:
            import stripe as _stripe
            _stripe.api_key = config.stripe.secret_key
            customer_id = _stripe_get_or_create_customer(email, email.split("@")[0], company)
            
            price_amount = 500000 if plan == "pro" else 100000
            plan_name = 'SentinelGuard Pro - 5,000 Assets' if plan == "pro" else 'SentinelGuard Starter - 500 Assets'
            plan_desc = 'Advanced CSPM with Auto-Remediation and compliance.' if plan == "pro" else 'Basic CSPM scanning and alerts.'

            # Create a realistic checkout session for B2B SaaS
            session = _stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan_name,
                            'description': plan_desc,
                        },
                        'unit_amount': price_amount,
                        'recurring': {'interval': 'month'}
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.host_url + f'success.html?session_id={{CHECKOUT_SESSION_ID}}&plan={plan}',
                cancel_url=request.host_url + 'dashboard.html',
            )
            results["checkout_url"] = session.url
            logger.info(f"[Stripe] Checkout session created for {email} ({plan})")
        except Exception as exc:
            errors["stripe_checkout"] = str(exc)
            logger.error(f"[Stripe] Checkout failed: {exc}")

    resp = {"ok": len(errors) == 0, "results": results}
    if errors:
        resp["errors"] = errors
    return jsonify(resp), 200


# ══════════════════════════════════════════════════════════════════════════════
# Route 5 — Generic Track  (any dashboard JS event)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/track", methods=["POST"])
def track():
    """
    Lightweight PostHog event proxy called by dashboard JS.
    Avoids CORS issues with direct browser → PostHog calls on some networks.

    Body: { email, event, properties? }
    """
    body  = request.get_json(silent=True) or {}
    email = body.get("email", "anonymous")
    event = body.get("event", "Unknown Event")
    props = body.get("properties", {})

    ok = _ph_capture(email, event, props)
    return jsonify({"ok": ok}), 200


# ══════════════════════════════════════════════════════════════════════════════
# Route 6 — Health
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "integrations": {
            "hubspot":   bool(config.hubspot),
            "stripe":    bool(config.stripe),
            "posthog":   bool(config.posthog),
            "freshdesk": bool(config.freshdesk),
            "supabase":  bool(config.supabase),
            "meta_ads":  bool(config.meta_ads),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    svcs = [k for k, v in {
        "HubSpot":  config.hubspot,
        "Stripe":   config.stripe,
        "PostHog":  config.posthog,
        "Freshdesk":config.freshdesk,
        "Supabase": config.supabase,
        "Meta Ads": config.meta_ads,
    }.items() if v]

    print("\n" + "=" * 60)
    print("  SentinelGuard AI — Real-Time Event Gateway")
    print("=" * 60)
    for svc in svcs:
        print(f"  ✓ {svc}")
    print("=" * 60)
    print("  Endpoints:")
    print("    POST /api/signup")
    print("    POST /api/onboarding-complete")
    print("    POST /api/support-ticket      ← Freshdesk")
    print("    POST /api/upgrade-intent      ← HubSpot SQL + Meta")
    print("    POST /api/track               ← PostHog")
    print("    GET  /api/health")
    print("=" * 60)
    print("  http://localhost:5050")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5050, debug=True)
