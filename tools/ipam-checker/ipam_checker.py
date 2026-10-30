#!/usr/bin/env python3
import os
import sys
import argparse
import ipaddress
import yaml
import requests
from typing import Set, Any


def extract_ips_from_yaml(data: Any) -> Set[str]:
    """Recursively searches for valid IPv4/IPv6 addresses or CIDRs in the YAML structure."""
    found_ips = set()

    if isinstance(data, dict):
        for value in data.values():
            found_ips.update(extract_ips_from_yaml(value))
    elif isinstance(data, list):
        for item in data:
            found_ips.update(extract_ips_from_yaml(item))
    elif isinstance(data, str):
        candidate = data.strip()
        try:
            ipaddress.ip_network(candidate, strict=False)
            found_ips.add(candidate)
        except ValueError:
            pass

    return found_ips


def check_netbox(ip_str: str, base_url: str, token: str, verify_ssl: bool = True) -> bool:
    """Checks IP or subnet against the NetBox REST API."""
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    net = ipaddress.ip_network(ip_str, strict=False)
    is_subnet = "/" in ip_str and net.num_addresses > 1

    if is_subnet:
        endpoint = f"{base_url.rstrip('/')}/api/ipam/prefixes/"
        params = {"prefix": str(net)}
    else:
        endpoint = f"{base_url.rstrip('/')}/api/ipam/ip-addresses/"
        params = {"address": str(net.network_address)}

    response = requests.get(endpoint, headers=headers, params=params, timeout=10, verify=verify_ssl)
    response.raise_for_status()
    data = response.json()
    return data.get("count", 0) > 0


def check_efficientip(ip_str: str, base_url: str, user: str, password: str, verify_ssl: bool = True) -> bool:
    """Checks IP or subnet against the EfficientIP SOLIDserver REST API."""
    headers = {
        "X-IPM-Username": user,
        "X-IPM-Password": password,
        "Accept": "application/json",
    }
    net = ipaddress.ip_network(ip_str, strict=False)
    is_subnet = "/" in ip_str and net.num_addresses > 1

    if is_subnet:
        endpoint = f"{base_url.rstrip('/')}/rest/ip_block_subnet_list"
        params = {"WHERE": f"start_hostaddr='{net.network_address}' AND subnet_size='{net.num_addresses}'"}
    else:
        endpoint = f"{base_url.rstrip('/')}/rest/ip_address_list"
        params = {"WHERE": f"hostaddr='{net.network_address}'"}

    response = requests.get(
        endpoint,
        headers=headers,
        params=params,
        auth=(user, password),
        timeout=10,
        verify=verify_ssl,
    )

    if response.status_code == 204:
        return False

    response.raise_for_status()
    data = response.json()
    return isinstance(data, list) and len(data) > 0


def main():
    parser = argparse.ArgumentParser(description="Validates IPs from YAML files against NetBox or EfficientIP.")
    parser.add_argument("-f", "--file", required=True, help="Path to the YAML file")
    parser.add_argument(
        "-p", "--provider",
        choices=["netbox", "efficientip"],
        default=os.getenv("IPAM_PROVIDER", "netbox"),
        help="IPAM Provider: 'netbox' or 'efficientip' (ENV: IPAM_PROVIDER)",
    )
    parser.add_argument("--url", default=os.getenv("IPAM_URL"), help="IPAM base URL (ENV: IPAM_URL)")
    parser.add_argument("--token", default=os.getenv("IPAM_TOKEN"), help="NetBox API token (ENV: IPAM_TOKEN)")
    parser.add_argument("--user", default=os.getenv("IPAM_USER"), help="EfficientIP username (ENV: IPAM_USER)")
    parser.add_argument("--password", default=os.getenv("IPAM_PASSWORD"), help="EfficientIP password (ENV: IPAM_PASSWORD)")
    parser.add_argument("--insecure", action="store_true", help="Disable SSL certificate verification")

    args = parser.parse_args()
    verify_ssl = not args.insecure

    if not verify_ssl:
        requests.packages.urllib3.disable_warnings()

    if not args.url:
        print("[!] Error: IPAM_URL (--url) must be provided.", file=sys.stderr)
        sys.exit(2)

    if args.provider == "netbox" and not args.token:
        print("[!] Error: NetBox requires IPAM_TOKEN (--token).", file=sys.stderr)
        sys.exit(2)

    if args.provider == "efficientip" and (not args.user or not args.password):
        print("[!] Error: EfficientIP requires IPAM_USER and IPAM_PASSWORD.", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)
    except Exception as e:
        print(f"[!] Error reading YAML file: {e}", file=sys.stderr)
        sys.exit(2)

    ips_to_check = extract_ips_from_yaml(yaml_content)
    if not ips_to_check:
        print("[+] No IP addresses found in the YAML file.")
        sys.exit(0)

    print(f"[*] Provider: {args.provider.upper()} | Found entries: {len(ips_to_check)}")

    missing_ips = []
    for ip in sorted(ips_to_check):
        print(f"[*] Checking {ip} ...", end=" ", flush=True)
        try:
            if args.provider == "netbox":
                exists = check_netbox(ip, args.url, args.token, verify_ssl)
            else:
                exists = check_efficientip(ip, args.url, args.user, args.password, verify_ssl)

            if exists:
                print("OK")
            else:
                print("MISSING")
                missing_ips.append(ip)
        except requests.exceptions.RequestException as e:
            print(f"API-ERROR ({e})")
            sys.exit(2)

    if missing_ips:
        print(f"\n[!] VALIDATION FAILED ({len(missing_ips)} not found in IPAM):")
        for ip in missing_ips:
            print(f"  - {ip}")
        sys.exit(1)

    print("\n[✓] All entries successfully verified in IPAM.")
    sys.exit(0)


if __name__ == "__main__":
    main()