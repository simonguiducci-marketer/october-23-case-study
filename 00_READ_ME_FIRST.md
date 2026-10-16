# League. Growth Marketing Data Package

**FY26 reporting period: 1 Jul 2025 to 30 Jun 2026. Extracted 30 Jun 2026.**

> **All data here is synthetic.** Companies, contacts, campaigns, spend and outcomes were
> fabricated for this exercise. Nothing is League customer, member or production data.
> Treat it as you would a real CRM extract anyway. That is part of the test.

---

## Your task

Two things, built in your own time before the session. About two hours of work.

1. **Build a funnel view.** MQL to SQL to SQO to Closed Won across the six channels, and
   whatever else you think matters. Build an interactive artifact, dashboard, worked
   spreadsheet, etc.
2. **Allocate H1 FY27 paid media.** Constraints and targets are at the bottom of this file.
   Show the channel-level math and say whether the targets are achievable.

Expect us to ask how you built it, not just what you concluded.

---

## Files

| File | What it is |
|---|---|
| `01_leads_fy26.csv` | Lead-level extract, one row per lead. 765 rows. |
| `02_ad_spend_fy26.csv` | Monthly paid media spend by channel. |
| `03_gtm_data_package.xlsx` | The same two tables as tabs. |

---

## Context

League sells an AI-powered healthcare platform to enterprise buyers of 1,000+ employees:
large employers, health plans, provider systems. Direct enterprise sales, long cycles,
multiple decision-makers. Stack is Salesforce, Pardot, GA, SEMrush and Demandbase.

You are the incoming Director, Demand Generation. The question on the table: how should
we spend?

---

## The six channels

For this exercise, assume all Paid Marketing runs through these six. Organic, referral and
partner pipeline exists but sits outside this budget and is out of scope.

| Channel | What it is |
|---|---|
| **Google Demand Gen** | Google's audience-based campaigns. Broad reach, cheap clicks. |
| **LinkedIn** | Paid social. ABM audiences, gated report promotion, retargeting. |
| **Content Syndication** | Third-party vendor delivering gated-content leads on a guaranteed-volume contract. |
| **Webinars** | Own-brand webinar programme, promoted by email and paid social. |
| **Events** | Field events, conference activations, executive roundtables. |
| **Demandbase** | ABM display against the Tier 1 account list (1,200 accounts). |

---

## Funnel definitions

| Stage | Definition in this data |
|---|---|
| **MQL** | Hit the Pardot scoring threshold. `mql_date` populated. |
| **SQL** | An AE accepted the lead and logged a discovery call. `sql_date` populated. |
| **SQO** | Qualified opportunity with budget and timeline. `sqo_date` populated. |
| **Closed Won / Lost** | `closed_date` and `close_reason` populated. `acv_usd` on wins. |

Stage labels were entered by hand over three quarters by three different people.

---

## Field notes

**`01_leads_fy26.csv`**

| Field | Note |
|---|---|
| `lead_id` | Salesforce lead ID. Unique per row. |
| `created_date` / `mql_date` | Form fill date, and date the scoring threshold was crossed. |
| `sql_date` / `sqo_date` / `closed_date` | Blank where the lead never reached that stage. |
| `lifecycle_stage` | Current stage, free text. |
| `acv_usd` | Annual contract value, wins only. |
| `employee_band` | Self-reported on the form. League's ICP is 1,000+. |
| `industry_segment` | Self-reported. |
| `channel_reported` | Channel as recorded at the time. |
| `campaign_name` | Campaign the lead was assigned to. |
| `utm_source` / `utm_medium` / `utm_campaign` | As captured on the landing page. |
| `abm_target_account` | Whether the account sits on the Demandbase Tier 1 list. |
| `owner` | Assigned AE. |

**`02_ad_spend_fy26.csv`**

Media spend only. No headcount, agency retainers or tooling. `impressions` and `clicks`
are populated for Google Demand Gen and LinkedIn only. The `notes` column holds whatever
the contractors wrote down at the time.

---

## What you would know on day one

Everything else you have to find in the data.

- **Webinars are capacity-capped.** Marketing can run at most 3 per month at roughly
  $3,000 each in promotion, so about $54,000 per half.
- **Demandbase is bounded by the account list.** 1,200 Tier 1 accounts. Past about $40,000
  per half you are buying frequency, not reach.
- **HLTH 2026 is contracted.** $45,000 is committed for H1 FY27 and cannot move.
- **The content syndication contract renews in August.** Current terms are a guaranteed 200
  leads per year at a fixed fee. Renewal is your call.
- **The LinkedIn landing page template was migrated on 9 Feb 2026** during a website refresh.

---

## H1 FY27 planning constraints (Jul to Dec 2026)

| | |
|---|---|
| **Paid media budget** | **$280,000** (flat on H2 FY26) |
| **MQL target** | **300** |
| **SQL target** | **55** |
| **Committed spend** | $45,000, HLTH 2026 |

Leadership set both targets and intends to measure marketing on both. If you think they are
incompatible, say so and show the trade-off.
