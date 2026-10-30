#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Any


def parse_terraform_plan(plan_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Wertet resource_changes und resource_drift aus einem Terraform JSON-Plan aus."""
    changes = {
        "create": [],
        "update": [],
        "delete": [],
        "replace": [],
    }

    # Kombiniere reguläre Plan-Abweichungen und explizite Resource-Drifts
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
    """Erstellt einen kompakten Markdown-Bericht für PRs, Issues oder Webhooks."""
    total = sum(len(v) for v in changes.values())
    if total == 0:
        return f"### ✅ Kein Terraform-Drift erkannt (`{project_name}`)\nAlle Ressourcen sind synchron mit dem State."

    lines = [
        f"### ⚠️ Terraform Drift erkannt: `{project_name}`",
        f"Es wurden **{total}** abweichende Ressourcen festgestellt:\n",
    ]

    labels = {
        "replace": "🔄 Ersetzen (Destroy & Recreate)",
        "delete": "❌ Löschen (Im Code entfernt / Manuell angelegt)",
        "update": "✏️ Ändern (Out-of-Band Modifikation)",
        "create": "➕ Erstellen (Manuell gelöscht / Neu im Code)",
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
    """Sendet den Bericht an einen MS Teams, Slack oder Discord Webhook."""
    payload = {
        "text": markdown_text,
        "title": f"Terraform Drift Report: {project_name}",
    }
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Analysiert Terraform JSON-Pläne auf Infrastruktur-Drifts.")
    parser.add_argument("-f", "--file", required=True, help="Pfad zur Terraform Plan JSON-Datei")
    parser.add_argument("-p", "--project", default=os.getenv("TF_PROJECT_NAME", "default-stack"), help="Projekt-/Stack-Name")
    parser.add_argument("-w", "--webhook", default=os.getenv("DRIFT_WEBHOOK_URL"), help="Optionaler Webhook (Teams/Slack)")
    parser.add_argument("-o", "--output", help="Optionaler Dateipfad für den Markdown-Report (z.B. drift-report.md)")
    parser.add_argument("--fail-on-drift", action="store_true", help="Beendet das Skript mit Exit-Code 1, falls Drift vorliegt")

    args = parser.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    except Exception as e:
        print(f"[!] Fehler beim Laden der JSON-Plan-Datei: {e}", file=sys.stderr)
        sys.exit(2)

    changes = parse_terraform_plan(plan_data)
    total_drifts = sum(len(v) for v in changes.values())
    report = build_markdown_report(changes, args.project)

    print(report)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as out_f:
                out_f.write(report)
            print(f"\n[*] Bericht gespeichert unter: {args.output}")
        except Exception as e:
            print(f"[!] Fehler beim Schreiben der Ausgabedatei: {e}", file=sys.stderr)
            sys.exit(2)

    if total_drifts > 0 and args.webhook:
        try:
            print("[*] Sende Drift-Alarm an Webhook...")
            send_webhook(args.webhook, report, args.project)
            print("[✓] Webhook erfolgreich zugestellt.")
        except requests.exceptions.RequestException as e:
            print(f"[!] Fehler beim Senden des Webhooks: {e}", file=sys.stderr)
            sys.exit(2)

    if total_drifts > 0 and args.fail_on_drift:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()