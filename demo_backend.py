from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Iterable
from functools import lru_cache
import os

import pandas as pd


DATA_DIR = Path(os.environ.get("PANASILLIES_DATA_DIR", Path(__file__).resolve().parent)).expanduser()


ZONE_PROFILES = {
    "Movies": {
        "keywords": {"movies", "film", "cinema", "entertainment"},
        "fit": 0.95,
        "reason": "High engagement in long-haul entertainment sessions.",
    },
    "TV": {
        "keywords": {"tv", "series", "show", "entertainment"},
        "fit": 0.88,
        "reason": "Strong repeat exposure across seatback browsing.",
    },
    "Audio": {
        "keywords": {"audio", "music", "podcast", "sound"},
        "fit": 0.79,
        "reason": "Useful for passive discovery and lower-cost reach.",
    },
    "Games": {
        "keywords": {"games", "game", "family", "interactive"},
        "fit": 0.84,
        "reason": "Good interaction depth for leisure and family segments.",
    },
    "Retail": {
        "keywords": {"retail", "shopping", "shop", "duty", "travel"},
        "fit": 0.81,
        "reason": "Commercial placement with measurable conversion intent.",
    },
}


ZONE_ENGINE_GROUPS = {
    "Movies": {
        "keywords": ("movie", "movies", "film", "cinema", "hbo", "a24"),
        "reason": "High available movie inventory and strong long-haul entertainment fit.",
    },
    "TV": {
        "keywords": ("tv", "show", "series"),
        "reason": "Strong seatback browsing match with reliable forecast capacity.",
    },
    "Audio": {
        "keywords": ("audio", "music", "podcast"),
        "reason": "Lower-utilization audio inventory can absorb incremental impressions.",
    },
    "Games": {
        "keywords": ("game", "games"),
        "reason": "Interactive inventory with strong leisure-session engagement.",
    },
    "Retail": {
        "keywords": ("retail", "shop", "shopping", "duty"),
        "reason": "Commerce-oriented placement with travel purchase intent.",
    },
}


@dataclass
class CampaignInput:
    campaign_name: str
    airline: str
    target_impressions: int
    budget: int
    start_date: date
    end_date: date
    categories: list[str]


def _read_csv(name: str, **kwargs) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def load_demo_data() -> dict[str, pd.DataFrame]:
    return {
        "data_dir": DATA_DIR,
        "campaigns": _read_csv("campaigns_cleaned.csv", parse_dates=["start_date", "end_date"]),
        "pacing": _read_csv("output_pacing.csv"),
        "alerts": _read_csv("output_alerts.csv"),
        "allocations": _read_csv("output_allocations.csv"),
        "forecasts": _read_csv("output_zone_forecasts.csv"),
        "feasibility": _read_csv("output_feasibility.csv"),
        "priority": _read_csv("output_priority_scores.csv"),
        "zone_utilization": _read_csv("output_zone_utilization.csv"),
    }


@lru_cache(maxsize=1)
def build_om_zone_candidates() -> list[dict]:
    """Build zone candidates with pipeline_OM.py Phase 3 scoring on precomputed Model 1 output."""
    campaigns = _read_csv("campaigns_cleaned.csv", parse_dates=["start_date", "end_date"])
    campaign_delivery = _read_csv("campaign_delivery.csv", parse_dates=["event_date"])
    forecasts = _read_csv("output_zone_forecasts.csv")

    if campaigns.empty or campaign_delivery.empty or forecasts.empty:
        return []

    zone_capacities = (
        forecasts.groupby("zone_name")["daily_capacity"]
        .sum()
        .to_dict()
    )

    today = pd.Timestamp.now().normalize()
    active = campaigns[
        (campaigns["start_date"] <= today)
        & (campaigns["end_date"] >= today)
    ]
    zone_competition = active.groupby("zone_name")["campaign_id"].nunique().reset_index()
    zone_competition.columns = ["zone_name", "active_campaigns"]

    recent = campaign_delivery[
        campaign_delivery["event_date"] >= today - pd.Timedelta(days=7)
    ]
    zone_recent = recent.groupby("zone_name")["served_impressions"].sum().reset_index()
    zone_recent["daily_actual"] = zone_recent["served_impressions"] / 7

    rows = []
    for zone_name, capacity in zone_capacities.items():
        if capacity <= 0:
            continue

        comp = zone_competition[zone_competition["zone_name"] == zone_name]
        active_campaigns = int(comp["active_campaigns"].values[0]) if len(comp) > 0 else 0
        available_capacity = capacity / max(active_campaigns + 1, 1)

        actual = zone_recent[zone_recent["zone_name"] == zone_name]
        daily_actual = float(actual["daily_actual"].values[0]) if len(actual) > 0 else 0.0
        zpr = daily_actual / capacity if capacity > 0 else 0.0
        zpr = max(min(zpr, 3.0), 0.01)

        category = "other"
        for candidate in ["home", "tv", "movies", "boarding", "map", "music", "games", "shopping", "welcome"]:
            if candidate in zone_name.lower():
                category = candidate
                break

        score = available_capacity * max(zpr, 0.1)

        rows.append(
            {
                "zone_name": zone_name,
                "daily_capacity": round(float(capacity)),
                "active_campaigns": active_campaigns,
                "available_capacity": round(float(available_capacity)),
                "zpr": round(float(zpr), 3),
                "category": category,
                "score": round(float(score), 2),
            }
        )

    return sorted(rows, key=lambda row: row["score"], reverse=True)


@lru_cache(maxsize=1)
def build_om_category_candidates() -> list[dict]:
    """Aggregate OM-scored concrete zones back into the five UI zone categories."""
    zone_candidates = build_om_zone_candidates()
    category_rows = []

    for category, config in ZONE_ENGINE_GROUPS.items():
        keywords = config["keywords"]
        matches = [
            row for row in zone_candidates
            if any(keyword in row["zone_name"].lower() for keyword in keywords)
        ]
        if not matches:
            matches = zone_candidates[:12]

        daily_capacity = sum(float(row["daily_capacity"]) for row in matches)
        available_capacity = sum(float(row["available_capacity"]) for row in matches)
        active_campaigns = sum(int(row["active_campaigns"]) for row in matches)
        score = sum(float(row["score"]) for row in matches)
        weighted_zpr = (
            sum(float(row["zpr"]) * float(row["available_capacity"]) for row in matches)
            / max(available_capacity, 1.0)
        )

        category_rows.append(
            {
                "zone_name": category,
                "daily_capacity": round(daily_capacity),
                "active_campaigns": active_campaigns,
                "available_capacity": round(available_capacity),
                "zpr": round(weighted_zpr, 3),
                "category": category.lower(),
                "score": round(score, 2),
                "source_zone_count": len(matches),
                "reason": config["reason"],
            }
        )

    return sorted(category_rows, key=lambda row: row["score"], reverse=True)


def build_zone_recommendation_stats(
    forecasts: pd.DataFrame,
    utilization: pd.DataFrame,
    allocations: pd.DataFrame,
) -> list[dict]:
    """Build backend-derived zone/category stats for the frontend recommendation engine."""
    rows = []
    for zone, config in ZONE_ENGINE_GROUPS.items():
        keywords = config["keywords"]
        forecast_matches = _match_keywords(forecasts, "zone_name", keywords)
        if forecast_matches.empty:
            forecast_matches = forecasts.nlargest(30, "daily_capacity").copy()

        utilization_matches = _match_keywords(utilization, "zone_name", keywords)
        allocation_matches = _match_keywords(allocations, "zone_name", keywords)

        capacity = float(forecast_matches["daily_capacity"].fillna(0).sum())
        active_campaigns = float(forecast_matches["active_campaigns_in_zone"].fillna(0).sum())
        avg_utilization = (
            float(utilization_matches["utilization_pct"].fillna(0).mean())
            if not utilization_matches.empty
            else 50.0
        )
        allocated = (
            float(allocation_matches["allocated_impressions"].fillna(0).sum())
            if not allocation_matches.empty
            else 0.0
        )
        row_count = int(len(forecast_matches))

        inventory_score = min(38.0, max(0.0, capacity) ** 0.18)
        utilization_score = max(0.0, 28.0 - avg_utilization / 4.0)
        competition_penalty = min(18.0, active_campaigns / max(row_count * 2.5, 1))
        base_score = max(50.0, min(96.0, 44 + inventory_score + utilization_score - competition_penalty))

        rows.append(
            {
                "zone": zone,
                "capacity": round(capacity),
                "active_campaigns": round(active_campaigns),
                "avg_utilization_pct": round(avg_utilization, 1),
                "allocated_impressions": round(allocated),
                "forecast_rows": row_count,
                "base_score": round(base_score, 1),
                "reason": config["reason"],
            }
        )
    return sorted(rows, key=lambda item: item["base_score"], reverse=True)


def _match_keywords(df: pd.DataFrame, column: str, keywords: tuple[str, ...]) -> pd.DataFrame:
    if df.empty or column not in df:
        return pd.DataFrame()
    mask = df[column].astype(str).str.lower().apply(lambda value: any(key in value for key in keywords))
    return df[mask].copy()


def dashboard_campaigns(data: dict[str, pd.DataFrame], created: Iterable[dict] | None = None) -> pd.DataFrame:
    pacing = data["pacing"].copy()
    if not pacing.empty:
        pacing = pacing[
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
            ]
        ]
        pacing["progress"] = pacing["delivery_pct"].clip(0, 100)

    created_rows = []
    for i, campaign in enumerate(created or [], start=9001):
        created_rows.append(
            {
                "campaign_id": i,
                "campaign_name": campaign["campaign_name"],
                "revenue_type": "paid",
                "planned": campaign["target_impressions"],
                "delivered": int(campaign["target_impressions"] * 0.02),
                "delivery_pct": 2.0,
                "pacing_ratio": 0.18,
                "status": "New - Allocation Ready",
                "severity": "WATCH",
                "progress": 2.0,
            }
        )

    if created_rows:
        pacing = pd.concat([pd.DataFrame(created_rows), pacing], ignore_index=True)
    return pacing


def dashboard_stats(campaigns: pd.DataFrame, alerts: pd.DataFrame, forecasts: pd.DataFrame) -> dict[str, str]:
    active = len(campaigns)
    critical = 0 if alerts.empty else int((alerts["severity"] == "CRITICAL").sum())
    avg_delivery = 0 if campaigns.empty else campaigns["delivery_pct"].mean()
    capacity = 0 if forecasts.empty else forecasts["daily_capacity"].sum()
    return {
        "Active Campaigns": f"{active}",
        "Flagged": f"{critical}",
        "Avg Delivery": f"{avg_delivery:.1f}%",
        "Daily Capacity": f"{capacity:,.0f}",
    }


def recommend_zones(campaign: CampaignInput, forecasts: pd.DataFrame) -> pd.DataFrame:
    selected = set(campaign.categories)
    rows = []
    for category, profile in ZONE_PROFILES.items():
        matching_forecasts = _matching_forecasts(category, forecasts)
        capacity = matching_forecasts["daily_capacity"].sum() if not matching_forecasts.empty else 0
        category_boost = 0.08 if category in selected else 0
        budget_boost = min(campaign.budget / 100000, 0.08)
        fit_score = min(profile["fit"] + category_boost + budget_boost, 0.99)
        expected = int(min(capacity * fit_score, campaign.target_impressions * (0.18 + fit_score / 3)))
        rows.append(
            {
                "recommended_zone": category,
                "fit_score": round(fit_score * 100, 1),
                "expected_impressions": max(expected, int(campaign.target_impressions * 0.08)),
                "predicted_performance": _performance_label(fit_score, capacity),
                "reason": profile["reason"],
            }
        )
    return pd.DataFrame(rows).sort_values("fit_score", ascending=False).reset_index(drop=True)


def forecast_allocation(campaign: CampaignInput, recommendations: pd.DataFrame) -> pd.DataFrame:
    if recommendations.empty:
        return pd.DataFrame()

    weights = recommendations["fit_score"] / recommendations["fit_score"].sum()
    allocation = recommendations[["recommended_zone", "fit_score", "expected_impressions"]].copy()
    allocation["allocated_impressions"] = (weights * campaign.target_impressions).round().astype(int)
    allocation["inventory_risk"] = allocation.apply(
        lambda row: "Low" if row["expected_impressions"] >= row["allocated_impressions"] else "Watch",
        axis=1,
    )
    allocation["match_status"] = allocation["inventory_risk"].map({"Low": "Matched", "Watch": "Needs pacing monitor"})
    return allocation


def generated_alerts(campaign: CampaignInput, allocation: pd.DataFrame) -> pd.DataFrame:
    alerts = []
    if allocation.empty:
        return pd.DataFrame(alerts)

    watch_rows = allocation[allocation["inventory_risk"] == "Watch"]
    if not watch_rows.empty:
        alerts.append(
            {
                "severity": "WATCH",
                "campaign": campaign.campaign_name,
                "alert": "Inventory risk in selected zones",
                "recommendation": "Shift 10-15% delivery to Movies or TV and re-run allocation.",
            }
        )

    days = max((campaign.end_date - campaign.start_date).days, 1)
    daily_goal = campaign.target_impressions / days
    if daily_goal > 75000:
        alerts.append(
            {
                "severity": "CRITICAL",
                "campaign": campaign.campaign_name,
                "alert": "Aggressive daily impression goal",
                "recommendation": "Extend flight dates or increase zone coverage before approval.",
            }
        )

    alerts.append(
        {
            "severity": "INFO",
            "campaign": campaign.campaign_name,
            "alert": "Zone recommendation generated",
            "recommendation": "Approve matched allocation and monitor pacing after launch.",
        }
    )
    return pd.DataFrame(alerts)


def pipeline_steps() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"step": "Campaign Input", "status": "Complete", "output": "Brief, budget, dates, zones"},
            {"step": "Forecast Model", "status": "Complete", "output": "Zone capacity prediction"},
            {"step": "Recommendation Logic", "status": "Complete", "output": "Ranked zone/category fit"},
            {"step": "Allocation", "status": "Complete", "output": "Daily impression allocation"},
            {"step": "Dashboard Output", "status": "Live", "output": "KPIs, alerts, pacing monitor"},
        ]
    )


def campaign_to_dict(campaign: CampaignInput) -> dict:
    row = asdict(campaign)
    row["start_date"] = campaign.start_date.isoformat()
    row["end_date"] = campaign.end_date.isoformat()
    return row


def campaign_from_dict(row: dict) -> CampaignInput:
    return CampaignInput(
        campaign_name=row["campaign_name"],
        airline=row["airline"],
        target_impressions=int(row["target_impressions"]),
        budget=int(row["budget"]),
        start_date=pd.to_datetime(row["start_date"]).date(),
        end_date=pd.to_datetime(row["end_date"]).date(),
        categories=list(row["categories"]),
    )


def _matching_forecasts(category: str, forecasts: pd.DataFrame) -> pd.DataFrame:
    if forecasts.empty or "zone_name" not in forecasts:
        return pd.DataFrame()

    keywords = ZONE_PROFILES[category]["keywords"]
    mask = forecasts["zone_name"].str.lower().apply(lambda value: any(key in value for key in keywords))
    matched = forecasts[mask]
    if matched.empty:
        return forecasts.nlargest(12, "daily_capacity")
    return matched.nlargest(12, "daily_capacity")


def _performance_label(fit_score: float, capacity: float) -> str:
    if fit_score >= 0.93 and capacity > 10000:
        return "High"
    if fit_score >= 0.84:
        return "Medium-High"
    return "Medium"
