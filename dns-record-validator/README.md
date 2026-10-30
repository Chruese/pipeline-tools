# DNS Record Validator

Ein CLI-Tool für CI/CD-Pipelines, das definierte DNS-Einträge (`A`, `AAAA`, `CNAME`, `TXT`, `PTR`) aus einer YAML-Datei liest und gegen interne oder öffentliche Nameserver verifiziert.

Ideal für Pre-Flight-Checks vor Firewall- oder Infrastruktur-Deployments sowie für Post-Deployment-Verifizierungen von Private DNS Zones.

## Features

- **Unterstützte Record-Typen:** Prüft `A`, `AAAA`, `CNAME`, `TXT`, `MX` sowie Reverse-Lookups (`PTR`).
- **Custom Nameserver:** Kann gezielt gegen interne Core-DNS-Server, Azure Private DNS Resolver oder öffentliche Resolver prüfen.
- **Fail-Fast:** Bricht die Pipeline mit Exit-Code `1` ab, falls ein Hostname nicht auflösbar ist (`NXDOMAIN`) oder auf eine falsche IP zeigt.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## YAML-Format (`dns-records.yaml`)

```yaml
records:
  - name: "api.intern.example.com"
    type: "A"
    expected: "10.20.1.15"

  - name: "portal.example.com"
    type: "CNAME"
    expected: "app-gateway.westeurope.cloudapp.azure.com"

  - name: "10.20.1.15"
    type: "PTR"
    expected: "api.intern.example.com"
```

## Verwendung

### Standard-Auflösung (System-Resolver)

```bash
python dns_validator.py -f ./dns-records.yaml
```

### Abfrage gegen spezifischen internen DNS-Server

```bash
python dns_validator.py -f ./dns-records.yaml --nameserver 10.100.0.4
```

### CLI-Parameter

- `-f`, `--file`: Pfad zur YAML-Datei mit den DNS-Regeln (Pflichtfeld)
- `-n`, `--nameserver`: IP-Adresse eines spezifischen DNS-Servers (optional)
- `-t`, `--timeout`: Timeout in Sekunden pro Abfrage (Standard: `5.0`)

## Exit-Codes

| Code | Beschreibung |
| :--- | :--- |
| `0` | Alle DNS-Records existieren und entsprechen den erwarteten Werten. |
| `1` | Mindestens ein DNS-Record weicht ab oder konnte nicht aufgelöst werden. |
| `2` | Konfigurations- oder Dateifehler (YAML ungültig). |

## Einbindung in GitHub Actions

```yaml
- name: Verify DNS Records
  run: |
    python tools/dns-record-validator/dns_validator.py \
      -f ./configs/expected-dns.yaml \
      --nameserver 10.0.0.4
```