"""
Check Point SmartCenter / MDS Compiler
--------------------------------------
Erzeugt aus den neutralen YAML-Tickets ein strukturiertes JSON-Payload
für Terraform (checkpoint Provider) oder Ansible (check_point.mgmt).

Besonderheiten für Check Point (Brownfield & Objekt-Zwang):
1. Automatische Zerlegung von CIDRs in Check Point 'hosts' (/32) und 'networks' (< /32).
2. Automatische Erstellung deduplizierter Service-Objekte (svc-tcp-xxx / svc-udp-xxx).
3. Platzierung aller Regeln unterhalb einer festen Section ('GITOPS-AUTOMATED-RULES'),
   damit manuelle Bestandsregeln auf der Perimeter-Firewall unberührt bleiben.
"""

import ipaddress
from typing import Dict, List, Tuple

from ..models import RuleSpec, TicketPolicy
from .azure import generate_rule_name


def _cidr_to_cp_object(cidr: str) -> Tuple[str, str, dict]:
    """
    Wandelt ein CIDR in ein deterministisches Check Point Objekt um.
    Gibt (obj_type, obj_name, obj_payload) zurück.
    obj_type ist entweder 'host' (/32) oder 'network' (Subnetz).
    """
    net = ipaddress.ip_network(cidr, strict=False)
    if net.prefixlen == 32:
        ip_str = str(net.network_address)
        obj_name = f"h-gitops-{ip_str}"
        return "host", obj_name, {
            "name": obj_name,
            "ipv4_address": ip_str,
            "comments": "Managed by GitOps Firewall Orchestrator",
        }
    else:
        net_str = str(net.network_address)
        obj_name = f"n-gitops-{net_str}-{net.prefixlen}"
        return "network", obj_name, {
            "name": obj_name,
            "subnet4": net_str,
            "mask_length4": net.prefixlen,
            "comments": "Managed by GitOps Firewall Orchestrator",
        }


def _service_to_cp_object(protocol: str, port: str) -> Tuple[str, str, dict]:
    """
    Wandelt ein Protokoll/Port-Paar in ein Check Point Service-Objekt um.
    Gibt (proto_type, svc_name, svc_payload) zurück.
    """
    proto_clean = protocol.lower()
    port_clean = port.replace("-", "to")
    svc_name = f"svc-gitops-{proto_clean}-{port_clean}"

    return proto_clean, svc_name, {
        "name": svc_name,
        "port": port,
        "protocol": proto_clean.upper(),
        "comments": "Managed by GitOps Firewall Orchestrator",
    }


def build_checkpoint_payload(
    tickets: List[TicketPolicy],
    registry_units: dict,
    env: str,
) -> dict:
    """
    Kompiliert alle Tickets mit target_platforms=['checkpoint'] in ein
    idempotentes JSON-Artefakt für Check Point.
    """
    hosts: Dict[str, dict] = {}
    networks: Dict[str, dict] = {}
    tcp_services: Dict[str, dict] = {}
    udp_services: Dict[str, dict] = {}
    access_rules: List[dict] = []

    section_name = f"GITOPS-AUTOMATED-{env.upper()}"
    layer_name = f"Network"  # Alternativ eigener Inline-Layer, z.B. "GitOps-Inline-Layer"

    for ticket in tickets:
        if "checkpoint" not in ticket.target_platforms:
            continue

        for rule in ticket.rules:
            unit_cfg = registry_units[rule.owning_unit]
            strict_name = generate_rule_name(ticket.change_id, rule)

            # 1. Quell-CIDRs in Check Point Host-/Network-Objekte auflösen
            src_object_names: List[str] = []
            for cidr in rule.source.cidrs:
                obj_type, obj_name, obj_data = _cidr_to_cp_object(cidr)
                src_object_names.append(obj_name)
                if obj_type == "host":
                    hosts[obj_name] = obj_data
                else:
                    networks[obj_name] = obj_data

            # 2. Ziel-CIDRs in Check Point Host-/Network-Objekte auflösen
            dst_object_names: List[str] = []
            for cidr in rule.destination.cidrs:
                obj_type, obj_name, obj_data = _cidr_to_cp_object(cidr)
                dst_object_names.append(obj_name)
                if obj_type == "host":
                    hosts[obj_name] = obj_data
                else:
                    networks[obj_name] = obj_data

            # 3. Services in Check Point Service-Objekte auflösen
            svc_object_names: List[str] = []
            for svc in rule.services:
                if svc.protocol == "icmp":
                    svc_object_names.append("icmp-requests")
                    continue
                for port in svc.ports:
                    proto_type, svc_name, svc_data = _service_to_cp_object(svc.protocol, port)
                    svc_object_names.append(svc_name)
                    if proto_type == "tcp":
                        tcp_services[svc_name] = svc_data
                    elif proto_type == "udp":
                        udp_services[svc_name] = svc_data

            # 4. DORA-Audit-Kommentar zusammenbauen
            sec_tag = (
                f" | SEC-APPROVAL: {rule.security_approval.secops_ticket}"
                if rule.security_approval
                else ""
            )
            audit_comment = (
                f"[{ticket.change_id}] Unit:{rule.owning_unit} | "
                f"Req:{ticket.requested_by} | Exp:{ticket.expiry_date}{sec_tag} | "
                f"{rule.description}"
            )[:250]

            # 5. Sortier-Gewicht aus der Registry holen, damit Regeln deterministisch geordnet sind
            base_prio = (
                unit_cfg["rc_priority_ingress"]
                if rule.direction == "ingress"
                else unit_cfg["rc_priority_egress"]
            )

            access_rules.append({
                "name": strict_name,
                "layer": layer_name,
                "section": section_name,
                "sort_weight": base_prio,
                "action": "Accept" if rule.action == "allow" else "Drop",
                "source": src_object_names,
                "destination": dst_object_names,
                "service": svc_object_names,
                "track": "Log",
                "enabled": True,
                "comments": audit_comment,
                "custom_fields": {
                    "change_id": ticket.change_id,
                    "expiry_date": ticket.expiry_date.isoformat(),
                    "owning_unit": rule.owning_unit,
                },
            })

    # Sortiere Regeln deterministisch nach Unit-Priorität und Regelname
    sorted_rules = sorted(access_rules, key=lambda r: (r["sort_weight"], r["name"]))

    # Berechne für Check Point die sequenzielle Verkettung innerhalb der GitOps-Section:
    # Regel 1 liegt direkt unter dem Section-Header, Regel 2 unter Regel 1 usw.
    for idx, r in enumerate(sorted_rules):
        if idx == 0:
            r["position"] = {"below": section_name}
        else:
            r["position"] = {"below": sorted_rules[idx - 1]["name"]}

    return {
        "environment": env,
        "target_layer": layer_name,
        "automation_section": section_name,
        "objects": {
            "hosts": list( sorted(hosts.values(), key=lambda x: x["name"]) ),
            "networks": list( sorted(networks.values(), key=lambda x: x["name"]) ),
            "tcp_services": list( sorted(tcp_services.values(), key=lambda x: x["name"]) ),
            "udp_services": list( sorted(udp_services.values(), key=lambda x: x["name"]) ),
        },
        "access_rules": sorted_rules,
    }