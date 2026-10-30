# IPAM YAML Validator

A lightweight CLI tool for CI/CD pipelines that extracts IP addresses and subnets from declarative YAML files (e.g., firewall or NSG rules) and validates them against **NetBox** or **EfficientIP SOLIDserver**.

The tool operates on a fail-fast principle: if an IP address or subnet is not registered in the IPAM, the script exits with code `1` before subsequent steps like `terraform plan` or `terraform apply` can start.

## Features

- **Multi-Provider:** Supports both NetBox (`/api/ipam/`) and EfficientIP SOLIDserver (`/rest/`).
- **Host & Subnet Detection:** Automatically distinguishes between single IPs and CIDR subnets.
- **Recursive YAML Parsing:** Finds IPv4 and IPv6 addresses regardless of the nesting depth of the YAML file.
- **CI/CD Ready:** Fully controllable via environment variables or CLI parameters.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### 1. NetBox

```bash
export IPAM_PROVIDER="netbox"
export IPAM_URL="[https://netbox.example.com](https://netbox.example.com)"
export IPAM_TOKEN="your-api-token"

python ipam_checker.py -f ./rules.yaml
```

### 2. EfficientIP SOLIDserver

```bash
export IPAM_PROVIDER="efficientip"
export IPAM_URL="[https://solidserver.example.com](https://solidserver.example.com)"
export IPAM_USER="svc_pipeline"
export IPAM_PASSWORD="your-password"

python ipam_checker.py -f ./rules.yaml
```

### CLI Parameters

- `-f`, `--file`: Path to the YAML file to validate (Required)
- `-p`, `--provider`: `netbox` or `efficientip` (Default: `netbox` or `ENV: IPAM_PROVIDER`)
- `--url`: Base URL of the IPAM system (`ENV: IPAM_URL`)
- `--token`: API token for NetBox (`ENV: IPAM_TOKEN`)
- `--user`: Username for EfficientIP (`ENV: IPAM_USER`)
- `--password`: Password for EfficientIP (`ENV: IPAM_PASSWORD`)
- `--insecure`: Ignores self-signed SSL certificates for internal IPAM instances

## Exit Codes

| Code | Description |
| :--- | :--- |
| `0` | All found IPs/subnets are registered in the IPAM. |
| `1` | At least one IP or subnet was not found in the IPAM. |
| `2` | Technical error (missing credentials, YAML syntax error, or API unreachable). |

## Integration in GitHub Actions

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