# Terraform Drift Notifier

Ein leichtgewichtiges CLI-Tool für CI/CD-Pipelines, das die JSON-Ausgabe eines `terraform plan` analysiert, manuelle Cloud-Änderungen (Out-of-Band Drifts) erkennt und als übersichtlichen Markdown-Report oder Webhook-Alarm (MS Teams / Slack) ausgibt.

## Features

- **Klare Kategorisierung:** Gruppiert Abweichungen nach `Replace`, `Delete`, `Update` und `Create`.
- **Markdown-Export:** Generiert saubere Berichte für GitHub Step Summaries (`$GITHUB_STEP_SUMMARY`) oder Pull-Request-Kommentare.
- **Webhook-Integration:** Sendet Benachrichtigungen nur dann, wenn tatsächlich ein Drift vorliegt.
- **Pipeline-Steuerung:** Optionales `--fail-on-drift`-Flag, um geplante CI-Jobs bei Abweichungen gezielt als fehlgeschlagen zu markieren.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Verwendung

### 1. Terraform Plan als JSON erzeugen

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
```

### 2. Drift-Analyse starten

```bash
python drift_notifier.py \
  --file plan.json \
  --project "azure-hub-network" \
  --output drift-report.md \
  --fail-on-drift
```

### CLI-Parameter

- `-f`, `--file`: Pfad zur `plan.json`-Datei (Pflichtfeld)
- `-p`, `--project`: Name des Terraform-Stacks (`ENV: TF_PROJECT_NAME`)
- `-w`, `--webhook`: Webhook-URL für MS Teams / Slack (`ENV: DRIFT_WEBHOOK_URL`)
- `-o`, `--output`: Speichert den Markdown-Bericht in einer Datei
- `--fail-on-drift`: Gibt Exit-Code `1` zurück, sobald mindestens eine Abweichung erkannt wird

## Exit-Codes

| Code | Beschreibung |
| :--- | :--- |
| `0` | Kein Drift erkannt (oder Drift erkannt ohne `--fail-on-drift`). |
| `1` | Drift erkannt (in Verbindung mit `--fail-on-drift`). |
| `2` | Technischer Fehler (Datei nicht lesbar, JSON ungültig, Webhook fehlgeschlagen). |

## Einbindung in GitHub Actions (Nightly Drift Check)

```yaml
- name: Generate Terraform Plan JSON
  run: |
    terraform init
    terraform plan -out=tfplan
    terraform show -json tfplan > plan.json

- name: Analyze Drift
  env:
    DRIFT_WEBHOOK_URL: ${{ secrets.DRIFT_WEBHOOK_URL }}
  run: |
    python tools/tf-drift-notifier/drift_notifier.py \
      -f plan.json \
      -p "prod-firewall" \
      -o $GITHUB_STEP_SUMMARY \
      --fail-on-drift
```