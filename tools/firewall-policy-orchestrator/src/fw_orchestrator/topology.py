import ipaddress
from typing import List

def verify_cidrs_against_registry(unit_name: str, cidrs: List[str], registry_units: dict) -> None:
    if unit_name not in registry_units:
        raise ValueError(f"Unbekannte Subscription/Unit '{unit_name}' in topology_registry.yaml.")
    
    allowed = [ipaddress.ip_network(c) for c in registry_units[unit_name].get("allowed_cidrs", [])]
    for cidr in cidrs:
        net = ipaddress.ip_network(cidr, strict=False)
        if not any(net.subnet_of(a) for a in allowed):
            raise ValueError(
                f"CIDR '{cidr}' ist für Unit '{unit_name}' nicht zulässig! "
                f"Erlaubt laut Registry: {[str(a) for a in allowed]}"
            )