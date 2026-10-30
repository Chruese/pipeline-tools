#!/usr/bin/env python3
import sys
import argparse
import yaml
import dns.resolver
import dns.reversename
from typing import List, Dict, Any


def load_dns_config(file_path: str) -> List[Dict[str, Any]]:
    """Loads expected DNS records from a YAML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict) and "records" in data:
        return data["records"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("YAML must contain a list of entries or a 'records' key.")


def verify_record(
    fqdn: str,
    record_type: str,
    expected_values: List[str],
    resolver: dns.resolver.Resolver,
) -> tuple[bool, List[str], str]:
    """Verifies a single DNS record against the expected target values."""
    try:
        rtype = record_type.upper()
        if rtype == "PTR":
            query_name = dns.reversename.from_address(fqdn)
            answers = resolver.resolve(query_name, "PTR")
        else:
            answers = resolver.resolve(fqdn, rtype)

        actual_values = [r.to_text().strip(".") for r in answers]
        normalized_expected = [str(v).strip(".") for v in expected_values]

        missing = [val for val in normalized_expected if val not in actual_values]
        if missing:
            return False, actual_values, f"Expected: {normalized_expected}, Found: {actual_values}"

        return True, actual_values, "OK"

    except dns.resolver.NXDOMAIN:
        return False, [], "NXDOMAIN (Domain does not exist)"
    except dns.resolver.NoAnswer:
        return False, [], f"No answer for record type {record_type}"
    except dns.resolver.LifetimeTimeout:
        return False, [], "DNS timeout"
    except Exception as e:
        return False, [], f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(description="Validates DNS records from a YAML file against real nameservers.")
    parser.add_argument("-f", "--file", required=True, help="Path to the YAML file with DNS definitions")
    parser.add_argument("-n", "--nameserver", help="Optional DNS server (e.g. 10.0.0.4 or 8.8.8.8)")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Timeout per DNS query in seconds")

    args = parser.parse_args()

    try:
        records = load_dns_config(args.file)
    except Exception as e:
        print(f"[!] Error reading YAML file: {e}", file=sys.stderr)
        sys.exit(2)

    resolver = dns.resolver.Resolver()
    resolver.timeout = args.timeout
    resolver.lifetime = args.timeout

    if args.nameserver:
        resolver.nameservers = [args.nameserver]
        print(f"[*] Using custom nameserver: {args.nameserver}")

    print(f"[*] Checking {len(records)} DNS records...\n")

    failed_records = []

    for entry in records:
        fqdn = entry.get("name") or entry.get("fqdn")
        rtype = entry.get("type", "A").upper()
        expected = entry.get("expected") or entry.get("target") or entry.get("value")

        if not fqdn or not expected:
            print(f"[!] Skipping incomplete entry: {entry}", file=sys.stderr)
            continue

        expected_list = expected if isinstance(expected, list) else [str(expected)]

        print(f"[*] {fqdn} ({rtype}) -> {', '.join(expected_list)} ...", end=" ", flush=True)
        success, _, message = verify_record(fqdn, rtype, expected_list, resolver)

        if success:
            print("OK")
        else:
            print(f"FAILED ({message})")
            failed_records.append(f"{fqdn} [{rtype}]: {message}")

    if failed_records:
        print(f"\n[!] DNS VALIDATION FAILED ({len(failed_records)} errors):")
        for fail in failed_records:
            print(f"  - {fail}")
        sys.exit(1)

    print("\n[✓] All DNS records successfully resolved and verified.")
    sys.exit(0)


if __name__ == "__main__":
    main()