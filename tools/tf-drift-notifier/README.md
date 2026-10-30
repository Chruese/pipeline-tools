# Terraform Drift Notifier

A lightweight CLI tool for CI/CD pipelines that analyzes the JSON output of a `terraform plan`, detects manual cloud changes (out-of-band drifts), and outputs a clear Markdown report or webhook alert (MS Teams / Slack).

## Features

- **Clear Categorization:** Groups deviations into `Replace`, `Delete`, `Update`, and `Create`.
- **Markdown Export:** Generates clean reports for GitHub Step Summaries (`$GITHUB_STEP_SUMMARY`) or pull request comments.
- **Webhook Integration:** Sends notifications only when a drift is actually detected.
- **Pipeline Control:** Optional `--fail-on-drift` flag to intentionally fail scheduled CI jobs upon deviations.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1. Generate Terraform Plan as JSON

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
```

### 2. Run Drift Analysis

```bash
python drift_notifier.py \
  --file plan.json \
  --project "azure-hub-network" \
  --output drift-report.md \
  --fail-on-drift
```

### CLI Parameters

- `-f`, `--file`: Path to the `plan.json` file (Required)
- `-p`, `--project`: Name of the Terraform stack (`ENV: TF_PROJECT_NAME`)
- `-w`, `--webhook`: Webhook URL for MS Teams / Slack (`ENV: DRIFT_WEBHOOK_URL`)
- `-o`, `--output`: Saves the Markdown report to a file
- `--fail-on-drift`: Returns exit code `1` as soon as at least one deviation is detected

## Exit Codes

| Code | Description |
| :--- | :--- |
| `0` | No drift detected (or drift detected without `--fail-on-drift`). |
| `1` | Drift detected (in combination with `--fail-on-drift`). |
| `2` | Technical error (file unreadable, invalid JSON, webhook failed). |

## Integration in GitHub Actions (Nightly Drift Check)

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