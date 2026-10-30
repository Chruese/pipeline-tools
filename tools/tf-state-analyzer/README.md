# Terraform State Analyzer

A lightweight CLI tool and CI/CD security scanner that inspects Terraform state files (`.tfstate`) for accidentally exposed secrets, API keys, passwords, and sensitive configurations.

The tool helps enforce security compliance by catching leaked secrets in state artifacts before they are stored insecurely or exposed in collaborative environments.

---

## Features

- **Deep State Inspection:** Recursively parses nested JSON structures in Terraform state files (resources, modules, instances, attributes).
- **Smart Detection:** Combines sensitive keyword matching, regex patterns (AWS, GitHub, Google API keys, private keys), and heuristics (such as Azure connection strings).
- **Masking:** Automatically masks sensitive values in reports (`abc...xyz`) for safe sharing and auditing.
- **Multiple Output Formats:** Generates reports in **JSON**, **Markdown** (ideal for Pull Request comments or step summaries), and plain **Text**.
- **CI/CD Ready:** Returns exit code `1` if secrets are found, enabling automated pipeline blocks.

---

## Project Structure

```text
tf-state-analyzer/
├── main.py             # CLI entry point and orchestration
├── state_loader.py     # State file loading and validation
├── secret_scanner.py   # Secret detection, regex, and masking logic
├── report_generator.py # Formats and saves reports (JSON, Markdown, TXT)
├── utils.py            # Recursive state walker generator
└── requirements.txt    # Python dependencies
```

---

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Local Execution

Scan a state file and print the text report to the console:
```bash
python main.py --state ./terraform.tfstate
```

Generate a Markdown report for documentation or Pull Requests:
```bash
python main.py --state ./terraform.tfstate --output report.md
```

### CLI Parameters

- `--state`: Path to the Terraform state file (`.tfstate`) — **Required**
- `--output`: Optional path to save the report. The format is automatically determined by the file extension (`.json`, `.md`, `.txt`).

---

## Exit Codes

| Code | Description |
| :--- | :--- |
| `0` | Clean. No secrets found in the state file. |
| `1` | Findings detected. One or more potential secrets were discovered. |
| `2` | Error. State file not found, unreadable, or invalid JSON. |

---

## Integration in GitHub Actions

```yaml
- name: Scan Terraform State for Secrets
  run: |
    python tools/tf-state-analyzer/main.py \
      --state ./terraform.tfstate \
      --output $GITHUB_STEP_SUMMARY
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.