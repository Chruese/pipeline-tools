#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Any


def parse_terraform_plan(plan_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Analyzes resource_changes and resource_drift from a Terraform JSON plan."""
    changes = {
        "create": [],
        "update": [],
        "delete": [],
        "replace": [],
    }

    # Combine regular plan changes and explicit resource drifts
    resource_items = plan_data.get("resource_changes", []) + plan_data.get("resource_drift", [])
    seen_addresses = set()

    for res in resource_items:
        address = res.get("address")
        if not address or address in seen_addresses:
            continue

        actions = res.get("change", {}).get("actions", [])

        if actions == ["no-op"] or actions == ["read"]:
            continue

        seen_addresses.add(address)

        if "create" in actions and "delete" in actions:
            changes["replace"].append(address)
        elif "create" in actions:
            changes["create"].append(address)
        elif "delete" in actions:
            changes["delete"].append(address)
        elif "update" in actions:
            changes["update"].append(address)

    return changes


def build_markdown_report(changes: Dict[str, List[str]], project_name: str) -> str:
    """Generates a compact Markdown report for PRs, issues, or webhooks."""
    total = sum(len(v) for v in changes.values())
    if total == 0:
        return f"### ✅ No Terraform drift detected (`{project_name}`)\nAll resources are in sync with the state."

    lines = [
        f"### ⚠️ Terraform Drift Detected: `{project_name}`",
        f"Found **{total}** deviating resources:\n",
    ]

    labels = {
        "replace": "🔄 Replace (Destroy & Recreate)",
        "delete": "❌ Delete (Removed from code / Manually created)",
        "update": "✏️ Update (Out-of-band modification)",
        "create": "➕ Create (Manually deleted / New in code)",
    }

    for key in ["replace", "delete", "update", "create"]:
        items = changes[key]
        if items:
            lines.append(f"**{labels[key]} ({len(items)}):**")
            for addr in sorted(items):
                lines.append(f"- `{addr}`")
            lines.append("")

    return "\n".join(lines)


def send_webhook(webhook_url: str, markdown_text: str, project_name: str) -> None:
    """Sends the report to an MS Teams, Slack, or Discord webhook."""
    payload = {
        "text": markdown_text,
        "title": f"Terraform Drift Report: {project_name}",
    }
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Analyzes Terraform JSON plans for infrastructure drifts.")
    parser.add_argument("-f", "--file", required=True, help="Path to the Terraform plan JSON file")
    parser.add_argument("-p", "--project", default=os.getenv("TF_PROJECT_NAME", "default-stack"), help="Project/Stack name")
    parser.add_argument("-w", "--webhook", default=os.getenv("DRIFT_WEBHOOK_URL"), help="Optional webhook URL (Teams/Slack)")
    parser.add_argument("-o", "--output", help="Optional output file path for the markdown report (e.g. drift-report.md)")
    parser.add_argument("--fail-on-drift", action="store_true", help="Exits with code 1 if any drift is detected")

    args = parser.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    except Exception as e:
        print(f"[!] Error loading JSON plan file: {e}", file=sys.stderr)
        sys.exit(2)

    changes = parse_terraform_plan(plan_data)
    total_drifts = sum(len(v) for v in changes.values())
    report = build_markdown_report(changes, args.project)

    print(report)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as out_f:
                out_f.write(report)
            print(f"\n[*] Report saved to: {args.output}")
        except Exception as e:
            print(f"[!] Error writing output file: {e}", file=sys.stderr)
            sys.exit(2)

    if total_drifts > 0 and args.webhook:
        try:
            print("[*] Sending drift alert to webhook...")
            send_webhook(args.webhook, report, args.project)
            print("[✓] Webhook successfully delivered.")
        except requests.exceptions.RequestException as e:
            print(f"[!] Error sending webhook: {e}", file=sys.stderr)
            sys.exit(2)

    if total_drifts > 0 and args.fail_on_drift:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()