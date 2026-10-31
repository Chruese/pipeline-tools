"""Interaktiver Assistent zum Erstellen valider YAML-Tickets."""

import re
from pathlib import Path
import yaml

def prompt_non_empty(prompt_text: str) -> str:
    while True:
        val = input(f"{prompt_text}: ").strip()
        if val:
            return val

def run_wizard(output_dir: Path) -> None:
    print("\n=== Jira Ticket -> Policy YAML Wizard ===")
    change_id = prompt_non_empty("Jira Change ID (z.B. CHG-2026-8941)").upper()
    env = prompt_non_empty("Environment (dev/stage/prod)").lower()
    requester = prompt_non_empty("Antragsteller E-Mail")
    expiry = prompt_non_empty("Ablaufdatum (YYYY-MM-DD)")

    print("\n--- Regel-Konfiguration ---")
    desc = prompt_non_empty("Zweck / Beschreibung")
    direction = prompt_non_empty("Richtung (ingress/egress)").lower()
    owning_unit = prompt_non_empty("Owning Subscription / Unit (z.B. sub-corebanking-prod)")

    src_app = prompt_non_empty("Source App Kürzel (z.B. payapi)")
    src_unit = prompt_non_empty("Source Unit (z.B. sub-payment-prod)")
    src_ips = [x.strip() for x in prompt_non_empty("Source IPs/CIDRs (kommagetrennt)").split(",")]

    dst_app = prompt_non_empty("Destination App Kürzel (z.B. coredb)")
    dst_unit = prompt_non_empty("Destination Unit (z.B. sub-corebanking-prod)")
    dst_ips = [x.strip() for x in prompt_non_empty("Destination IPs/CIDRs (kommagetrennt)").split(",")]

    proto = prompt_non_empty("Protokoll (tcp/udp)").lower()
    ports = [x.strip() for x in prompt_non_empty("Ports (z.B. 443 oder 80)").split(",")]

    rule_dict = {
        "rule_id": "01",
        "description": desc,
        "action": "allow",
        "direction": direction,
        "owning_unit": owning_unit,
        "source": {"app_short_name": src_app, "unit": src_unit, "cidrs": src_ips},
        "destination": {"app_short_name": dst_app, "unit": dst_unit, "cidrs": dst_ips},
        "services": [{"protocol": proto, "ports": ports}],
    }

    if "80" in ports or proto == "tcp" and any(p in ["22", "80", "1433"] for p in ports):
        print("\n[!] Genehmigungspflichtiger Port erkannt! SecOps-Freigabe erforderlich.")
        rule_dict["security_approval"] = {
            "secops_ticket": prompt_non_empty("SecOps Ticket (z.B. SEC-2026-102)"),
            "approved_by": prompt_non_empty("Genehmigt durch (E-Mail)"),
            "justification": prompt_non_empty("Begründung für Ausnahme"),
        }

    policy_payload = {
        "schema_version": "1.0",
        "change_id": change_id,
        "environment": env,
        "requested_by": requester,
        "expiry_date": expiry,
        "target_platforms": ["azure"],
        "rules": [rule_dict],
    }

    target_path = output_dir / env / owning_unit / f"{change_id}.yaml"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(policy_payload, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f"\n[OK] Ticket erfolgreich angelegt unter: {target_path}\n")