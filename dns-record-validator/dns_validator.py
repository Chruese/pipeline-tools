#!/usr/bin/env python3
import sys
import argparse
import yaml
import dns.resolver
import dns.reversename
from typing import List, Dict, Any


def load_dns_config(file_path: str) -> List[Dict[str, Any]]:
    """Lädt die erwarteten DNS-Einträge aus einer YAML-Datei."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict) and "records" in data:
        return data["records"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("YAML muss eine Liste von Einträgen oder einen 'records'-Schlüssel enthalten.")


def verify_record(
    fqdn: str,
    record_type: str,
    expected_values: List[str],
    resolver: dns.resolver.Resolver,
) -> tuple[bool, List[str], str]:
    """Prüft einen einzelnen DNS-Record gegen die erwarteten Zielwerte."""
    try:
        rtype = record_type.upper()
        if rtype == "PTR":
            query_name = dns.reversename.from_address(fqdn)
            answers = resolver.resolve(query_name, "PTR")
        else:
            answers = resolver.resolve(fqdn, rtype)

        actual_values = [r.to_text().strip(".") for r in answers]
        normalized_expected = [ str(v).strip(".") for v in expected_values ]

        missing = [val for val in normalized_expected if val not in actual_values]
        if missing:
            return False, actual_values, f"Erwartet: {normalized_expected}, Gefunden: {actual_values}"

        return True, actual_values, "OK"

    except dns.resolver.NXDOMAIN:
        return False, [], "NXDOMAIN (Domain existiert nicht)"
    except dns.resolver.NoAnswer:
        return False, [], f"Keine Antwort für Typ {record_type}"
    except dns.resolver.LifetimeTimeout:
        return False, [], "DNS-Timeout"
    except Exception as e:
        return False, [], f"Fehler: {e}"


def main():
    parser = argparse.ArgumentParser(description="Validiert DNS-Records aus einer YAML-Datei gegen reale Nameserver.")
    parser.add_argument("-f", "--file", required=True, help="Pfad zur YAML-Datei mit den DNS-Definitionen")
    parser.add_argument("-n", "--nameserver", help="Optionaler DNS-Server (z. B. 10.0.0.4 oder 8.8.8.8)")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Timeout pro DNS-Abfrage in Sekunden")

    args = parser.parse_args()

    try:
        records = load_dns_config(args.file)
    except Exception as e:
        print(f"[!] Fehler beim Lesen der YAML-Datei: {e}", file=sys.stderr)
        sys.exit(2)

    resolver = dns.resolver.Resolver()
    resolver.timeout = args.timeout
    resolver.lifetime = args.timeout

    if args.nameserver:
        resolver.nameservers = [args.nameserver]
        print(f"[*] Verwende benutzerdefinierten Nameserver: {args.nameserver}")

    print(f"[*] Prüfe {len(records)} DNS-Einträge...\n")

    failed_records = []

    for entry in records:
        fqdn = entry.get("name") or entry.get("fqdn")
        rtype = entry.get("type", "A").upper()
        expected = entry.get("expected") or entry.get("target") or entry.get("value")

        if not fqdn or not expected:
            print(f"[!] Überspringe unvollständigen Eintrag: {entry}", file=sys.stderr)
            continue

        expected_list = expected if isinstance(expected, list) else [str(expected)]

        print(f"[*] {fqdn} ({rtype}) -> {', '.join(expected_list)} ...", end=" ", flush=True)
        success, _, message = verify_record(fqdn, rtype, expected_list, resolver)

        if success:
            print("OK")
        else:
            print(f"FEHLER ({message})")
            failed_records.append(f"{fqdn} [{rtype}]: {message}")

    if failed_records:
        print(f"\n[!] DNS-VALIDIERUNG FEHLGESCHLAGEN ({len(failed_records)} Fehler):")
        for fail in failed_records:
            print(f"  - {fail}")
        sys.exit(1)

    print("\n[✓] Alle DNS-Einträge wurden erfolgreich aufgelöst und verifiziert.")
    sys.exit(0)


if __name__ == "__main__":
    main()