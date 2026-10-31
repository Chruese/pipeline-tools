import re
from typing import Dict, List
from ..models import RuleSpec, TicketPolicy

def generate_rule_name(change_id: str, rule: RuleSpec) -> str:
    chg_num = change_id.split("-")[-1]
    svc = rule.services[0]
    port_str = svc.ports[0].replace("-", "to")
    raw = f"chg-{chg_num}-{rule.rule_id}-{rule.source.app_short_name}-to-{rule.destination.app_short_name}-{svc.protocol}{port_str}"
    return re.sub(r"[^a-z0-9\-]", "", raw.lower())[:60]

def build_azure_rcg(tickets: List[TicketPolicy], registry_units: dict, env: str) -> dict:
    azure_collections: Dict[str, dict] = {}

    for ticket in tickets:
        if "azure" not in ticket.target_platforms:
            continue
        for rule in rule_list := ticket.rules:
            unit_cfg = registry_units[rule.owning_unit]
            dir_short = "in" if rule.direction == "ingress" else "out"
            rc_name = f"rc-{unit_cfg['short_code']}-{dir_short}"
            rc_prio = unit_cfg["rc_priority_ingress"] if rule.direction == "ingress" else unit_cfg["rc_priority_egress"]

            if rc_name not in azure_collections:
                azure_collections[rc_name] = {
                    "name": rc_name,
                    "priority": rc_prio,
                    "action": "Allow" if rule.action == "allow" else "Deny",
                    "owning_subscription": rule.owning_unit,
                    "rules": [],
                }

            rule_name = generate_rule_name(ticket.change_id, rule)
            sec_info = f" | SEC-APPROVAL: {rule.security_approval.secops_ticket}" if rule.security_approval else ""
            desc = f"[{ticket.change_id}] Sub:{rule.owning_unit} | Exp:{ticket.expiry_date}{sec_info} | {rule.description}"[:250]

            for idx, svc in enumerate(rule.services):
                azure_collections[rc_name]["rules"].append({
                    "name": rule_name if idx == 0 else f"{rule_name}-{idx+1}",
                    "description": desc,
                    "protocols": [svc.protocol.upper()],
                    "source_addresses": rule.source.cidrs,
                    "destination_addresses": rule.destination.cidrs,
                    "destination_ports": svc.ports,
                })

    sorted_rcs = sorted(azure_collections.values(), key=lambda x: x["priority"])
    return {
        "environment": env,
        "rcg_name": f"rcg-gitops-{env}-01",
        "rcg_priority": 2000,
        "network_rule_collections": sorted_rcs,
    }