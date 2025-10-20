from __future__ import annotations
import argparse
import os
import json
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import matplotlib.pyplot as plt

from utils import localize_series_to_tz

def load_config(path: str | None) -> dict:
    if path and os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    # defaults
    return {
        "timestamp_col": "timestamp",
        "merchant_id_col": "merchant_id",
        "comment_col": "comment",
        "issue_status_col": "issue_status",
        "issue_id_col": "issue_id",
        "resolution_timestamp_col": "resolved_at",
        "live_status_col": "live_status",
        "live_timestamp_col": "live_at",
        "actor_type_col": "actor_type",
    }

def safe_col(df: pd.DataFrame, key: str | None) -> str | None:
    if key and key in df.columns:
        return key
    return None

def compute_core_metrics(df: pd.DataFrame, cols: dict, tz_name: str) -> dict:
    ts_col = safe_col(df, cols.get("timestamp_col"))
    live_status_col = safe_col(df, cols.get("live_status_col"))
    issue_status_col = safe_col(df, cols.get("issue_status_col"))
    merchant_col = safe_col(df, cols.get("merchant_id_col"))

    out = {
        "late_night_interaction_count_20_06": None,
        "issues_reported": None,
        "issues_resolved": None,
        "merchants_went_live": None
    }

    if ts_col:
        ts = localize_series_to_tz(df[ts_col], tz_name)
        hours = ts.dt.hour
        # Late night window: 20:00–23:59 OR 00:00–06:00
        mask = (hours >= 20) | (hours < 6)
        out["late_night_interaction_count_20_06"] = int(mask.sum())

    if issue_status_col:
        # Basic count
        out["issues_reported"] = int((df[issue_status_col].astype(str).str.lower() == "reported").sum())
        out["issues_resolved"] = int((df[issue_status_col].astype(str).str.lower() == "resolved").sum())

    if live_status_col:
        out["merchants_went_live"] = int((df[live_status_col].astype(str).str.lower() == "live").sum())
        # Optionally deduplicate by merchant if you prefer unique merchants_went_live
        if merchant_col:
            uniq_live = df.loc[df[live_status_col].astype(str).str.lower() == "live", merchant_col].dropna().nunique()
            out["unique_merchants_went_live"] = int(uniq_live)

    return out

def compute_additional_metrics(df: pd.DataFrame, cols: dict, tz_name: str) -> dict:
    ts_col = safe_col(df, cols.get("timestamp_col"))
    issue_status_col = safe_col(df, cols.get("issue_status_col"))
    merchant_col = safe_col(df, cols.get("merchant_id_col"))

    add = {}
    if ts_col:
        ts = localize_series_to_tz(df[ts_col], tz_name)
        # Peak hour
        per_hour = ts.dt.hour.value_counts().sort_index()
        add["peak_hour"] = int(per_hour.idxmax()) if not per_hour.empty else None

        # Weekday vs weekend
        weekday = ts.dt.dayofweek  # Mon=0..Sun=6
        weekend_mask = weekday >= 5
        add["weekend_interaction_count"] = int(weekend_mask.sum())
        add["weekday_interaction_count"] = int((~weekend_mask).sum())

        # Weekly trend
        weekly = ts.dt.to_period("W").value_counts().sort_index()
        add["weekly_counts"] = {str(k): int(v) for k, v in weekly.items()}

    if issue_status_col:
        # Open issues = not resolved if such value exists
        val = df[issue_status_col].astype(str).str.lower()
        add["open_issues"] = int((val == "open").sum())

    if merchant_col:
        add["active_merchants"] = int(df[merchant_col].dropna().nunique())

    return add

def render_charts(df: pd.DataFrame, cols: dict, tz_name: str, out_dir: Path) -> list[str]:
    ts_col = safe_col(df, cols.get("timestamp_col"))
    saved = []
    if ts_col:
        ts = localize_series_to_tz(df[ts_col], tz_name)

        # 1) Interactions by hour
        per_hour = ts.dt.hour.value_counts().sort_index()
        plt.figure()
        per_hour.sort_index().plot(kind="bar")
        plt.title("Interactions by Hour")
        plt.xlabel("Hour of Day (0-23)")
        plt.ylabel("Count")
        p1 = out_dir / "charts" / "interactions_by_hour.png"
        p1.parent.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        plt.savefig(p1)
        plt.close()
        saved.append(str(p1))

        # 2) Weekly trend
        weekly = ts.dt.to_period("W").value_counts().sort_index()
        if not weekly.empty:
            plt.figure()
            weekly.index = weekly.index.astype(str)
            weekly.plot(kind="line", marker="o")
            plt.title("Weekly Interaction Trend")
            plt.xlabel("Week")
            plt.ylabel("Count")
            p2 = out_dir / "charts" / "weekly_trend.png"
            plt.tight_layout()
            plt.savefig(p2)
            plt.close()
            saved.append(str(p2))

    # 3) Issues pie if present
    issue_status_col = safe_col(df, cols.get("issue_status_col"))
    if issue_status_col:
        counts = (
            df[issue_status_col]
            .astype(str)
            .str.lower()
            .value_counts()
            .reindex(["reported", "resolved", "open"], fill_value=0)
        )
        plt.figure()
        counts.plot(kind="pie", autopct="%1.1f%%")
        plt.title("Issues Breakdown")
        p3 = out_dir / "charts" / "issues_breakdown.png"
        plt.tight_layout()
        plt.savefig(p3)
        plt.close()
        saved.append(str(p3))

    return saved

def main():
    ap = argparse.ArgumentParser(description="Generate comments operational report")
    ap.add_argument("--csv", required=True, help="Path to CSV file")
    ap.add_argument("--config", default="config.yaml", help="Path to column mapping YAML")
    ap.add_argument("--tz", default="Asia/Dhaka", help="IANA timezone (default: Asia/Dhaka)")
    ap.add_argument("--out", default="./out", help="Output directory")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load config + data
    cfg = load_config(args.config)
    df = pd.read_csv(args.csv)

    # Compute metrics
    core = compute_core_metrics(df, cfg, args.tz)
    add = compute_additional_metrics(df, cfg, args.tz)

    # Charts
    charts = render_charts(df, cfg, args.tz, out_dir)

    # Save JSON
    metrics = {"core": core, "additional": add, "charts": charts}
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Save Markdown summary
    md_lines = [
        "# Comments Operational Report",
        "",
        "## Core Metrics",
        f"- Late night interactions (20:00–06:00): **{core.get('late_night_interaction_count_20_06')}**",
        f"- Issues reported: **{core.get('issues_reported')}**",
        f"- Issues resolved: **{core.get('issues_resolved')}**",
        f"- Merchants went live (rows): **{core.get('merchants_went_live')}**",
    ]
    if "unique_merchants_went_live" in core:
        md_lines.append(f"- Unique merchants went live: **{core.get('unique_merchants_went_live')}**")

    md_lines.extend([
        "",
        "## Additional Metrics",
        f"- Peak hour: **{add.get('peak_hour')}**",
        f"- Weekend interactions: **{add.get('weekend_interaction_count')}**",
        f"- Weekday interactions: **{add.get('weekday_interaction_count')}**",
        f"- Open issues: **{add.get('open_issues')}**",
        f"- Active merchants: **{add.get('active_merchants')}**",
        "",
        "## Weekly Counts",
    ])
    for k, v in (add.get("weekly_counts") or {}).items():
        md_lines.append(f"- {k}: {v}")

    if charts:
        md_lines.extend(["", "## Charts"])
        for ch in charts:
            md_lines.append(f"- {ch}")

    (out_dir / "metrics.md").write_text("\n".join(md_lines))

    print(f"Wrote {out_dir/'metrics.json'} and {out_dir/'metrics.md'}")
    if charts:
        print("Charts:")
        for ch in charts:
            print("-", ch)

if __name__ == "__main__":
    main()
