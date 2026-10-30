# IPAM YAML Validator

Ein leichtgewichtiges CLI-Tool für CI/CD-Pipelines, das IP-Adressen und Subnetze aus deklarativen YAML-Dateien (z. B. Firewall- oder NSG-Regeln) extrahiert und gegen **NetBox** oder **EfficientIP SOLIDserver** validiert.

Das Tool arbeitet nach dem Fail-Fast-Prinzip: Ist eine IP oder ein Subnetz nicht im IPAM registriert, bricht das Skript mit Exit-Code `1` ab, bevor nachgelagerte Schritte wie `terraform plan` oder `terraform apply` starten.

## Features

- **Multi-Provider:** Unterstützt sowohl NetBox (`/api/ipam/`) als auch EfficientIP SOLIDserver (`/rest/`).
- **Host & Subnetz-Erkennung:** Unterscheidet automatisch zwischen Einzel-IPs und CIDR-Subnetzen.
- **Rekursives YAML-Parsing:** Findet IPv4- und IPv6-Adressen unabhängig von der Verschachtelungstiefe der YAML-Datei.
- **CI/CD-Ready:** Steuerung komplett über Umgebungsvariablen oder CLI-Parameter möglich.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Verwendung

### 1. NetBox

```bash
export IPAM_PROVIDER="netbox"
export IPAM_URL="[https://netbox.example.com](https://netbox.example.com)"
export IPAM_TOKEN="dein-api-token"

python ipam_checker.py -f ./rules.yaml
```

### 2. EfficientIP SOLIDserver

```bash
export IPAM_PROVIDER="efficientip"
export IPAM_URL="[https://solidserver.example.com](https://solidserver.example.com)"
export IPAM_USER="svc_pipeline"
export IPAM_PASSWORD="dein-passwort"

python ipam_checker.py -f ./rules.yaml
```

### CLI-Parameter

- `-f`, `--file`: Pfad zur zu prüfenden YAML-Datei (Pflichtfeld)
- `-p`, `--provider`: `netbox` oder `efficientip` (Standard: `netbox` oder `ENV: IPAM_PROVIDER`)
- `--url`: Basis-URL des IPAM-Systems (`ENV: IPAM_URL`)
- `--token`: API-Token für NetBox (`ENV: IPAM_TOKEN`)
- `--user`: Benutzername für EfficientIP (`ENV: IPAM_USER`)
- `--password`: Passwort für EfficientIP (`ENV: IPAM_PASSWORD`)
- `--insecure`: Ignoriert selbstsignierte SSL-Zertifikate bei internen IPAM-Instanzen

## Exit-Codes

| Code | Beschreibung |
| :--- | :--- |
| `0` | Alle gefundenen IPs/Subnetze sind im IPAM registriert. |
| `1` | Mindestens eine IP oder ein Subnetz wurde nicht im IPAM gefunden. |
| `2` | Technischer Fehler (fehlende Credentials, YAML-Syntaxfehler oder API nicht erreichbar). |

## Einbindung in GitHub Actions

```yaml
- name: Validate IPs against IPAM
  env:
    IPAM_PROVIDER: "efficientip"
    IPAM_URL: ${{ secrets.IPAM_URL }}
    IPAM_USER: ${{ secrets.IPAM_USER }}
    IPAM_PASSWORD: ${{ secrets.IPAM_PASSWORD }}
  run: |
    python tools/ipam-checker/ipam_checker.py -f ./configs/firewall-rules.yaml
```