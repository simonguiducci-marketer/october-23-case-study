"""
clean_fy26.py — League Growth Marketing case study, FY26 data cleaning.

Reads the raw extracts (never modified) and writes cleaned copies:
  01_leads_fy26_clean.csv      all 765 rows, original columns + cleaned columns + flags
  02_ad_spend_fy26_clean.csv   all 73 rows, original columns + include flag + reason
  cleaning_log_fy26.csv        one row per rule: issue ID, what was done, rows affected

Principle: flag, don't delete. Every row stays; the "clean" view is the set of rows
where include_clean == True. Issue IDs refer to League_Known_Data_Issues.xlsx (v1.1).

Usage:
  python clean_fy26.py <01_leads_fy26.csv> <02_ad_spend_fy26.csv> <output_dir>
"""
import sys
import pandas as pd

LEADS_IN, SPEND_IN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
EXTRACT_DATE = pd.Timestamp("2026-06-30")
FY_START = pd.Timestamp("2025-07-01")
DATES = ["created_date", "mql_date", "sql_date", "sqo_date", "closed_date"]

L = pd.read_csv(LEADS_IN, parse_dates=DATES)
S = pd.read_csv(SPEND_IN)
log = []

def note(issue, rule, rows, effect):
    log.append({"issue_id": issue, "rule": rule, "rows_affected": int(rows), "effect_on_clean_view": effect})

# ---------------------------------------------------------------- LEADS

# LD-02 / LD-18: channel from campaign_name. Each campaign maps to exactly one channel
# (Checks Passed: campaign to channel). Recovers blank/"Unknown" LinkedIn rows.
CAMPAIGN_TO_CHANNEL = {
    "FY26 GDG - Healthcare Platform (Broad)": "Google Demand Gen",
    "FY26 GDG - Benefits Administration": "Google Demand Gen",
    "FY26 LI - Benefits Leader ABM": "LinkedIn",
    "FY26 LI - Total Cost of Care Report": "LinkedIn",
    "FY26 LI - Retargeting": "LinkedIn",
    "FY26 Syndication - Buyers Guide (Guaranteed 200)": "Content Syndication",
    "FY26 Webinar - Navigating Care Costs": "Webinars",
    "FY26 Webinar - AI in Member Experience": "Webinars",
    "Q3 Executive Roundtable Series": "Events",
    "HLTH 2025 Activation": "Events",
    "National Benefits Leadership Summit": "Events",
    "FY26 ABM - Tier 1 Target Accounts": "Demandbase",
}
L["channel_clean"] = L["campaign_name"].map(CAMPAIGN_TO_CHANNEL)
assert L["channel_clean"].notna().all(), "unmapped campaign"
reported = L["channel_reported"].fillna("").str.strip().str.lower().str.rstrip("s")
clean_cmp = L["channel_clean"].str.lower().str.rstrip("s")
L["flag_channel_recovered"] = L["channel_reported"].isna() | (L["channel_reported"].str.strip() == "Unknown")
L["flag_channel_relabelled"] = ~L["flag_channel_recovered"] & (L["channel_reported"] != L["channel_clean"])
assert (reported[~L["flag_channel_recovered"]] == clean_cmp[~L["flag_channel_recovered"]]).all(), "channel conflict"
note("LD-02 / LD-18", "Channel taken from campaign_name instead of channel_reported",
     L["flag_channel_recovered"].sum(), "Blank/Unknown rows recovered to their channel (all LinkedIn)")
note("LD-02", "Spelling/case variants of channel_reported normalised via campaign_name",
     L["flag_channel_relabelled"].sum(), "No count change; labels unified")
L["flag_utm_missing"] = L["utm_source"].isna()
note("LD-03", "Missing UTMs flagged; not used for attribution", L["flag_utm_missing"].sum(), "None (campaign_name used instead)")

# LD-01 / LD-05: funnel stage derived from dates, not the hand-typed label.
L["is_won"] = L["acv_usd"].notna()
L["is_lost"] = L["closed_date"].notna() & ~L["is_won"]
L["flag_win_missing_sql_sqo"] = L["is_won"] & L["sql_date"].isna() & L["sqo_date"].isna()
L["reached_sql"] = L["sql_date"].notna() | L["sqo_date"].notna() | L["is_won"]
L["reached_sqo"] = L["sqo_date"].notna() | L["is_won"]
L["stage_clean"] = "MQL"
L.loc[L["reached_sql"], "stage_clean"] = "SQL"
L.loc[L["reached_sqo"], "stage_clean"] = "SQO"
L.loc[L["is_lost"], "stage_clean"] = "Closed Lost"
L.loc[L["is_won"], "stage_clean"] = "Closed Won"
LABEL_MAP = {"mql": "MQL", "sql": "SQL", "sales qualified": "SQL", "sqo": "SQO",
             "sales qualified opportunity": "SQO", "won": "Closed Won", "closed won": "Closed Won",
             "lost": "Closed Lost", "closed lost": "Closed Lost"}
L["stage_label_normalised"] = L["lifecycle_stage"].str.strip().str.lower().map(LABEL_MAP)
L["flag_stage_label_mismatch"] = L["stage_label_normalised"] != L["stage_clean"]
note("LD-01", "Stage derived from date fields; 10 label spellings mapped to 5 stages for comparison",
     (L["lifecycle_stage"] != L["stage_label_normalised"]).sum(),
     f"Labels disagreeing with dates after mapping: {L['flag_stage_label_mismatch'].sum()}")
note("LD-05", "Wins with no sql_date/sqo_date counted as reached SQL and SQO",
     L["flag_win_missing_sql_sqo"].sum(), "+3 SQL and +3 SQO versus counting dates only")

# LD-04: duplicates by contact_email. Keep the most advanced record; ties -> lowest lead_id.
rank = (L["reached_sql"].astype(int) + L["reached_sqo"].astype(int)
        + L["closed_date"].notna().astype(int) + L["is_won"].astype(int))
L["_rank"] = rank
L["_idnum"] = L["lead_id"].str.extract(r"(\d+)")[0].astype(int)
order = L.sort_values(["contact_email", "_rank", "_idnum"], ascending=[True, False, True])
keep_ids = set(order.drop_duplicates("contact_email", keep="first")["lead_id"])
L["flag_duplicate"] = ~L["lead_id"].isin(keep_ids)
dup_groups = L[L.duplicated("contact_email", keep=False)].groupby("contact_email")["campaign_name"].nunique()
L["flag_duplicate_cross_campaign"] = L["contact_email"].isin(dup_groups[dup_groups > 1].index)
note("LD-04", "Duplicates by contact_email: keep most advanced record, ties to lowest lead_id",
     L["flag_duplicate"].sum(),
     f"{L['flag_duplicate'].sum()} rows excluded; {L.loc[L['flag_duplicate'], 'reached_sql'].sum()} of them had reached SQL; "
     f"{dup_groups.gt(1).sum()} pairs span two campaigns (flagged)")

# LD-10 / LD-11: ICP by size and buyer segment. Flags only; shown as toggles, not removed.
L["is_icp_size"] = L["employee_band"].isin(["1,000-4,999", "5,000-19,999", "20,000+"])
L["segment_role"] = L["industry_segment"].map(lambda s: "Influencer" if s == "Broker / Consultant" else "Buyer")
note("LD-10", "is_icp_size = 1,000+ employees", (~L["is_icp_size"]).sum(), "None by default; available as a filter")
note("LD-11", "Government kept as Buyer; Broker / Consultant tagged Influencer",
     (L["segment_role"] == "Influencer").sum(), "None by default; available as a filter")

# Flag-only checks (no effect on counts)
L["flag_sql_before_mql"] = L["sql_date"].notna() & (L["sql_date"] < L["mql_date"])
note("LD-06", "SQL date before MQL date flagged", L["flag_sql_before_mql"].sum(), "None")
L["flag_mql_after_extract"] = L["mql_date"] > EXTRACT_DATE
note("LD-07", "MQL date after 30 Jun 2026 extract flagged", L["flag_mql_after_extract"].sum(), "None")
L["flag_created_pre_fy26"] = L["created_date"] < FY_START
note("LD-08", "Created before FY26 flagged (kept: they MQL'd in the extract)", L["flag_created_pre_fy26"].sum(), "None")
L["flag_sql_unassigned"] = L["reached_sql"] & (L["owner"] == "Unassigned")
note("LD-09", "SQL or later with no owner flagged", L["flag_sql_unassigned"].sum(), "None")
L["flag_abm_contradiction"] = (L["channel_clean"] == "Demandbase") & (L["abm_target_account"] == "No")
note("LD-13", "Demandbase leads not flagged Tier 1", L["flag_abm_contradiction"].sum(), "None")

# LD-15: cohort fields so conversion can be read on mature cohorts.
L["mql_half"] = L["mql_date"].map(lambda d: "H1 FY26" if d < pd.Timestamp("2026-01-01") else "H2 FY26")
L["mql_quarter"] = L["mql_date"].map(
    lambda d: "Q1 FY26" if d < pd.Timestamp("2025-10-01") else "Q2 FY26" if d < pd.Timestamp("2026-01-01")
    else "Q3 FY26" if d < pd.Timestamp("2026-04-01") else "Q4 FY26")
note("LD-15", "mql_half and mql_quarter added for cohort reading", 0, "None; enables mature-cohort view")

L["include_clean"] = ~L["flag_duplicate"]
L = L.drop(columns=["_rank", "_idnum"])
for c in DATES:
    L[c] = L[c].dt.strftime("%Y-%m-%d")

# ---------------------------------------------------------------- SPEND

S["half"] = S["month"].map(lambda m: "H1 FY26" if m < "2026-01" else "H2 FY26")
S["include_clean"] = True
S["exclusion_reason"] = ""
dup = S.duplicated(["month", "channel", "spend_usd"], keep="first")
S.loc[dup, ["include_clean", "exclusion_reason"]] = [False, "SP-01 duplicate row"]
note("SP-01", "Second Content Syndication 2025-11 row excluded", dup.sum(), "-$8,125 Syndication spend")
S["flag_spend_missing"] = S["spend_usd"].isna()
note("SP-02", "Blank Events 2026-03 spend kept blank, not filled", S["flag_spend_missing"].sum(),
     "Events spend understated; shown as a sensitivity range, not a single figure")
note("LD-19", "Period totals computed for baseline check", 0, "None; $280K treated as a fixed budget")

# ---------------------------------------------------------------- OUTPUT

L.to_csv(f"{OUT}/01_leads_fy26_clean.csv", index=False)
S.to_csv(f"{OUT}/02_ad_spend_fy26_clean.csv", index=False)
pd.DataFrame(log).to_csv(f"{OUT}/cleaning_log_fy26.csv", index=False)

C = L[L["include_clean"]]
print(f"Leads: {len(L)} rows, clean view {len(C)}")
print(f"Spend: {len(S)} rows, clean total ${S.loc[S['include_clean'], 'spend_usd'].sum():,.2f}")
print(pd.DataFrame(log).to_string(index=False))
