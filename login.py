from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from demo_backend import build_om_zone_candidates, build_zone_recommendation_stats, dashboard_campaigns, load_demo_data


st.set_page_config(
    page_title="OneMedia3 - Panasillies",
    page_icon="OM3",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _records(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> list[dict]:
    if df.empty:
        return []
    safe = df[[column for column in columns if column in df.columns]].copy()
    safe = safe.replace({pd.NA: None}).where(pd.notna(safe), None)
    if limit is not None:
        safe = safe.head(limit)
    return safe.to_dict(orient="records")


def payload() -> dict:
    data = load_demo_data()
    campaigns = dashboard_campaigns(data)
    alerts = data["alerts"].copy()
    forecasts = data["forecasts"].sort_values("daily_capacity", ascending=False).copy()
    priority = data["priority"].copy()
    feasibility = data["feasibility"].copy()
    allocations = data["allocations"].sort_values("allocated_impressions", ascending=False).copy()
    utilization = data["zone_utilization"].sort_values("utilization_pct", ascending=False).copy()
    campaigns_raw = data["campaigns"].copy()
    fleet_metrics = pd.read_csv(data["data_dir"] / "fleet_metrics.csv").iloc[0].to_dict()

    return {
        "today": date.today().isoformat(),
        "defaultStart": (date.today() + timedelta(days=7)).isoformat(),
        "defaultEnd": (date.today() + timedelta(days=45)).isoformat(),
        "source": {
            "campaigns_cleaned.csv": int(len(campaigns_raw)),
            "output_pacing.csv": int(len(data["pacing"])),
            "output_alerts.csv": int(len(alerts)),
            "output_allocations.csv": int(len(allocations)),
            "output_zone_forecasts.csv": int(len(forecasts)),
            "output_feasibility.csv": int(len(feasibility)),
            "output_priority_scores.csv": int(len(priority)),
            "output_zone_utilization.csv": int(len(utilization)),
        },
        "omRecommendationSource": "precomputed Model 1 output_zone_forecasts.csv + pipeline_OM.py Phase 3 zone scoring",
        "omZoneCandidates": build_om_zone_candidates(),
        "zoneStats": build_zone_recommendation_stats(forecasts, utilization, allocations),
        "fleetMetrics": fleet_metrics,
        "campaigns": _records(
            campaigns,
            [
                "campaign_id",
                "campaign_name",
                "revenue_type",
                "planned",
                "delivered",
                "delivery_pct",
                "pacing_ratio",
                "status",
                "needed_daily",
                "available_daily",
                "feasibility",
                "remaining_days",
                "predicted_final_delivery_pct",
                "severity",
            ],
        ),
        "alerts": _records(
            alerts,
            [
                "campaign_id",
                "campaign_name",
                "severity",
                "pi",
                "pacing_ratio",
                "predicted_delivery_pct",
                "root_cause",
            ],
        ),
        "forecasts": _records(
            forecasts,
            [
                "zone_name",
                "daily_capacity",
                "predicted_imp_per_flight",
                "active_campaigns_in_zone",
                "total_planned_daily_demand",
                "paid_ratio",
            ],
        ),
        "priority": _records(
            priority,
            [
                "campaign_id",
                "campaign_name",
                "priority_score",
                "queue_position",
                "goal_type",
                "revenue_type",
                "zone_fit",
                "pacing_gap",
                "time_urgency",
                "planned_daily_impressions",
            ],
        ),
        "feasibility": _records(
            feasibility,
            [
                "campaign_id",
                "campaign_name",
                "planned_daily",
                "allocated_daily",
                "fulfillment_pct",
                "confidence",
            ],
        ),
        "allocations": _records(
            allocations,
            [
                "campaign_id",
                "zone_name",
                "allocated_impressions",
                "zone_zpr",
                "zone_capacity",
                "total_allocated",
                "allocation_weight",
            ],
        ),
        "utilization": _records(
            utilization,
            ["zone_name", "total_allocated", "capacity", "utilization_pct", "zpr"],
        ),
    }


HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: #f4f6f9;
  font-family: Arial, Helvetica, sans-serif;
  color: #202938;
}
button, input, select { font-family: Arial, Helvetica, sans-serif; }
.app {
  width: 100%;
  min-width: 960px;
  min-height: 860px;
  height: 100vh;
  position: relative;
  overflow: hidden;
  border: 2px solid #b8c6da;
  background: #eef2f6;
}
.login-app {
  width: 100%;
  min-width: 960px;
  height: 100vh;
  min-height: 760px;
  position: relative;
  overflow: hidden;
  background: #34679f;
}
.login-title {
  position: absolute;
  top: 54px;
  left: 0;
  right: 0;
  text-align: center;
  color: white;
  font-size: 48px;
  font-weight: 800;
}
.login-card {
  position: absolute;
  top: 142px;
  left: 50%;
  transform: translateX(-50%);
  width: 560px;
  height: 356px;
  background: white;
  border: 2px solid #d9dde4;
  border-radius: 12px;
  padding: 40px 74px;
  text-align: center;
}
.login-card .service {
  font-size: 22px;
  margin-bottom: 52px;
}
.login-card input[type="text"],
.login-card input[type="password"] {
  width: 420px;
  height: 50px;
  margin-bottom: 20px;
  border: 2px solid #b8bec6;
  background: #d9dde3;
  color: #222;
  text-align: center;
  font-size: 16px;
  font-weight: 700;
}
.login-card .primary {
  width: 420px;
  height: 50px;
  margin-bottom: 20px;
  font-size: 16px;
}
.primary {
  border: 1px solid #1d5791;
  background: #2b6eac;
  color: white;
  font-weight: 700;
  cursor: pointer;
}
.primary:hover {
  background: #245f99;
}
.remember {
  font-size: 16px;
  font-weight: 700;
}
.remember input {
  width: 20px;
  height: 20px;
  margin-left: 10px;
  vertical-align: middle;
  appearance: none;
  border: 1px solid #d1d5db;
  background: #d9d9d9;
  cursor: pointer;
}
.remember input:checked {
  background: #2b6eac;
  box-shadow: inset 0 0 0 4px #d9dde3;
}
.tiny-links {
  margin-top: 28px;
  font-size: 16px;
  font-weight: 700;
  line-height: 24px;
}
.copyright {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 34px;
  text-align: center;
  color: white;
  font-size: 16px;
  font-weight: 700;
}
.login-error {
  position: absolute;
  top: 512px;
  left: 50%;
  transform: translateX(-50%);
  width: 560px;
  color: #fff;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
}
.brand {
  position: absolute;
  left: 0;
  top: 0;
  width: 162px;
  height: 36px;
  background: #1670d6;
  color: white;
  font-size: 11px;
  line-height: 12px;
  font-weight: 700;
  padding: 9px 14px;
  white-space: nowrap;
}
.topbar {
  position: absolute;
  left: 162px;
  top: 0;
  right: 0;
  height: 36px;
  background: #111a2d;
  border-bottom: 3px solid #2f5f99;
  color: #eef4ff;
}
.toplink {
  position: absolute;
  top: 12px;
  width: 90px;
  text-align: center;
  font-size: 11px;
  color: #e7edf8;
  cursor: pointer;
}
.toplink.active {
  color: #ffffff;
  font-weight: 800;
  text-decoration: underline;
  text-underline-offset: 8px;
}
.toplink:nth-child(1) { left: 80px; }
.toplink:nth-child(2) { left: 170px; }
.toplink:nth-child(3) { left: 260px; }
.toplink:nth-child(4) { left: 350px; }
.toplink:nth-child(5) { left: 440px; }
.toplink:nth-child(6) { left: 530px; }
.toplink:nth-child(7) { left: 620px; }
.user {
  position: absolute;
  right: 112px;
  top: 13px;
  font-size: 8px;
  color: #d7deec;
}
.logout {
  position: absolute;
  right: 34px;
  top: 13px;
  width: 64px;
  text-align: center;
  color: #eef4ff;
  font-size: 8px;
  font-weight: 700;
  cursor: pointer;
  z-index: 5;
}
.side {
  position: absolute;
  left: 0;
  top: 36px;
  bottom: 0;
  width: 162px;
  background: #1d222c;
}
.nav {
  display: block;
  width: 162px;
  height: 38px;
  border: 0;
  background: transparent;
  color: #f4f7fb;
  text-align: left;
  padding-left: 14px;
  font-size: 9px;
  cursor: pointer;
}
.nav.active {
  background: #2d3443;
  font-weight: 700;
}
.nav:hover { background: #313949; }
.main {
  position: absolute;
  left: 162px;
  top: 36px;
  right: 0;
  bottom: 0;
  padding: 20px;
  background: #eef2f6;
  overflow: auto;
}
.crumb {
  font-size: 10px;
  color: #6e7c91;
  margin-bottom: 10px;
}
h1 {
  margin: 0 0 20px 0;
  font-size: 20px;
  line-height: 24px;
  color: #222b3a;
}
.panel {
  border: 1px solid #bcc9dc;
  background: white;
}
.panel-head {
  height: 28px;
  background: #f7f8fa;
  border-bottom: 1px solid #bcc9dc;
  padding: 8px 10px;
  font-size: 11px;
  font-weight: 700;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}
.kpi { height: 90px; }
.kpi .num {
  margin: 7px 17px 2px;
  font-size: 28px;
  font-weight: 800;
  color: #16264b;
}
.kpi .label {
  margin-left: 17px;
  color: #697487;
  font-size: 11px;
}
.grid-two {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(240px, 1fr);
  gap: 22px;
}
.grid-even {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9px;
}
.table th {
  height: 28px;
  background: #f7f8fa;
  color: #233047;
  text-align: left;
  padding: 0 8px;
  border-bottom: 1px solid #cbd5e4;
}
.table td {
  height: 30px;
  padding: 0 8px;
  border-bottom: 1px solid #dde5ef;
  background: white;
}
.table tr:nth-child(even) td { background: #fbfcfd; }
.module {
  height: 22px;
  margin: 6px 20px;
  border: 1px solid #bcc9dc;
  background: #fbfcfe;
  padding: 6px 10px;
  font-size: 8px;
  font-weight: 700;
  cursor: pointer;
}
.form-panel {
  width: min(948px, 100%);
  min-height: 220px;
}
.form-body {
  padding: 16px 20px;
  display: grid;
  grid-template-columns: repeat(2, minmax(240px, 320px));
  column-gap: 40px;
  row-gap: 10px;
}
.field label {
  display: block;
  font-size: 11px;
  margin-bottom: 5px;
  color: #263246;
}
.field input, .field select {
  width: 320px;
  height: 25px;
  border: 1px solid #b9c4d3;
  background: white;
  padding: 4px 8px;
  font-size: 10px;
}
.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.chip {
  border: 1px solid #b9c4d3;
  background: #f7f9fc;
  padding: 6px 9px;
  font-size: 10px;
}
.chip input {
  width: auto;
  height: auto;
  margin-right: 5px;
}
.action-row { padding: 0 20px 18px; }
.notice {
  margin: 16px 0;
  width: min(948px, 100%);
  border: 1px solid #b9c4d3;
  background: #f9fbff;
  padding: 10px 12px;
  font-size: 11px;
}
.error {
  margin: 12px 20px;
  color: #b42318;
  font-size: 11px;
  font-weight: 700;
}
.status {
  display: inline-block;
  min-width: 56px;
  text-align: center;
  border: 1px solid #b9c4d3;
  padding: 3px 6px;
  font-size: 9px;
  font-weight: 700;
}
.critical, .at-risk { color: #b42318; }
.warning, .watch, .delayed { color: #b7791f; }
.ok, .on-track, .completed, .ready, .staged, .tracked { color: #16703a; }
.waiting { color: #657184; }
.ops-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}
.ops-card {
  border: 1px solid #bcc9dc;
  background: white;
  min-height: 126px;
}
.ops-card .body {
  padding: 10px 12px;
  font-size: 10px;
  line-height: 17px;
}
.pill {
  display: inline-block;
  border: 1px solid #b9c4d3;
  background: #f7f9fc;
  padding: 3px 7px;
  font-size: 9px;
  font-weight: 700;
  margin-right: 5px;
}
.filter-row {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid #c8d2e1;
  background: #fbfcfe;
}
.filter-btn {
  min-width: 72px;
  border: 1px solid #b9c4d3;
  background: #ffffff;
  padding: 5px 9px;
  font-size: 9px;
  font-weight: 700;
  cursor: pointer;
}
.filter-btn.active {
  background: #2b6eac;
  color: #ffffff;
  border-color: #1d5791;
}
.scroll-panel {
  max-height: 340px;
  overflow: auto;
}
.source-line {
  margin-top: 10px;
  color: #657184;
  font-size: 9px;
}
.progress {
  width: 100%;
  height: 10px;
  border: 1px solid #bdc8d8;
  background: #edf1f6;
}
.progress span {
  display: block;
  height: 100%;
  background: #2b6eac;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.rec-card {
  border: 1px solid #bcc9dc;
  background: white;
  min-height: 116px;
}
.rec-card .title {
  background: #f7f8fa;
  border-bottom: 1px solid #bcc9dc;
  padding: 8px 10px;
  font-size: 11px;
  font-weight: 700;
}
.rec-card .body {
  padding: 9px 10px;
  font-size: 10px;
  line-height: 16px;
}
.rec-card.selected {
  border-color: #1d5791;
  box-shadow: inset 0 0 0 2px #2b6eac;
}
.decision-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  margin: 12px 0;
}
.zone-pick {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #b9c4d3;
  background: #ffffff;
  padding: 6px 9px;
  font-size: 10px;
}
.zone-pick input {
  width: auto;
  height: auto;
}
.bar-chart {
  height: 96px;
  padding: 10px;
  display: flex;
  align-items: flex-end;
  gap: 9px;
}
.bar {
  width: 34px;
  background: #2b6eac;
  border: 1px solid #1d5791;
}
.pie {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  border: 1px solid #bcc9dc;
  margin: 18px auto;
}
.legend {
  padding: 0 16px 10px;
  display: grid;
  gap: 5px;
}
.legend-item {
  display: grid;
  grid-template-columns: 12px 1fr auto;
  align-items: center;
  gap: 7px;
  font-size: 10px;
}
.swatch {
  width: 10px;
  height: 10px;
  border: 1px solid #9ba9bd;
}
.stepper {
  position: relative;
  width: min(860px, 72vw);
  height: 72px;
  margin: -5px auto 12px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  align-items: start;
}
.step-line {
  position: absolute;
  left: 12.5%;
  right: 12.5%;
  top: 20px;
  height: 2px;
  background: #5e6878;
}
.step-item {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  gap: 7px;
}
.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #bfc5cf;
  color: white;
  text-align: center;
  line-height: 28px;
  font-size: 9px;
  font-weight: 700;
}
.step-dot.active {
  background: #1f75bd;
  border: 3px solid #e43b2f;
  line-height: 22px;
}
.step-label {
  width: 120px;
  text-align: center;
  color: #697487;
  font-size: 8px;
}
.goal-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  padding: 12px 20px 8px;
}
.goal {
  height: 38px;
  border: 0;
  color: white;
  background: #6e9c64;
  font-size: 8px;
  font-weight: 700;
}
.goal.active {
  background: #245321;
}
.clickable-row {
  cursor: pointer;
}
.clickable-row:hover td {
  background: #eef4fb;
}
.detail-box {
  margin-top: 10px;
  border: 1px solid #bcc9dc;
  background: #ffffff;
  padding: 10px;
  font-size: 10px;
  min-height: 52px;
}
.unit-note {
  color: #657184;
  font-size: 9px;
  margin-top: 7px;
}
.handoff-status {
  margin-left: 10px;
  font-size: 10px;
  color: #16703a;
  font-weight: 700;
}
.date-wrap {
  position: relative;
}
.date-wrap input {
  padding-right: 72px;
}
.calendar-btn {
  position: absolute;
  right: 0;
  top: 0;
  width: 68px;
  height: 25px;
  border: 1px solid #9fafc5;
  background: #f7f9fc;
  font-size: 9px;
  cursor: pointer;
}
.calendar-pop {
  position: absolute;
  z-index: 5;
  width: 260px;
  border: 1px solid #9fafc5;
  background: white;
  box-shadow: 0 8px 18px rgba(20, 32, 48, .18);
  padding: 10px;
  font-size: 10px;
}
.cal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 700;
}
.cal-head button {
  width: 28px;
  height: 22px;
  border: 1px solid #bcc9dc;
  background: #f7f9fc;
  cursor: pointer;
}
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}
.cal-day, .cal-label {
  height: 24px;
  text-align: center;
  line-height: 24px;
}
.cal-label {
  color: #657184;
  font-weight: 700;
}
.cal-day {
  border: 1px solid #e1e7f0;
  cursor: pointer;
}
.cal-day:hover {
  background: #e9f2ff;
}
.cal-muted {
  color: #a0a8b5;
}
@media (max-width: 1180px) {
  .app, .login-app {
    min-width: 980px;
  }
  .kpi-row {
    grid-template-columns: repeat(4, minmax(170px, 1fr));
  }
  .grid-two {
    grid-template-columns: minmax(560px, 1fr) minmax(240px, 320px);
  }
  .form-panel {
    width: min(948px, calc(100vw - 220px));
  }
}
</style>
</head>
<body>
<div id="root"></div>
<script>
const DATA = __APP_DATA__;
const USERS = {
  "panasillies.user@panasonic.aero": { password: "password", name: "Panasillies User", role: "Campaign Manager" },
  "demo@panasonic.aero": { password: "panasonic", name: "Demo User", role: "Campaign Manager" }
};

let state = loadState();
if (!state) {
  state = {
    loggedIn: false,
    page: "Dashboard",
    user: null,
    currentCampaign: null,
    savedCampaigns: [],
    recommendations: [],
    allocation: [],
    generatedAlerts: [],
    loginError: "",
    rememberedEmail: "",
    formError: "",
    goal: "Branding",
    selectedAlert: null,
    alertFilter: "ALL",
    reviewedAlerts: {},
	    campaignStep: 1,
	    draftCampaign: {},
	    calendarField: null,
	    calendarMonth: null,
	    handoffStatus: ""
	  };
	}
state.goal = state.goal || "Branding";
state.selectedAlert = state.selectedAlert || null;
state.rememberedEmail = state.rememberedEmail || "";
state.alertFilter = state.alertFilter || "ALL";
state.reviewedAlerts = state.reviewedAlerts || {};
state.savedCampaigns = state.savedCampaigns || [];
state.generatedAlerts = state.generatedAlerts || [];
state.recommendations = state.recommendations || [];
state.allocation = state.allocation || [];
state.campaignStep = state.campaignStep || 1;
state.draftCampaign = state.draftCampaign || {};
state.calendarField = state.calendarField || null;
state.calendarMonth = state.calendarMonth || null;
state.handoffStatus = state.handoffStatus || "";
if (state.page === "A" + "I Zone Recommendation") state.page = "Zone Recommendation";
let migratedState = false;
const savedBeforeCleanup = state.savedCampaigns.length;
state.savedCampaigns = state.savedCampaigns.filter(campaign => !isTestCampaignName(campaign.name || campaign.campaign_name));
if (state.savedCampaigns.length !== savedBeforeCleanup) migratedState = true;
if (state.currentCampaign && isTestCampaignName(state.currentCampaign.name || state.currentCampaign.campaign_name)) {
  state.currentCampaign = null;
  state.recommendations = [];
  state.allocation = [];
  state.generatedAlerts = [];
  migratedState = true;
}
if (state.draftCampaign && isTestCampaignName(state.draftCampaign.name || state.draftCampaign.campaign_name)) {
  state.draftCampaign = {};
  migratedState = true;
}
state.generatedAlerts = state.generatedAlerts.map(alert => ({
  ...alert,
  reason: String(alert.reason || "").replace("A" + "I recommendation generated", "Zone recommendation generated"),
  action: String(alert.action || "")
}));
if (migratedState) saveState();

const navItems = [
  ["Dashboard", "Dashboard"],
  ["Create Campaign", "Create Campaign"],
  ["Zone Recommendation", "Zone Recommendation"],
  ["Flagged Campaign Alerts", "Flagged Campaign Alerts"],
  ["Delivery Monitoring", "Delivery Monitoring"],
  ["Recommendation Output", "Recommendation Output"],
  ["Pipeline Operations", "Pipeline Operations"]
];

function saveState() {
  localStorage.setItem("om3-demo-state", JSON.stringify(state));
}

function loadState() {
  try {
    return JSON.parse(localStorage.getItem("om3-demo-state"));
  } catch {
    return null;
  }
}

function money(value) {
  return Number(value || 0).toLocaleString();
}

function pct(value) {
  return Number(value || 0).toFixed(1) + "%";
}

function short(value, length) {
  value = String(value || "");
  return value.length > length ? value.slice(0, length - 1) + "..." : value;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function isTestCampaignName(name) {
  const normalized = String(name || "").trim();
  return /^xxxx\d*$/i.test(normalized)
    || /^illy 2026 demo campaign$/i.test(normalized)
    || /^panasillies test campaign$/i.test(normalized);
}

function formatDate(isoDate) {
  const [year, month, day] = String(isoDate).split("-");
  return `${month}/${day}/${year}`;
}

function parseDate(value) {
  const text = String(value || "").trim();
  const match = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!match) return null;
  const [, month, day, year] = match;
  const date = new Date(Number(year), Number(month) - 1, Number(day));
  if (date.getFullYear() !== Number(year) || date.getMonth() !== Number(month) - 1 || date.getDate() !== Number(day)) return null;
  return date;
}

function progress(value) {
  const width = Math.max(0, Math.min(100, Number(value || 0)));
  return `<div class="progress"><span style="width:${width}%"></span></div>`;
}

function render() {
  document.getElementById("root").innerHTML = !state.loggedIn ? loginPage() : appShell(routePage());
}

function appShell(main) {
  const user = state.user || { name: "xxxxx", role: "Campaign Manager" };
  const nav = navItems.map(([label, page]) => `
    <button class="nav ${state.page === page ? "active" : ""}" onclick="go('${page}')">${label}</button>
  `).join("");
  const topClass = pages => pages.includes(state.page) ? "toplink active" : "toplink";
  return `
    <div class="app">
      <div class="brand">OneMedia3 - Panasillies</div>
      <div class="topbar">
        <span class="${topClass(["Create Campaign"])}" onclick="go('Create Campaign')" title="Create campaign workflow">Campaigns</span>
        <span class="${topClass(["Dashboard"])}" onclick="go('Dashboard')" title="Campaign overview">Profile Setup</span>
        <span class="${topClass(["Flagged Campaign Alerts"])}" onclick="go('Flagged Campaign Alerts')" title="Review campaign alerts">Approvals</span>
        <span class="${topClass(["Zone Recommendation", "Recommendation Output"])}" onclick="go('Zone Recommendation')" title="Zone recommendation and allocation">MMA</span>
        <span class="${topClass(["Exports"])}" onclick="go('Exports')" title="Export recommendation report">Exports</span>
        <span class="${topClass(["Delivery Monitoring"])}" onclick="go('Delivery Monitoring')" title="Delivery report">Reports</span>
        <span class="${topClass(["Pipeline Operations"])}" onclick="go('Pipeline Operations')" title="Pipeline, OneMedia integration, and retraining">Ops</span>
        <span class="user">LOGGED IN AS: ${user.name}</span>
      </div>
      <div class="side">${nav}<button class="nav" onclick="handleDemoLogout()">Log Out</button></div>
      <main class="main">${main}</main>
    </div>
  `;
}

function routePage() {
  if (state.page === "Dashboard") return dashboardPage();
  if (state.page === "Create Campaign") return createCampaignPage();
  if (state.page === "Campaign Form Input") return createCampaignPage();
  if (state.page === "Zone Recommendation") return recommendationPage();
  if (state.page === "Flagged Campaign Alerts") return flaggedPage();
  if (state.page === "Delivery Monitoring") return monitoringPage();
  if (state.page === "Pipeline Operations") return pipelineOperationsPage();
  if (state.page === "Exports") return exportsPage();
  return recommendationOutputPage();
}

function go(page) {
  state.page = page;
  state.formError = "";
  state.calendarField = null;
  saveState();
  render();
}

function handleDemoLogout() {
  state.loggedIn = false;
  state.loginError = "";
  state.page = "Dashboard";
  saveState();
  render();
}

function loginPage() {
  const remembered = state.rememberedEmail || "panasillies.user@panasonic.aero";
  return `
    <div class="login-app">
      <div class="login-title">Panasonic</div>
      <div class="login-card">
        <div class="service">Panasonic Services</div>
        <input id="loginEmail" type="text" value="${remembered}" />
        <input id="loginPassword" type="password" value="password" />
        <button class="primary" onclick="login()">Login</button>
        <label class="remember">Remember Me <input id="remember" type="checkbox" ${state.rememberedEmail ? "checked" : ""} onchange="toggleRemember()" /></label>
        <div class="tiny-links">Forgot your password?<br/>Register for account</div>
      </div>
      ${state.loginError ? `<div class="login-error">${state.loginError}</div>` : ""}
      <div class="copyright">Copyright ©2026 Panasonic Avionics Corporation. All rights reserved.</div>
    </div>
  `;
}

function toggleRemember() {
  const remember = document.getElementById("remember").checked;
  const email = document.getElementById("loginEmail").value.trim();
  state.rememberedEmail = remember ? email : "";
  saveState();
  render();
}

function login() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  const remember = document.getElementById("remember").checked;
  const user = USERS[email];
  if (!user || user.password !== password) {
    state.loginError = "Invalid username or password. Try panasillies.user@panasonic.aero / password.";
    render();
    return;
  }
  state.loggedIn = true;
  state.user = { email, name: user.name, role: user.role };
  state.rememberedEmail = remember ? email : "";
  state.page = "Dashboard";
  state.loginError = "";
  saveState();
  render();
}

function pageTitle(crumb, title) {
  return `<div class="crumb">${crumb}</div><h1>${title}</h1>`;
}

function dashboardPage() {
  const savedRows = state.savedCampaigns.map(campaignRow);
  const campaigns = [...savedRows, ...DATA.campaigns];
  const active = campaigns.filter(c => !String(c.status || "").toLowerCase().includes("completed")).length;
  const alertRows = [...state.generatedAlerts, ...DATA.alerts];
  const flagged = alertRows.filter(a => ["CRITICAL", "WARNING"].includes(String(a.severity || "").toUpperCase())).length;
  const completed = DATA.feasibility.filter(row => Number(row.fulfillment_pct || 0) >= 99).length;
  const totalImpressions = DATA.campaigns.reduce((sum, row) => sum + Number(row.planned || 0), 0);
  const delivered = DATA.campaigns.reduce((sum, row) => sum + Number(row.delivered || 0), 0);
  const deliveryRate = totalImpressions ? delivered / totalImpressions * 100 : 0;
  const roi = (Number(DATA.fleetMetrics.ctr || 0) * 1000 + Number(DATA.fleetMetrics.video_completion_rate || 0) * 100).toFixed(1);
  const rows = campaigns.slice(0, 7).map(c => `
    <tr>
      <td><b>${short(c.campaign_name || c.name, 34)}</b></td>
      <td>${c.airline || c.revenue_type || "paid"}</td>
      <td>${progress(c.delivery_pct || c.progress || 0)}</td>
      <td>${c.status || "New"}</td>
      <td>${Number(c.pacing_ratio || 0).toFixed(2)}</td>
    </tr>
  `).join("");
  const alertPreview = alertRows
    .filter(a => ["CRITICAL", "WARNING"].includes(String(a.severity || "").toUpperCase()))
    .slice(0, 5)
    .map(a => `
      <tr>
        <td><span class="status ${riskClass(a.severity)}">${a.severity}</span></td>
        <td><b>${short(a.campaign_name || state.currentCampaign?.name || "New Campaign", 34)}</b></td>
        <td>${short(a.root_cause || a.reason, 42)}</td>
        <td>${suggestedAction(a)}</td>
      </tr>
    `).join("");
  const zoneRows = DATA.utilization.slice(0, 6).map(z => `
    <tr>
      <td><b>${short(z.zone_name, 34)}</b></td>
      <td>${money(z.total_allocated)}</td>
      <td>${money(z.capacity)}</td>
      <td>${pct(z.utilization_pct)}</td>
      <td><span class="status ${zoneHealth(z).toLowerCase()}">${zoneHealth(z)}</span></td>
    </tr>
  `).join("");
  return `
    ${pageTitle("OneMedia / Dashboard", "OneMedia3 Operations Dashboard")}
    <div class="kpi-row">
      ${kpi("Active Campaigns", money(active), "active campaigns")}
      ${kpi("Completed", money(completed), "completed campaigns")}
      ${kpi("Flagged", money(flagged), "alerts")}
      ${kpi("Delivery Rate", pct(deliveryRate), "overall delivery")}
    </div>
    <div class="kpi-row" style="margin-bottom:16px;">
      ${kpi("Total Impressions", money(Math.round(totalImpressions)), "planned")}
      ${kpi("ROI Index", roi, "modeled score")}
      ${kpi("Campaign Count", money(campaigns.length), "monitor rows")}
      ${kpi("Forecast Zones", money(DATA.forecasts.length), "zone capacity")}
    </div>
    <div class="grid-two">
      <div class="panel">
        <table class="table">
          <thead><tr><th>Campaign</th><th>Airline / Client</th><th>Progress</th><th>Status</th><th>Pacing</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <div class="panel" style="height:250px;">
        <div class="panel-head">Quick Entry</div>
        ${[
          ["Create Campaign", "Create Campaign"],
          ["Flagged Campaigns", "Flagged Campaign Alerts"],
	          ["Recommendation Result", "Recommendation Output"],
	          ["Delivery Monitoring", "Delivery Monitoring"],
	          ["Zone Recommendation", "Zone Recommendation"],
	          ["Pipeline Operations", "Pipeline Operations"]
	        ].map(x => `<div class="module" onclick="go('${x[1]}')">${x[0]}</div>`).join("")}
	      </div>
	    </div>
	    <div class="grid-even" style="margin-top:18px;">
	      <div class="panel scroll-panel">
	        <div class="panel-head">Active CRITICAL / WARNING Alerts</div>
	        <table class="table"><thead><tr><th>Risk</th><th>Campaign</th><th>Root Cause</th><th>Recommended Action</th></tr></thead><tbody>${alertPreview || `<tr><td colspan="4">No CRITICAL or WARNING alerts in the current output.</td></tr>`}</tbody></table>
	      </div>
	      <div class="panel scroll-panel">
	        <div class="panel-head">Zone Performance and Utilization</div>
	        <table class="table"><thead><tr><th>Zone</th><th>Allocated</th><th>Capacity</th><th>Utilization</th><th>Health</th></tr></thead><tbody>${zoneRows}</tbody></table>
	      </div>
	    </div>
	    <div class="source-line">Connected data: ${Object.entries(DATA.source).map(([k, v]) => `${k}: ${money(v)} rows`).join(" | ")}</div>
	  `;
	}

function createCampaignPage() {
  const step = state.campaignStep || 1;
  const title = step === 1 ? "Create Banner Campaign" : step === 2 ? "2a. Ad Group Details" : step === 3 ? "2b. Zone Identification" : "Step 3 - Budget & Cap";
  return `
    ${pageTitle("OneMedia / Campaigns / New", title)}
    ${stepper(step)}
    ${step === 1 ? campaignStepOne() : step === 2 ? campaignStepTwoA() : step === 3 ? campaignStepTwoB() : campaignStepThree()}
    ${state.formError ? `<div class="error">${state.formError}</div>` : ""}
    ${campaignSummary()}
  `;
}

function stepper(step) {
  const steps = [
    ["1", "Create Campaign"],
    ["2a", "Ad Group"],
    ["2b", "Zones"],
    ["3", "Budget & Clip"]
  ];
  return `
    <div class="stepper">
      <div class="step-line"></div>
      ${steps.map(([number, label], index) => `
        <div class="step-item">
          <div class="step-dot ${step === index + 1 ? "active" : ""}">${number}</div>
          <div class="step-label">${label}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function campaignStepOne() {
  const d = state.draftCampaign;
  return `
    <div class="panel form-panel">
      <div class="panel-head">Step 1 - Identify campaign advertiser and name your campaign</div>
      <div class="form-body">
        ${field("Campaign Type *", `<select id="campaignType" onchange="syncDraftPreview()"><option ${selected(d.campaignType, "Banner")}>Banner</option><option ${selected(d.campaignType, "Interstitial")}>Interstitial</option><option ${selected(d.campaignType, "Video")}>Video</option></select>`)}
        ${field("Creative Type", `<select id="creativeType" onchange="syncDraftPreview()"><option ${selected(d.creativeType, "Image / Rich Media")}>Image / Rich Media</option><option ${selected(d.creativeType, "Video Pre-roll")}>Video Pre-roll</option><option ${selected(d.creativeType, "Audio Spot")}>Audio Spot</option></select>`)}
        ${field("Revenue Type *", `<select id="revenueType" onchange="syncDraftPreview()"><option ${selected(d.revenueType, "House / Paid / Partner")}>House / Paid / Partner</option><option ${selected(d.revenueType, "Paid")}>Paid</option><option ${selected(d.revenueType, "Partner")}>Partner</option></select>`)}
        ${field("Campaign Name *", `<input id="campaignName" value="${d.name || "xxxx"}" oninput="syncDraftPreview()" />`)}
        ${field("Advertiser / Airline *", `<select id="airline" onchange="syncDraftPreview()"><option ${selected(d.airline, "Panasillies")}>Panasillies</option><option ${selected(d.airline, "Southwest")}>Southwest</option><option ${selected(d.airline, "United")}>United</option><option ${selected(d.airline, "Delta")}>Delta</option><option ${selected(d.airline, "Qatar")}>Qatar</option></select>`)}
        ${field("Start Date *", dateInput("startDate", d.start || formatDate(DATA.defaultStart)))}
        ${field("End Date *", dateInput("endDate", d.end || formatDate(DATA.defaultEnd)))}
        ${field("Destination URL", `<input id="destinationUrl" value="${d.destinationUrl || "https://panasillies.example"}" oninput="syncDraftPreview()" />`)}
      </div>
      <div class="goal-row">
        <button class="goal ${state.goal === "Branding" ? "active" : ""}" onclick="selectGoal(this, 'Branding');syncDraftPreview()">BRANDING</button>
        <button class="goal ${state.goal === "Consideration" ? "active" : ""}" onclick="selectGoal(this, 'Consideration');syncDraftPreview()">CONSIDERATION</button>
        <button class="goal ${state.goal === "Conversion" ? "active" : ""}" onclick="selectGoal(this, 'Conversion');syncDraftPreview()">CONVERSION</button>
      </div>
      <div class="action-row"><button class="primary" onclick="saveCampaignStep(2)">Save & Continue</button></div>
    </div>
    ${calendarPopup()}
  `;
}

function campaignStepTwoA() {
  const d = state.draftCampaign;
  return `
    <div class="panel form-panel">
      <div class="panel-head">Create New Ad Group</div>
      <div class="form-body">
        ${field("Name *", `<input id="adGroupName" value="${d.adGroupName || "Panasillies Banner Ad Group"}" />`)}
        ${field("Ad Group Start Date *", dateInput("adGroupStart", d.adGroupStart || d.start || formatDate(DATA.defaultStart)))}
        ${field("Ad Group End Date *", dateInput("adGroupEnd", d.adGroupEnd || d.end || formatDate(DATA.defaultEnd)))}
        ${field("Destination URL", `<input id="adGroupUrl" value="${d.adGroupUrl || d.destinationUrl || "https://panasillies.example"}" />`)}
        ${field("Ad Size / Placement", `<select id="placement"><option ${selected(d.placement, "Seatback / Sponsored Tile")}>Seatback / Sponsored Tile</option><option ${selected(d.placement, "Pre-roll")}>Pre-roll</option><option ${selected(d.placement, "Audio Companion")}>Audio Companion</option></select>`)}
        ${field("Creative Asset", `<input id="creativeAsset" value="${d.creativeAsset || "panasillies_banner_300x250.png"}" />`)}
      </div>
      <div class="notice" style="margin:10px 20px;width:900px;">Upload area: asset metadata is saved for demo and connected to the recommendation flow.</div>
      <div class="action-row"><button class="primary" onclick="saveCampaignStep(1)">Back</button><button class="primary" onclick="saveCampaignStep(3)" style="margin-left:8px;">Save & Continue</button></div>
    </div>
    ${calendarPopup()}
  `;
}

function campaignStepTwoB() {
  const d = state.draftCampaign;
  const candidateZones = (DATA.omZoneCandidates || []).slice(0, 12);
  const selectedZones = d.zones || candidateZones.slice(0, 5).map(row => row.zone_name);
  const rows = candidateZones.map(stat => `
    <tr>
      <td><input type="checkbox" class="zone" value="${escapeHtml(stat.zone_name)}" ${selectedZones.includes(stat.zone_name) ? "checked" : ""} onchange="syncDraftPreview()" /></td>
      <td><b>${escapeHtml(stat.zone_name)}</b></td>
      <td>${money(stat.daily_capacity)}</td>
      <td>${money(stat.available_capacity)}</td>
      <td>${money(stat.active_campaigns)}</td>
      <td>${Number(stat.zpr || 0).toFixed(2)}</td>
      <td>${Number(stat.score || 0).toFixed(1)}</td>
    </tr>
  `).join("");
  return `
    <div class="panel form-panel">
      <div class="panel-head">Zone Identification from pipeline_OM.py</div>
      <table class="table"><thead><tr><th></th><th>Zone Name</th><th>Forecast Capacity / Day</th><th>Available / Day</th><th>Active Campaigns</th><th>ZPR</th><th>OM Score</th></tr></thead><tbody>${rows}</tbody></table>
      <div class="unit-note" style="padding:8px 20px;">Zone options come from precomputed Model 1 capacity forecasts and pipeline_OM.py Phase 3 scoring logic.</div>
      <div class="action-row"><button class="primary" onclick="saveCampaignStep(2)">Back</button><button class="primary" onclick="saveCampaignStep(4)" style="margin-left:8px;">Save & Continue</button></div>
    </div>
  `;
}

function campaignStepThree() {
  const d = state.draftCampaign;
  return `
    <div class="panel form-panel">
      <div class="panel-head">Budget & Cap</div>
      <div class="form-body">
        ${field("Priority / Goal *", `<input id="priorityGoal" value="${d.priorityGoal || state.goal || "Branding"}" oninput="syncDraftPreview()" />`)}
        ${field("Target Impressions *", `<input id="target" type="number" value="${d.target || 850000}" min="1" oninput="syncDraftPreview()" />`)}
        ${field("Budget *", `<input id="budget" type="number" value="${d.budget || 125000}" min="0" oninput="syncDraftPreview()" />`)}
        ${field("Flight Impression Cap", `<input id="frequencyCap" type="number" value="${d.frequencyCap || 3}" min="1" oninput="syncDraftPreview()" />`)}
      </div>
      <div class="notice" style="margin:10px 20px;width:900px;">Final submit runs backend-derived zone scoring and allocation against your campaign input.</div>
      <div class="action-row"><button class="primary" onclick="saveCampaignStep(3)">Back</button><button class="primary" onclick="createCampaign()" style="margin-left:8px;">Save for Review</button></div>
    </div>
  `;
}

function validateCampaign(campaign) {
  if (!campaign.name.trim()) return "Campaign name is required.";
  if (!campaign.target || campaign.target <= 0) return "Target impressions must be greater than 0.";
  if (campaign.budget < 0) return "Budget cannot be negative.";
  if (!campaign.start || !campaign.end) return "Start date and end date are required.";
  const startDate = parseDate(campaign.start);
  const endDate = parseDate(campaign.end);
  if (!startDate || !endDate) return "Dates must use MM/DD/YYYY format.";
  if (endDate < startDate) return "End date cannot be earlier than start date.";
  if (!campaign.zones.length) return "Select at least one zone preference.";
  return "";
}

function openCalendar(fieldId) {
  const current = parseDate(valueOf(fieldId)) || new Date();
  state.calendarField = fieldId;
  state.calendarMonth = { year: current.getFullYear(), month: current.getMonth() };
  saveState();
  render();
}

function changeCalendarMonth(delta) {
  const cal = state.calendarMonth || { year: new Date().getFullYear(), month: new Date().getMonth() };
  const next = new Date(cal.year, cal.month + delta, 1);
  state.calendarMonth = { year: next.getFullYear(), month: next.getMonth() };
  saveState();
  render();
}

function pickDate(fieldId, month, day, year) {
  state.draftCampaign = state.draftCampaign || {};
  const value = `${String(month + 1).padStart(2, "0")}/${String(day).padStart(2, "0")}/${year}`;
  state.draftCampaign[fieldId] = value;
  if (fieldId === "startDate") state.draftCampaign.start = value;
  if (fieldId === "endDate") state.draftCampaign.end = value;
  if (fieldId === "adGroupStart") state.draftCampaign.adGroupStart = value;
  if (fieldId === "adGroupEnd") state.draftCampaign.adGroupEnd = value;
  state.calendarField = null;
  saveState();
  render();
}

function calendarPopup() {
  if (!state.calendarField) return "";
  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const cal = state.calendarMonth || { year: new Date().getFullYear(), month: new Date().getMonth() };
  const first = new Date(cal.year, cal.month, 1);
  const daysInMonth = new Date(cal.year, cal.month + 1, 0).getDate();
  const prevDays = new Date(cal.year, cal.month, 0).getDate();
  const cells = [];
  for (let i = 0; i < first.getDay(); i++) {
    cells.push(`<div class="cal-day cal-muted">${prevDays - first.getDay() + i + 1}</div>`);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push(`<div class="cal-day" onclick="pickDate('${state.calendarField}', ${cal.month}, ${day}, ${cal.year})">${day}</div>`);
  }
  while (cells.length % 7 !== 0) {
    cells.push(`<div class="cal-day cal-muted">${cells.length % 7}</div>`);
  }
  return `
    <div class="calendar-pop" style="left:390px;top:176px;">
      <div class="cal-head"><button onclick="changeCalendarMonth(-1)">‹</button><span>${monthNames[cal.month]} ${cal.year}</span><button onclick="changeCalendarMonth(1)">›</button></div>
      <div class="cal-grid">${weekdayNames.map(day => `<div class="cal-label">${day}</div>`).join("")}${cells.join("")}</div>
    </div>
  `;
}

function selected(value, option) {
  return (value || option) === option ? "selected" : "";
}

function dateInput(id, value) {
  return `<div class="date-wrap"><input id="${id}" value="${value}" placeholder="MM/DD/YYYY" /><button class="calendar-btn" onclick="openCalendar('${id}')">Calendar</button></div>`;
}

function saveCampaignStep(nextStep) {
  const step = state.campaignStep || 1;
  const d = state.draftCampaign || {};
  state.calendarField = null;
  if (step === 1) {
    Object.assign(d, {
      campaignType: valueOf("campaignType"),
      creativeType: valueOf("creativeType"),
      revenueType: valueOf("revenueType"),
      name: valueOf("campaignName") || "xxxx",
      airline: valueOf("airline"),
      start: valueOf("startDate"),
      end: valueOf("endDate"),
      destinationUrl: valueOf("destinationUrl"),
      goal: state.goal || "Branding"
    });
    const err = validateStepOne(d);
    if (err && nextStep > 1) {
      state.formError = err;
      render();
      return;
    }
  }
  if (step === 2) {
    Object.assign(d, {
      adGroupName: valueOf("adGroupName"),
      adGroupStart: valueOf("adGroupStart"),
      adGroupEnd: valueOf("adGroupEnd"),
      adGroupUrl: valueOf("adGroupUrl"),
      placement: valueOf("placement"),
      creativeAsset: valueOf("creativeAsset")
    });
    const err = validateAdGroup(d);
    if (err && nextStep > 2) {
      state.formError = err;
      render();
      return;
    }
  }
  if (step === 3) {
    d.zones = [...document.querySelectorAll(".zone:checked")].map(x => x.value);
    if (!d.zones.length && nextStep > 3) {
      state.formError = "Select at least one zone.";
      render();
      return;
    }
  }
  if (step === 4) {
    Object.assign(d, {
      priorityGoal: valueOf("priorityGoal"),
      target: Number(valueOf("target") || 0),
      budget: Number(valueOf("budget") || 0),
      frequencyCap: Number(valueOf("frequencyCap") || 0)
    });
  }
  state.draftCampaign = d;
  state.campaignStep = nextStep;
  state.formError = "";
  saveState();
  render();
}

function valueOf(id) {
  const el = document.getElementById(id);
  return el ? el.value : "";
}

function validateStepOne(d) {
  if (!d.name || !d.name.trim()) return "Campaign name is required.";
  if (!d.start || !d.end) return "Start date and end date are required.";
  const startDate = parseDate(d.start);
  const endDate = parseDate(d.end);
  if (!startDate || !endDate) return "Dates must use MM/DD/YYYY format.";
  if (endDate < startDate) return "End date cannot be earlier than start date.";
  return "";
}

function validateAdGroup(d) {
  if (!d.adGroupName || !d.adGroupName.trim()) return "Ad group name is required.";
  const startDate = parseDate(d.adGroupStart);
  const endDate = parseDate(d.adGroupEnd);
  if (!startDate || !endDate) return "Ad group dates must use MM/DD/YYYY format.";
  if (endDate < startDate) return "Ad group end date cannot be earlier than start date.";
  return "";
}

function selectGoal(button, goal) {
  state.goal = goal;
  document.querySelectorAll(".goal").forEach(item => item.classList.remove("active"));
  button.classList.add("active");
}

function createCampaign() {
  const d = state.draftCampaign || {};
  Object.assign(d, {
    priorityGoal: valueOf("priorityGoal"),
    target: Number(valueOf("target") || 0),
    budget: Number(valueOf("budget") || 0),
    frequencyCap: Number(valueOf("frequencyCap") || 0)
  });
  state.draftCampaign = d;
  const campaign = {
    id: Date.now(),
    name: d.name || "xxxx",
    airline: d.airline || "Panasillies",
    target: Number(d.target || 0),
    budget: Number(d.budget || 0),
    start: d.start,
    end: d.end,
    goal: d.goal || state.goal || "Branding",
    zones: d.zones || [],
    campaignType: d.campaignType,
    adGroupName: d.adGroupName,
    placement: d.placement,
    frequencyCap: d.frequencyCap
  };
  const error = validateCampaign(campaign);
  if (error) {
    state.formError = error;
    state.campaignStep = 4;
    render();
    return;
  }
  state.formError = "";
  state.currentCampaign = campaign;
  state.recommendations = recommend(campaign);
  state.allocation = allocate(campaign, state.recommendations);
  state.generatedAlerts = alerts(campaign, state.allocation);
  state.savedCampaigns = [campaign, ...state.savedCampaigns.filter(c => c.id !== campaign.id)].slice(0, 8);
  state.page = "Zone Recommendation";
  state.campaignStep = 1;
  saveState();
  render();
}

function campaignSummary() {
  const summary = liveSummaryData();
  return `
    <div class="notice" id="campaignSummaryLive">
      <b>Campaign Summary:</b> ${summary.name} | ${summary.airline} | selected zones: ${summary.zones.join(", ")} |
      target impressions: ${money(summary.target)} | estimated delivery: ${money(summary.delivery)} | status: ${summary.status}
    </div>
  `;
}

function liveSummaryData() {
  const d = state.draftCampaign || {};
  const current = state.currentCampaign || {};
  const name = valueOf("campaignName") || d.name || current.name || "xxxx";
  const airline = valueOf("airline") || d.airline || current.airline || "Panasillies";
  const zonesFromDom = [...document.querySelectorAll(".zone:checked")].map(x => x.value);
  const zones = zonesFromDom.length ? zonesFromDom : (d.zones && d.zones.length ? d.zones : current.zones && current.zones.length ? current.zones : ["Movies", "TV", "Audio"]);
  const target = Number(valueOf("target") || d.target || current.target || 850000);
  const goal = valueOf("priorityGoal") || d.goal || current.goal || state.goal || "Branding";
  const delivery = estimateDeliveryFromInputs(target, zones, goal);
  return {
    name,
    airline,
    zones,
    target,
    delivery,
    status: "Recommendation Ready"
  };
}

function estimateDeliveryFromInputs(target, zones, goal) {
  const campaign = {
    target: Number(target || 0),
    zones: zones || [],
    goal: goal || "Branding"
  };
  const selectedExpected = recommend(campaign)
    .filter(row => campaign.zones.includes(row.zone))
    .reduce((sum, row) => sum + Number(row.expected || 0), 0);
  return Math.round(Math.min(Number(target || 0), selectedExpected || Number(target || 0)));
}

function syncDraftPreview() {
  const box = document.getElementById("campaignSummaryLive");
  if (!box) return;
  const summary = liveSummaryData();
  box.innerHTML = `<b>Campaign Summary:</b> ${summary.name} | ${summary.airline} | selected zones: ${summary.zones.join(", ")} | target impressions: ${money(summary.target)} | estimated delivery: ${money(summary.delivery)} | status: ${summary.status}`;
}

function recommendationPage() {
  if (!state.currentCampaign) return emptyState("OneMedia / Recommendation", "Zone Recommendation");
  const selectedZones = state.currentCampaign.zones || [];
  const cards = state.recommendations.slice(0, 5).map(r => `
    <div class="rec-card ${selectedZones.includes(r.zone) ? "selected" : ""}">
      <div class="title">${escapeHtml(r.zone)} <span style="float:right;">${pct(r.fit)}</span></div>
      <div class="body">
        Priority: <b>${r.priority}</b><br/>
        Predicted impressions: <b>${money(r.expected)} impressions</b><br/>
        Forecast capacity: <b>${money(r.capacity)} impressions/day</b><br/>
        Confidence: <b>${pct(r.confidence)}</b><br/>
        ${escapeHtml(r.reason)}
      </div>
    </div>
  `).join("");
  const zoneControls = state.recommendations.map(r => `
    <label class="zone-pick">
      <input type="checkbox" class="manual-zone" value="${escapeHtml(r.zone)}" ${selectedZones.includes(r.zone) ? "checked" : ""} />
      ${escapeHtml(r.zone)}
    </label>
  `).join("");
  const rows = state.recommendations.map(r => `
    <tr><td><b>${escapeHtml(r.zone)}</b></td><td>${selectedZones.includes(r.zone) ? "Selected" : "Available"}</td><td>${r.priority}</td><td>${money(r.expected)}</td><td>${money(r.capacity)}</td><td>${pct(r.confidence)}</td><td>${Number(r.score || 0).toFixed(1)}</td><td>${escapeHtml(r.reason)}</td></tr>
  `).join("");
  return `
    ${pageTitle("OneMedia / Recommendation", "Zone Recommendation")}
    <div class="card-grid">${cards}</div>
	    <div class="notice">
	      <b>Campaign:</b> ${escapeHtml(state.currentCampaign.name)} |
	      <b>Selected zones:</b> ${selectedZones.map(escapeHtml).join(", ") || "None"}
      <div class="decision-row">
        ${zoneControls}
      </div>
      <button class="primary" onclick="acceptTopZones()">Accept System Recommendation</button>
      <button class="primary" onclick="applyManualZones()" style="margin-left:8px;">Apply Modified Zones</button>
      <button class="primary" onclick="go('Recommendation Output')" style="margin-left:8px;">Review Allocation</button>
      ${state.formError ? `<div class="error" style="margin-left:0;">${state.formError}</div>` : ""}
    </div>
	    <div class="panel form-panel">
	      <div class="panel-head">Zone Recommendation Detail from pipeline_OM.py</div>
		      <table class="table"><thead><tr><th>Zone</th><th>Decision</th><th>Priority</th><th>Predicted Impressions</th><th>Forecast Capacity / Day</th><th>Confidence Score</th><th>OM Score</th><th>Reason</th></tr></thead><tbody>${rows}</tbody></table>
	    </div>
	    <div class="unit-note">Recommendation source: ${DATA.omRecommendationSource}. The frontend uses pipeline_OM zone candidates and only handles user accept/modify interactions.</div>
	  `;
	}

function monitoringPage() {
  const rows = [...state.savedCampaigns.map(campaignRow), ...DATA.campaigns].slice(0, 12).map(r => {
    const delivered = Number(r.delivered || 0);
    const planned = Number(r.planned || r.target || 0);
    const remaining = Math.max(planned - delivered, 0);
    const status = monitorStatus(r);
    return `
      <tr>
        <td><b>${short(r.campaign_name || r.name, 35)}</b></td>
        <td>${money(delivered)}</td>
        <td>${money(remaining)}</td>
        <td>${progress(r.delivery_pct || 0)}</td>
        <td>${Number(r.pacing_ratio || 0).toFixed(2)}</td>
        <td>${r.predicted_final_delivery_pct ? pct(r.predicted_final_delivery_pct) : projectedCompletionLabel(r)}</td>
        <td>${r.feasibility || feasibilityLabel(r)}</td>
        <td><span class="status ${status.toLowerCase().replaceAll(" ", "-")}">${status}</span></td>
      </tr>
    `;
  }).join("");
  const zoneRows = DATA.utilization.slice(0, 8).map(z => `
    <tr><td><b>${short(z.zone_name, 34)}</b></td><td>${money(z.total_allocated)}</td><td>${money(z.capacity)}</td><td>${pct(z.utilization_pct)}</td><td>${zoneAction(z)}</td></tr>
  `).join("");
  const chartBars = DATA.campaigns.slice(0, 12).map(r => `<div class="bar" style="height:${Math.max(8, Math.min(88, Number(r.delivery_pct || 0)))}px" title="${short(r.campaign_name, 20)}"></div>`).join("");
  return `
    ${pageTitle("OneMedia / Monitoring", "Delivery Monitoring")}
    <div class="grid-two">
      <div class="panel scroll-panel">
        <div class="panel-head">Live Campaign Tracking</div>
        <table class="table"><thead><tr><th>Campaign</th><th>Delivered</th><th>Remaining</th><th>Progress</th><th>Pacing</th><th>Predicted Final</th><th>Feasibility</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>
      </div>
      <div class="panel">
        <div class="panel-head">Delivery Progress Snapshot</div>
        <div class="bar-chart">${chartBars}</div>
        <div style="padding:0 10px 12px;font-size:10px;color:#657184;">Auto-refresh feel: latest pipeline output loaded from output_pacing.csv.</div>
      </div>
    </div>
    <div class="panel form-panel scroll-panel" style="margin-top:18px;">
      <div class="panel-head">Zone Utilization Monitor</div>
      <table class="table"><thead><tr><th>Zone</th><th>Allocated</th><th>Capacity</th><th>Utilization</th><th>Action</th></tr></thead><tbody>${zoneRows}</tbody></table>
    </div>
  `;
}

function flaggedPage() {
  const filter = state.alertFilter || "ALL";
  const generatedAlerts = state.generatedAlerts
    .map((alert, index) => ({ ...alert, index }))
    .filter(a => filter === "ALL" || String(a.severity).toUpperCase() === filter);
  const backendAlerts = DATA.alerts
    .map((alert, index) => ({ ...alert, index }))
    .filter(a => filter === "ALL" || String(a.severity).toUpperCase() === filter);
  const filters = ["ALL", "CRITICAL", "WARNING", "WATCH", "OK"].map(item => `
    <button class="filter-btn ${filter === item ? "active" : ""}" onclick="setAlertFilter('${item}')">${item}</button>
  `).join("");
  const generated = generatedAlerts.map(a => `
    <tr class="clickable-row" onclick="selectAlert('new', ${a.index})"><td><span class="status ${riskClass(a.severity)}" onclick="event.stopPropagation();setAlertFilter('${String(a.severity).toUpperCase()}')">${a.severity}</span></td><td>${a.pi || "-"}</td><td><b>${a.reason}</b></td><td>${a.action}</td></tr>
  `).join("");
  const existing = backendAlerts.map(a => `
    <tr class="clickable-row" onclick="selectAlert('backend', ${a.index})">
	      <td><b>${short(a.campaign_name, 38)}</b></td>
	      <td><span class="status ${riskClass(a.severity)}" onclick="event.stopPropagation();setAlertFilter('${String(a.severity).toUpperCase()}')">${a.severity}</span></td>
	      <td>${Number(a.pi || 0).toFixed(2)}</td>
	      <td>${a.root_cause}</td>
	      <td>${suggestedAction(a)}</td>
    </tr>
  `).join("");
  const detail = alertDetail();
  return `
    ${pageTitle("OneMedia / Alerts", "Flagged Campaign Alerts")}
    <div class="panel form-panel" style="margin-bottom:18px;">
      <div class="panel-head">New Campaign Alerts</div>
      <div class="filter-row">${filters}<span style="font-size:9px;color:#657184;line-height:22px;">Click a risk level to filter. Click a row to inspect details.</span></div>
	      <table class="table"><thead><tr><th>Risk</th><th>PI</th><th>Alert Reason</th><th>Suggested Action</th></tr></thead><tbody>${generated || `<tr><td colspan="4">Create a campaign to generate recommendation risk alerts.</td></tr>`}</tbody></table>
    </div>
    ${detail}
    <div class="panel form-panel scroll-panel" style="margin-top:12px;max-height:210px;">
      <div class="panel-head">Flagged Campaign Page from output_alerts.csv</div>
	      <table class="table"><thead><tr><th>Campaign</th><th>Risk</th><th>PI</th><th>Alert Reason</th><th>Suggested Action</th></tr></thead><tbody>${existing || `<tr><td colspan="5">No backend alerts match this filter.</td></tr>`}</tbody></table>
    </div>
  `;
}

function setAlertFilter(filter) {
  state.alertFilter = filter;
  state.selectedAlert = null;
  saveState();
  render();
}

function selectAlert(type, index) {
  state.selectedAlert = { type, index };
  saveState();
  render();
}

function alertDetail() {
  if (!state.selectedAlert) return `<div class="detail-box">Click any risk row to inspect the alert and suggested action.</div>`;
  const alert = state.selectedAlert.type === "new" ? state.generatedAlerts[state.selectedAlert.index] : DATA.alerts[state.selectedAlert.index];
  if (!alert) return `<div class="detail-box">Click any risk row to inspect the alert and suggested action.</div>`;
  const campaign = alert.campaign_name || state.currentCampaign?.name || "New Campaign";
  const reason = alert.root_cause || alert.reason;
  const action = alert.action || suggestedAction(alert);
  const key = `${state.selectedAlert.type}-${state.selectedAlert.index}`;
  const reviewed = state.reviewedAlerts[key] ? "Reviewed" : "Needs Review";
  return `
    <div class="detail-box">
      <b>Selected Risk Detail</b><br/>
      Campaign: ${campaign}<br/>
      Review status: ${reviewed}<br/>
      Reason: ${reason}<br/>
      Suggested action: ${action}<br/>
      <button class="primary" onclick="markAlertReviewed()" style="margin-top:8px;">Mark Reviewed</button>
      <button class="primary" onclick="go('Recommendation Output')" style="margin-top:8px;margin-left:8px;">Review Recommendation Output</button>
    </div>
  `;
}

function markAlertReviewed() {
  if (!state.selectedAlert) return;
  const key = `${state.selectedAlert.type}-${state.selectedAlert.index}`;
  state.reviewedAlerts[key] = true;
  saveState();
  render();
}

function recommendationOutputPage() {
  if (!state.currentCampaign) return backendRecommendationOutput();
  const rows = state.allocation.map(r => `
    <tr><td><b>${r.zone}</b></td><td>${pct(r.share)}</td><td>${money(r.allocated)}</td><td>${money(r.forecast)}</td><td>${r.status}</td></tr>
  `).join("");
  const legend = allocationLegend(state.allocation);
  const completion = Math.min(100, state.allocation.reduce((sum, r) => sum + Math.min(r.forecast, r.allocated), 0) / state.currentCampaign.target * 100);
  const roi = projectedRoi(state.currentCampaign, completion);
  return `
    ${pageTitle("OneMedia / Output", "Recommendation Output")}
    <div class="grid-two">
      <div class="panel">
        <div class="panel-head">Final Recommendation Summary</div>
        <table class="table"><thead><tr><th>Selected Zone</th><th>Allocation %</th><th>Allocated Impressions</th><th>Forecast Capacity / Day</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>
        <div class="unit-note">Allocation % = share of campaign target impressions. Allocated impressions = campaign-level target allocation. Forecast capacity/day = backend zone daily capacity.</div>
      </div>
      <div class="panel">
        <div class="panel-head">Allocation Visualization</div>
        <div class="pie" style="background:${pieGradient(state.allocation)}"></div>
        <div class="legend">${legend}</div>
        <div style="padding:0 16px 12px;font-size:11px;">
          Visualization unit: allocation share (% of campaign target impressions).<br/>
          Data basis: current campaign allocation calculated from forecast capacity and utilization outputs.<br/>
          Recommended allocation strategy: prioritize zones with stronger backend capacity and fit score.<br/>
          Expected completion rate: <b>${pct(completion)}</b><br/>
          Projected ROI: <b>${roi}x</b>
        </div>
      </div>
    </div>
	    <div class="notice">
	      <button class="primary" onclick="confirmAllocation()">Confirm Allocation</button>
	      <button class="primary" onclick="createOneMediaHandoff()" style="margin-left:8px;">Create OneMedia Handoff</button>
	      <button class="primary" onclick="applyZoneSwapPlan()" style="margin-left:8px;">Stage Zone Swap</button>
	      <button class="primary" onclick="downloadReport()" style="margin-left:8px;">Download Report</button>
	      <span id="confirmMsg" class="handoff-status">${state.handoffStatus}</span>
	    </div>
	  `;
	}

function backendRecommendationOutput() {
  const priorityRows = DATA.priority.slice(0, 8).map(r => `
    <tr><td>${r.queue_position}</td><td><b>${short(r.campaign_name, 42)}</b></td><td>${Number(r.priority_score || 0).toFixed(1)}</td><td>${Number(r.zone_fit || 0).toFixed(1)}</td><td>${r.goal_type}</td></tr>
  `).join("");
  const feasibilityRows = DATA.feasibility.slice(0, 8).map(r => `
    <tr><td><b>${short(r.campaign_name, 42)}</b></td><td>${money(r.planned_daily)}</td><td>${money(r.allocated_daily)}</td><td>${pct(r.fulfillment_pct)}</td><td>${r.confidence}</td></tr>
  `).join("");
  return `
    ${pageTitle("OneMedia / Output", "Recommendation Output")}
    <div class="grid-two">
      <div class="panel scroll-panel"><div class="panel-head">Priority Recommendation</div><table class="table"><thead><tr><th>Queue</th><th>Campaign</th><th>Priority</th><th>Zone Fit</th><th>Goal</th></tr></thead><tbody>${priorityRows}</tbody></table></div>
      <div class="panel scroll-panel"><div class="panel-head">Feasibility Output</div><table class="table"><thead><tr><th>Campaign</th><th>Planned</th><th>Allocated</th><th>Fulfillment</th><th>Confidence</th></tr></thead><tbody>${feasibilityRows}</tbody></table></div>
    </div>
	  `;
	}

function pipelineOperationsPage() {
  const sourceRows = Object.entries(DATA.source).map(([name, count]) => `
    <tr><td><b>${name}</b></td><td>${money(count)}</td><td>${exportPurpose(name)}</td></tr>
  `).join("");
  const zoneRows = (DATA.omZoneCandidates || []).slice(0, 10).map(z => `
    <tr><td><b>${escapeHtml(z.zone_name)}</b></td><td>${money(z.daily_capacity)}</td><td>${money(z.available_capacity)}</td><td>${money(z.active_campaigns)}</td><td>${zoneOpsAction(z)}</td></tr>
  `).join("");
  const integrationRows = [
    ["Nightly pipeline", "Ready", "Reads Athena-derived CSV outputs and refreshes dashboard tables"],
    ["New campaign intake", state.currentCampaign ? "Ready" : "Waiting", state.currentCampaign ? `Current campaign: ${state.currentCampaign.name}` : "Create a campaign to generate recommendations"],
    ["OneMedia handoff", state.handoffStatus ? "Staged" : "Ready", state.handoffStatus || "Use recommendation output to stage handoff"],
    ["Monthly retraining", "Tracked", "Model artifacts and metrics are visible without changing backend data"]
  ].map(row => `<tr><td><b>${row[0]}</b></td><td><span class="status ${row[1].toLowerCase()}">${row[1]}</span></td><td>${row[2]}</td></tr>`).join("");
  return `
    ${pageTitle("OneMedia / Ops", "Pipeline Operations")}
    <div class="ops-grid">
      <div class="ops-card">
        <div class="panel-head">Integration Status</div>
        <div class="body"><table class="table"><thead><tr><th>Area</th><th>Status</th><th>Detail</th></tr></thead><tbody>${integrationRows}</tbody></table></div>
      </div>
      <div class="ops-card">
        <div class="panel-head">Zone Swap Queue</div>
        <div class="body">
          <span class="pill">Manual Review</span><span class="pill">API Ready</span><span class="pill">No backend write</span>
          <div style="margin-top:10px;">${state.currentCampaign ? `Campaign: <b>${state.currentCampaign.name}</b><br/>Selected zones: <b>${state.currentCampaign.zones.join(", ")}</b>` : "No campaign selected"}</div>
          <button class="primary" onclick="go('Recommendation Output')" style="margin-top:10px;">Review Allocation</button>
        </div>
      </div>
    </div>
    <div class="grid-even" style="margin-top:18px;">
      <div class="panel scroll-panel">
        <div class="panel-head">Data Sources</div>
        <table class="table"><thead><tr><th>Source</th><th>Rows</th><th>Purpose</th></tr></thead><tbody>${sourceRows}</tbody></table>
      </div>
      <div class="panel scroll-panel">
        <div class="panel-head">Zone Recommendation Inputs</div>
        <table class="table"><thead><tr><th>Zone</th><th>Capacity</th><th>Available</th><th>Active Campaigns</th><th>Action</th></tr></thead><tbody>${zoneRows}</tbody></table>
      </div>
    </div>
  `;
}

function exportsPage() {
  const sourceRows = Object.entries(DATA.source).map(([name, count]) => `
    <tr><td><b>${name}</b></td><td>${money(count)} rows</td><td>${exportPurpose(name)}</td></tr>
  `).join("");
  const allocationRows = state.currentCampaign ? state.allocation.map(r => `
    <tr><td>${r.zone}</td><td>${pct(r.share)}</td><td>${money(r.allocated)}</td><td>${money(r.forecast)}</td><td>${r.status}</td></tr>
  `).join("") : DATA.allocations.slice(0, 8).map(r => `
    <tr><td>${short(r.zone_name, 32)}</td><td>${pct(Number(r.allocation_weight || 0) * 100)}</td><td>${money(r.allocated_impressions)}</td><td>${money(r.zone_capacity)}</td><td>Backend allocation</td></tr>
  `).join("");
  return `
    ${pageTitle("OneMedia / Exports", "Exports")}
    <div class="grid-two">
      <div class="panel">
        <div class="panel-head">Export Controls</div>
        <div style="padding:14px 16px;font-size:11px;line-height:18px;">
          Export uses the same backend pipeline data shown in the dashboard and recommendation pages.<br/>
          Current campaign: <b>${state.currentCampaign ? state.currentCampaign.name : "No new campaign selected"}</b><br/>
          Output basis: <b>${state.currentCampaign ? "current campaign recommendation + allocation" : "latest backend allocation output"}</b>
          <div style="margin-top:12px;">
            <button class="primary" onclick="downloadReport()">Download JSON Report</button>
            <button class="primary" onclick="downloadAllocationCsv()" style="margin-left:8px;">Download Allocation CSV</button>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-head">Backend Data Used</div>
        <table class="table"><thead><tr><th>Source File</th><th>Rows</th><th>Used For</th></tr></thead><tbody>${sourceRows}</tbody></table>
      </div>
    </div>
    <div class="panel form-panel" style="margin-top:14px;">
      <div class="panel-head">Export Preview</div>
      <table class="table"><thead><tr><th>Zone</th><th>Allocation %</th><th>Allocated Impressions</th><th>Forecast Capacity / Day</th><th>Status / Confidence</th></tr></thead><tbody>${allocationRows}</tbody></table>
    </div>
    <div class="unit-note">Export preview is generated from ${state.currentCampaign ? "the current campaign allocation" : "output_allocations.csv"} and zone capacity data loaded from this repository folder.</div>
  `;
}

function recommend(campaign) {
  const candidates = DATA.omZoneCandidates || [];
  const dailyNeed = dailyTarget(campaign);
  const selectedNames = new Set(campaign.zones || []);
  const targetAvailable = dailyNeed * 1.2;
  let cumulative = 0;
  const rows = [];
  const preferred = candidates.filter(row => selectedNames.has(row.zone_name));
  const remaining = candidates.filter(row => !selectedNames.has(row.zone_name));
  for (const row of [...preferred, ...remaining]) {
    const capacity = Number(row.daily_capacity || 0);
    const available = Number(row.available_capacity || 0);
    const score = Number(row.score || 0);
    const fit = Math.max(50, Math.min(99, score > 0 ? 55 + Math.log10(score + 1) * 13 : 50));
    cumulative += available;
    rows.push({
      zone: row.zone_name,
      category: row.category,
      priority: rows.length < 3 ? "P1" : rows.length < 8 ? "P2" : "P3",
      fit,
      confidence: Math.max(55, Math.min(98, 62 + Number(row.zpr || 0) * 10 + Math.log10(available + 1) * 5)),
      expected: Math.round(Math.min(available, dailyNeed)),
      capacity: Math.round(capacity),
      available,
      avgUtil: capacity ? Math.min(100, available / capacity * 100) : 0,
      active: Number(row.active_campaigns || 0),
      forecastRows: 1,
      zpr: Number(row.zpr || 0),
      score,
      reason: `pipeline_OM score uses Model 1 capacity, active campaign competition, available capacity, and capped ZPR. Available/day: ${money(available)}; ZPR: ${Number(row.zpr || 0).toFixed(2)}.`
    });
    if (rows.length >= 5 && cumulative >= targetAvailable) break;
  }
  return rows;
}

function allocate(campaign, recs) {
  const selected = campaign.zones && campaign.zones.length
    ? recs.filter(row => campaign.zones.includes(row.zone))
    : recs.slice(0, 3);
  const usable = selected.length ? selected : recs.slice(0, 3);
  const total = usable.reduce((sum, row) => sum + Number(row.available || row.fit || 0), 0);
  return usable.map(row => {
    const weight = Number(row.available || row.fit || 0);
    const share = total ? weight / total * 100 : 0;
    const allocated = Math.round(campaign.target * share / 100);
    return {
      zone: row.zone,
      forecast: row.capacity,
      allocated,
      share,
      status: row.capacity >= allocated ? "Matched" : "Inventory Watch"
    };
  });
}

function refreshCampaignOutputs() {
  if (!state.currentCampaign) return;
  state.recommendations = recommend(state.currentCampaign);
  state.allocation = allocate(state.currentCampaign, state.recommendations);
  state.generatedAlerts = alerts(state.currentCampaign, state.allocation);
  state.savedCampaigns = [state.currentCampaign, ...state.savedCampaigns.filter(c => c.id !== state.currentCampaign.id)].slice(0, 8);
  saveState();
}

function acceptTopZones() {
  if (!state.currentCampaign) return;
  const targetDaily = dailyTarget(state.currentCampaign);
  const picked = [];
  let capacity = 0;
  for (const row of state.recommendations) {
    picked.push(row.zone);
    capacity += Number(row.capacity || 0);
    if (picked.length >= 3 && capacity >= targetDaily * 1.2) break;
  }
  state.currentCampaign.zones = picked.length ? picked : state.recommendations.slice(0, 3).map(row => row.zone);
  refreshCampaignOutputs();
  render();
}

function applyManualZones() {
  if (!state.currentCampaign) return;
  const picked = [...document.querySelectorAll(".manual-zone:checked")].map(item => item.value);
  if (!picked.length) {
    state.formError = "Select at least one zone.";
    render();
    return;
  }
  state.formError = "";
  state.currentCampaign.zones = picked;
  refreshCampaignOutputs();
  render();
}

function dailyTarget(campaign) {
  const start = parseDate(campaign.start);
  const end = parseDate(campaign.end);
  const days = start && end ? Math.max(1, (end - start) / 86400000) : 30;
  return Number(campaign.target || 0) / days;
}

function alerts(campaign, allocation) {
  const rows = [];
  const watch = allocation.filter(row => row.status !== "Matched");
  if (watch.length) {
    rows.push({ severity: "WARNING", pi: "0.72", reason: "Low inventory in selected zones", action: `Shift impressions to ${allocation[0].zone} or extend campaign duration.` });
  }
  const days = Math.max(1, (parseDate(campaign.end) - parseDate(campaign.start)) / 86400000);
  if (campaign.target / days > 75000) {
    rows.push({ severity: "CRITICAL", reason: "Aggressive daily impression target", action: "Increase allocation to Audio/TV or extend campaign duration." });
  }
  rows.push({ severity: "OK", reason: "Zone recommendation generated", action: "Confirm allocation and monitor pacing after launch." });
  return rows;
}

function campaignRow(campaign) {
  return {
    campaign_name: campaign.name,
    name: campaign.name,
    airline: campaign.airline,
    planned: campaign.target,
    delivered: Math.round(campaign.target * 0.02),
	    delivery_pct: 2,
	    pacing_ratio: 0.18,
	    status: campaign.status || "New - Recommendation Ready",
	    severity: "WARNING"
	  };
	}

function monitorStatus(row) {
  if (String(row.status || "").toLowerCase().includes("completed")) return "Completed";
  if (String(row.severity || "").toLowerCase().includes("critical")) return "At Risk";
  if (String(row.severity || "").toLowerCase().includes("warning")) return "Delayed";
  if (Number(row.pacing_ratio || 0) < 0.5) return "Delayed";
  return "On Track";
}

function suggestedAction(alert) {
  const cause = String(alert.root_cause || alert.reason || "").toLowerCase();
  if (cause.includes("inventory")) return "Shift demand to higher-capacity zones.";
  if (cause.includes("aggressive")) return "Extend campaign duration or add zone coverage.";
  if (cause.includes("pacing")) return "Increase allocation to Audio or TV.";
  if (cause.includes("zone")) return "Shift impressions to higher-capacity zones.";
  return "Extend campaign duration and re-run allocation.";
}

function riskClass(severity) {
  const value = String(severity || "").toLowerCase();
  if (value.includes("critical")) return "critical";
  if (value.includes("warning")) return "warning";
  if (value.includes("watch")) return "watch";
  if (value.includes("ok")) return "ok";
  return "watch";
}

function projectedCompletionLabel(row) {
  if (row.delivery_pct) return pct(Math.min(100, Number(row.delivery_pct || 0) * 1.6));
  return "2.0%";
}

function feasibilityLabel(row) {
  const pacing = Number(row.pacing_ratio || 0);
  if (pacing < 0.5) return "Needs Boost";
  if (pacing < 0.8) return "Watch";
  return "OK";
}

function zoneHealth(row) {
  const util = Number(row.utilization_pct || row.avg_utilization_pct || 0);
  if (util >= 95) return "Watch";
  if (util >= 80) return "Warning";
  return "OK";
}

function zoneAction(row) {
  const util = Number(row.utilization_pct || 0);
  if (util >= 95) return "Shift demand to lower-utilization zones.";
  if (util >= 80) return "Keep capacity buffer and monitor pacing.";
  return "Available for incremental allocation.";
}

function zoneOpsAction(row) {
  const util = Number(row.avg_utilization_pct || 0);
  if (util >= 80) return "Review before approval";
  if (Number(row.capacity || row.daily_capacity || 0) <= 0) return "Capacity check";
  if (Number(row.zpr || 1) < 0.3) return "Watch ZPR";
  return "Eligible";
}

function projectedRoi(campaign, completion) {
  const budgetEfficiency = campaign.budget ? campaign.target / campaign.budget : 1;
  return Math.max(1.1, Math.min(4.8, budgetEfficiency / 9 + completion / 80)).toFixed(2);
}

const ZONE_COLORS = {
  TV: "#2b6eac",
  Movies: "#7aa2d6",
  Games: "#a7bdd7",
  Retail: "#d2dbe8",
  Audio: "#5e83b7"
};

function zoneColor(zone, index) {
  const fallback = ["#2b6eac", "#7aa2d6", "#a7bdd7", "#d2dbe8", "#5e83b7", "#9fb3cc"];
  return ZONE_COLORS[zone] || fallback[index % fallback.length];
}

function pieGradient(allocation) {
  if (!allocation.length) return "conic-gradient(#d2dbe8 0 100%)";
  let current = 0;
  const segments = allocation.map((row, index) => {
    const start = current;
    const end = Math.min(100, current + Number(row.share || 0));
    current = end;
    return `${zoneColor(row.zone, index)} ${start.toFixed(2)}% ${end.toFixed(2)}%`;
  });
  if (current < 100) segments.push(`#eef2f7 ${current.toFixed(2)}% 100%`);
  return `conic-gradient(${segments.join(", ")})`;
}

function allocationLegend(allocation) {
  return allocation.map((row, index) => `
    <div class="legend-item">
      <span class="swatch" style="background:${zoneColor(row.zone, index)}"></span>
      <span>${row.zone} - ${money(row.allocated)} impressions</span>
      <b>${pct(row.share)}</b>
    </div>
  `).join("");
}

function exportPurpose(name) {
  if (name.includes("forecasts")) return "Forecast capacity / day by zone";
  if (name.includes("utilization")) return "Zone utilization and inventory pressure";
  if (name.includes("allocations")) return "Backend allocation output";
  if (name.includes("alerts")) return "Flagged campaign alerts";
  if (name.includes("pacing")) return "Delivery monitoring";
  if (name.includes("campaigns")) return "Campaign universe";
  if (name.includes("priority")) return "Priority ranking";
  if (name.includes("feasibility")) return "Fulfillment feasibility";
  return "Pipeline input";
}

function confirmAllocation() {
  if (state.currentCampaign) {
    state.currentCampaign.status = "Allocation Confirmed";
    state.handoffStatus = "Allocation confirmed and ready for OneMedia handoff.";
    refreshCampaignOutputs();
  }
  const msg = document.getElementById("confirmMsg");
  if (msg) msg.textContent = "Allocation confirmed with selected zones and campaign saved.";
}

function createOneMediaHandoff() {
  if (!state.currentCampaign) return;
  state.handoffStatus = "OneMedia handoff staged for campaign setup and zone update review.";
  saveState();
  render();
}

function applyZoneSwapPlan() {
  if (!state.currentCampaign) return;
  const bestZones = state.recommendations.slice(0, 3).map(row => row.zone);
  state.currentCampaign.zones = bestZones;
  state.handoffStatus = `Zone swap staged: ${bestZones.join(", ")}.`;
  refreshCampaignOutputs();
  render();
}

function downloadReport() {
  const report = {
    campaign: state.currentCampaign,
    recommendations: state.recommendations,
    allocation: state.allocation,
    alerts: state.generatedAlerts,
    oneMediaHandoff: state.handoffStatus
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "recommendation_report.json";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadAllocationCsv() {
  const rows = state.currentCampaign
    ? state.allocation.map(r => ({
        zone: r.zone,
        allocation_pct: r.share.toFixed(2),
        allocated_impressions: r.allocated,
        forecast_capacity_per_day: r.forecast,
        status: r.status
      }))
    : DATA.allocations.slice(0, 200).map(r => ({
        zone: r.zone_name,
        allocation_pct: (Number(r.allocation_weight || 0) * 100).toFixed(2),
        allocated_impressions: r.allocated_impressions,
        forecast_capacity_per_day: r.zone_capacity,
        status: "Backend allocation"
      }));
  const headers = Object.keys(rows[0] || { zone: "", allocation_pct: "", allocated_impressions: "", forecast_capacity_per_day: "", status: "" });
  const csv = [headers.join(","), ...rows.map(row => headers.map(key => `"${String(row[key] ?? "").replaceAll('"', '""')}"`).join(","))].join("\\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "allocation_export.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function emptyState(crumb, title) {
  return `
    ${pageTitle(crumb, title)}
    <div class="notice">Create a campaign first. The zone recommendation, alerts, monitoring, and final recommendation output will appear here.</div>
    <button class="primary" onclick="go('Create Campaign')">Create Campaign</button>
  `;
}

function kpi(title, number, label) {
  return `<div class="panel kpi"><div class="panel-head">${title}</div><div class="num">${number}</div><div class="label">${label}</div></div>`;
}

function field(label, control) {
  return `<div class="field"><label>${label}</label>${control}</div>`;
}

render();
</script>
</body>
</html>
"""


def render_app() -> None:
    html = HTML.replace("__APP_DATA__", json.dumps(payload()))
    components.html(html, height=920, scrolling=False)


st.markdown(
    """
    <style>
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"] {
        display: none;
    }
    .block-container {
        padding: 0 !important;
        max-width: 100vw !important;
        width: 100vw !important;
    }
    section.main > div {
        padding: 0 !important;
    }
    iframe {
        display: block;
        width: 100vw !important;
        margin: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
render_app()
