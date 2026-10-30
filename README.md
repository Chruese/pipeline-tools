# Pipeline Tools

A centralized collection of CLI scripts, validators, and automation utilities specifically designed for use in CI/CD pipelines (e.g., GitHub Actions) and platform automation.

The goal of these tools is to catch errors in declarative Infrastructure-as-Code (IaC) via a **"Shift-Left"** approach—well before actual Terraform execution (`plan` / `apply`).

---

## 📂 Repository Structure

```text
pipeline-tools/
├── tools/
│   ├── ipam-checker/         # Validates IP addresses against NetBox or EfficientIP API
│   ├── tf-drift-notifier/    # Analyzes Terraform JSON plans for manual changes (drifts)
│   ├── dns-record-validator/ # Validates DNS records against internal/external nameservers
│   └── tf-state-analyzer/    # Analyzes Terraform state files for metrics and sizing
└── README.md
```

---

## 🛠️ Included Tools

### 1. `ipam-checker`
A CI/CD validator that recursively extracts IP addresses and subnets from declarative YAML files (e.g., firewall or NSG rules) and checks them against an IPAM system.
- **Providers:** NetBox, EfficientIP SOLIDserver
- **Behavior:** Fails the pipeline (`Exit Code 1`) if any IP is not registered in the IPAM.

### 2. `tf-drift-notifier`
Parses the JSON output of a `terraform plan` and formats manual out-of-band changes into a clear Markdown report (including optional webhook alerts for Teams/Slack).

### 3. `dns-record-validator`
Checks defined DNS records (`A`, `CNAME`, `PTR`, etc.) from a YAML configuration against specific nameservers (e.g., internal core DNS servers or Azure Private Resolvers) to prevent routing and naming conflicts beforehand.

### 4. `tf-state-analyzer`
Examines Terraform state files to analyze resource density, blast radius, and the distribution of cloud resources.

---

## 🚀 General Usage

Each tool resides in its own subdirectory under `tools/` and includes a dedicated `requirements.txt` and documentation.

Example for local execution:

```bash
cd tools/<tool-name>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python <script-name>.py --help
```

---


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
## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.