# Data Lifecycle & Correlation Logic

> **Uchun kim:** Analytics Engineer, RevOps muhandis, yoki bu loyiha bilan tanishmoqchi bo'lgan har qanday kishi.  
> **Maqsad:** "Nima qildik?" emas, **"Nima uchun shunday qildik va bu real hayotda qanday ishlaydi?"**

---

## 1. Muammo: Nima uchun oddiy random data yetarli emas?

Ko'pchilik data pipeline simulyatsiyalari shunday ishlaydi:

```
HubSpot → n ta tasodifiy kontakt, n ta tasodifiy deal
Stripe  → n ta tasodifiy mijoz, n ta tasodifiy obuna
PostHog → n ta tasodifiy hodisa
```

Natija? Warehouse'da hech narsa JOIN bo'lmaydi. "TechFlow Solutions" HubSpot'da bor, lekin Stripe'da yo'q. "Acme Corp" Stripe'da bor, lekin PostHog'da hech qachon tizimga kirmagan. Bu `Analytics Engineering` o'rganish uchun, yoki prezentatsiya uchun mutlaqo yaroqsiz.

**Bizning yondashuv:** Har kuni ishga tushadigan GitHub Actions script barcha 7 qatlam uchun *bir xil kompaniyalar* va *aniq ishbilarmonlik holatlari* bilan ishlaydi.

---

## 2. Arxitektura: `SimulationContext`

`utils/simulation_context.py` faylida `SimulationContext` klassi joylashgan. Har kunlik ishga tushirishda (`python main_revops_writer.py --all`) eng birinchi chaqiriladigan funksiya mana shu:

```python
# main_revops_writer.py → write_all()
self.context = build_simulation_context(num_random=4)
```

Keyin bu `context` ob'ekt barcha 7 ta integratsiyaga uzatiladi:

```
SimulationContext
├── fixed_personas   → 5 ta "hikoya" kompaniyasi (har kuni bir xil)
└── random_personas  → 4 ta tasodifiy yangi kompaniya (organik o'sish imitatsiyasi)
```

---

## 3. 5 ta Asosiy "Hikoya" Kompaniyasi (Fixed Personas)

Har bir persona real hayotdagi B2B SaaS lifecycle bosqichlaridan birini ifodalaydi.

### 🔴 Acme Corp — "Jim Kelayotgan Mijoz" (`at_risk` / `reports_export_blocker`)

**Real hayotdagi vaziyat:**  
Acme Corp 6 oy avval `Business` planiga o'tgan va $399/oy to'laydi. Oxirgi 14 kunda ularning moliya direktori har kuni "Reports Export" tugmasini bosganda — sahifa 10-15 sekund yuklanadi va bo'sh CSV fayl yuklab olinadi. Uchinchi marta IT'ga murojaat qildi. Bugun ertalab CEO'ga xabar yubordi: "Agar bu to'g'rilanmasa, keyingi oy obunani to'xtatamiz."

**Kodda bu qanday ko'rinadi:**

*PostHog (Layer 4):*
```python
# posthog_writer.py, scenario == SCENARIO_REPORTS_BLOCKER
events.append({
    'event': 'Feature Used',
    'properties': {
        'feature_action': 'export_failed_error',
        'load_time_ms':   random.randint(8000, 20000),  # 8-20 sekund
        'company':        'Acme Corp',
    }
})
# Bu 14 kun davomida har kuni takrorlanadi
```

*Freshdesk (Layer 5):*
```python
# freshdesk_writer.py, scenario == SCENARIO_REPORTS_BLOCKER
tickets = [
    ("URGENT: Report generation timing out after 10 seconds", priority=4),
    ("export_failed_error keeps appearing — 3rd time this week", priority=3),
    ("Cannot export custom date range to CSV — blank file", priority=3),
]
# Kontakt email: sarah@acmecorp.com (PostHog bilan bir xil!)
```

*HubSpot (Layer 2):*
```
deal_stage: closedwon (ular to'layapti)
lifecyclestage: customer
hs_priority: high (at_risk holatiga ko'ra)
```

**Analytics Engineerning aytadigan xulosasi:**  
> "Acme Corp HubSpot'da `closedwon` ko'rinsa ham, PostHog'da 14 kunlik `export_failed_error` signalini va Freshdesk'da 3 ta URGENT ticketni tushunmasak, churn uni server muammosi emas balki 'narx yuqori' sifatida yozilgan bo'lardi."

---

### 🟡 TechStart Inc — "Sales Qotib Qolgan" (`stalled` / `jira_integration_blocker`)

**Real hayotdagi vaziyat:**  
TechStart 35 kishilik DevOps startup. CTO Mike Williams 2 hafta avval demo ko'rdi, ixlos bildirdi. Lekin jamoasi butunlay Jira'da ishlaydi — vazifalar, sprintlar, PR tracking. 2-tomonlama Jira integratsiyasiz platformani qabul qilishadi degan so'z yo'q. Sales rep Sarah Kim "narxni tushirib bersak bo'ladimi?" deb o'ylaydi — lekin asl muammo bu emas.

**Kodda:**

*Call Transcripts (Layer 7):*
```python
# call_transcript_writer.py, scenario == SCENARIO_JIRA_BLOCKER
objection  = "we strictly need a 2-way Jira integration before buying"
outcome    = "stalled"
transcript = """
Sarah Kim: Following up from our demo, Mike. Any feedback from the team?
Mike Williams: The platform looks great, honestly. But we hit a wall — 
  we strictly need a 2-way Jira integration before buying.
Sarah Kim: Understood. Is this a hard blocker or something we can phase in?
Mike Williams: Hard blocker. Our devs live in Jira. Without 2-way sync 
  we can't adopt this.
"""
```

*PostHog (Layer 4):*
```python
# 10-30 kun oldin: integration sahifasida aylanib yurgan
events = [("integrations_connect", days_ago=10_to_30)]
# Oxirgi 10 kun: hech qanday session yo'q (disengaged)
```

*HubSpot (Layer 2):*
```
deal_stage:     presentationscheduled  (demo bo'ldi, orqaga ketdi)
hs_priority:    high
dealtype:       newbusiness
```

**Analytics Engineerning xulosasi:**  
> "HubSpot'da bu deal 'stalled' ko'rinadi, cause bosh qator yo'q. Call transcript'da esa aniq: '$0 da yo'qotilayotgan $17,880 ARR — sababchi Jira integratsiyasining yo'qligi.' Product roadmap'ga kirishi kerak."

---

### 🟢 DataFlow LLC — "Yaxshi yo'l, Kengayish" (`active` / `happy_path`)

**Real hayotdagi vaziyat:**  
DataFlow 60 kishilik SaaS kompaniya, 8 oy avval Professional planga o'tgan. Har hafta Platform'dan hisob-kitob chiqarib, CEO'ga yuboradi. Moliya direktori 10 minut tejayapti, deydi. Endi 5 ta yangi kishi qo'shmoqchi va Business planga o'tmoqchi.

**Kodda:**

*PostHog (Layer 4):*
```python
# So'nggi 30 kun davomida har kuni:
events = [
    ("Session Started", ...),
    ("reports_export", load_time_ms=200-800),  # tez, muvaffaqiyatli
]
# Har 3 kunda: Report Generated
events.append({"event": "Report Generated", "report_type": "revenue"})
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
# Faqat 1 ta past prioritetli savol: "hebdomadal report qanday yuboriladi?"
priority = 1   # Low
status   = 5   # Closed
tags     = ["feature_question", "happy_customer"]
```

---

### ⚫ CloudNine Co — "Yo'qolgan Deal" (`churned` / `budget_cut`)

**Real hayotdagi vaziyat:**  
CloudNine bilan 2 oy yaxshi muloqot bo'ldi. Shartnoma muzokaraga kirdi. Keyin Q3 boshida moliya bo'limi "hamma yangi xarajatlarni to'xtatdi". Sales rep ularni yo'qotdi va HubSpot'da "Closed Lost — Price Too High" deb yozdi. Aslida narx emas, Q3 byudjet muzlatishi bo'ldi.

**Kodda:**

*Call Transcripts (Layer 7):*
```python
objection = "not the right time — Q3 budget is locked"
outcome   = "closed_lost"
next_step = "No action — closed lost"
```

*PostHog (Layer 4):*
```python
# Oxirgi event: 50 kun oldin, bitta session
# Undan keyin hech narsa → "ghost account"
old_date = datetime.now() - timedelta(days=50)
events = [("Session Started", timestamp=old_date)]
# continue → boshqa event yo'q
```

*Freshdesk (Layer 5):*
```
# Hech qanday ticket generatsiya qilinmaydi
# stalled / churned / new_lead → no tickets
```

---

### 🔵 DevOps Pro — "Yangi Lead, Bugun Kirgan" (`new_lead` / `new_onboard`)

**Real hayotdagi vaziyat:**  
James Garcia — 15 kishilik startapning Founder'i. LinkedIn'da reklama ko'rdi, saytga kirdi, demo so'radi. Bugun birinchi discovery call bo'ldi. Hali hech narsa to'lamagan, hali trial ham boshmagan.

**Kodda:**

*Meta Ads (Layer 1):*
```python
# TODAY: Lead + CompleteRegistration event
event_name = "Lead"       → value $100
event_name = "CompleteRegistration" → value $500
```

*PostHog (Layer 4):*
```python
# Faqat bugun, 3 ta event:
events = [
    "User Signed Up"       → signup_source: "paid_ad"
    "Onboarding Started"   → (bugun)
    "Pricing Page Viewed"  → plan_seen: "professional"
]
# Boshqa hech narsa yo'q — birinchi kun
```

*HubSpot (Layer 2):*
```
deal_stage:   appointmentscheduled
dealtype:     newbusiness
lifecyclestage: lead
```

*Call Transcripts (Layer 7):*
```python
call_type = "discovery"
outcome   = "moved_to_demo"
next_step = "Schedule full demo with broader team"
```

---

## 4. Har kunlik ishga tushish oqimi

```
00:00 UTC — GitHub Actions
    │
    ▼
build_simulation_context(num_random=4)
    │
    ├── 5 fixed_personas (BIR XIL har kuni)
    └── 4 random_personas (YANGI har kuni → organik o'sish)
    │
    ▼ barcha 7 qatlamga uzatiladi
    │
Layer 1: Meta Ads      → DevOps Pro lead eventi
Layer 2: HubSpot       → Barcha 9 kompaniya, har xil deal stages
Layer 3: Stripe        → DataFlow upgrade, Acme active, boshqalar yo'q
Layer 4: PostHog       → Acme: export errors | DataFlow: healthy | CloudNine: ghost
Layer 5: Freshdesk     → Acme: 3 URGENT tickets | DataFlow: 1 low prio
Layer 6: Supabase      → Barcha persona va random kompaniyalar
Layer 7: Transcripts   → TechStart: Jira stall | CloudNine: Q3 lost | DataFlow: won
```

---

## 5. Nima uchun bu tuzilma real hayotga mos?

| Real hayot | Bizning simulyatsiya |
|-----------|----------------------|
| CRM'dagi "Lost — Price" ko'pincha noto'g'ri | Call transcript aniq objection'ni tutadi |
| At-risk mijozlar support'da shovqin ko'taradi | Acme: 3 URGENT ticket + 14 kun export xatosi |
| Churn ko'pincha bug'dan, narxdan emas | PostHog + Freshdesk correlation |
| Muvaffaqiyatli mijozlar upsell uchun ochiq | DataFlow: closing call bilan kengayish |
| Yangi leadlar bitta kunda hamma joyda paydo bo'ladi | DevOps Pro: Meta + HubSpot + PostHog |

---

## 6. Warehouse'ga olib borganda

Endi siz bu simulyatsiyadan kelgan data'ni BigQuery yoki Snowflake'ga Meltano yoki Airbyte bilan joylashtirsangiz, dbt'da quyidagi JOIN'lar ishlaydi:

```sql
-- Misol: At-Risq Kompaniyalarni Aniqlash
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

Bu query'ni ishlatishingiz mumkinligi uchun `company_domain` va `company_name` barcha keylarda bir xil ekanligi muhim — buni `SimulationContext` kafolatlaydi.

---

> **Xulosa:** Bu loyiha "random data generator" emas. Bu — *aniq biznes muammolarni modellash qiluvchi, cross-layer korrelyatsiyani kafolatlaydigan, har kuni organik o'sib boruvchi* A-series Revenue Engine simulyatsiyasidir.
