# 📚 Revenue Engine Simulator Documentation

Welcome to the documentation for the A-Series Revenue Engine Simulator. 

This folder contains detailed technical explanations of the simulator's business logic, cross-platform interactions, and entity lifecycles.

## 🗂️ Available Guides

- [**Data Lifecycle & Correlation Logic** (`data_lifecycle.md`)](./data_lifecycle.md)  
  *Start here.* This document deeply explains the "why" and "how" behind the data. It breaks down the 5 fixed buyer personas (The Silent At-Risk Customer, The Stalled Deal, The Brand New Inbound Lead, etc.) and shows exactly how an action in one platform triggers corresponding actions in the rest of the stack.

## 🔗 How the Data Layers Connect

If you're wondering how the data from Ads, CRM, Product, and Payments flow together, here is the basic workflow we simulate across the platforms:

1. **How do we get new prospects? (Ads)**
   * **Meta Ads (Layer 1)** fires `CompleteRegistration` and `Lead` events.
2. **How does Product data connect? (Product Analytics)**
   * **PostHog (Layer 4)** captures the new user dropping in from the ad. It tracks `User Signed Up` (Source: Paid Ad), onboarding flows, and everyday feature usage (or errors).
3. **How does the CRM work here? (Sales Funnel)**
   * **HubSpot (Layer 2)** intercepts the new signups and creates a Contact and a Deal. The Deal moves through stages (`appointmentscheduled` → `presentationscheduled` → `closedwon`/`closedlost`).
4. **How are payments connected to the data? (Billing)**
   * **Stripe (Layer 3)** monitors HubSpot. When a deal becomes `closedwon`, Stripe generates the Customer identity, Subscriptions, and a 12-month invoice history.
5. **How does underlying tech support them? (Database)**
   * **Supabase (Layer 6)** acts as the core application database, storing the unified `companies` and `users` tables, linking domains so you can join HubSpot Deals with Stripe Revenue and PostHog Activity.
   * **Supabase (Layer 7)** also holds AI-generated call transcripts, explaining *why* a HubSpot Deal was won or lost.

Everything is perfectly correlated using exact email addresses and company domains using a core engine called `SimulationContext`.

Read the `data_lifecycle.md` file for full code examples!
