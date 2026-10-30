# Pipeline Tools

Eine zentrale Sammlung von CLI-Skripten, Validatoren und Automatisierungswerkzeugen, die gezielt für den Einsatz in CI/CD-Pipelines (z. B. GitHub Actions) und Plattform-Automatisierungen entwickelt wurden.

Das Ziel dieser Tools ist es, Fehler im deklarativen Infrastructure-as-Code (IaC) **„Shift-Left“** abzufangen – also noch vor dem eigentlichen Terraform-Ausführen (`plan` / `apply`).

---

## 📂 Repository-Struktur

```text
pipeline-tools/
├── tools/
│   ├── ipam-checker/         # Prüft IP-Adressen gegen NetBox oder EfficientIP API
│   ├── tf-drift-notifier/    # Analysiert Terraform JSON-Pläne auf manuelle Änderungen (Drifts)
│   ├── dns-record-validator/ # Validiert DNS-Einträge gegen interne/externe Nameserver
│   └── tf-state-analyzer/    # Analysiert Terraform State-Dateien auf Metriken und Größe
└── README.md
```

---

## 🛠️ Enthaltene Tools

### 1. `ipam-checker`
Ein CI/CD-Validator, der IP-Adressen und Subnetze rekursiv aus deklarativen YAML-Dateien (z. B. Firewall- oder NSG-Regeln) extrahiert und gegen ein IPAM-System abgleicht.
- **Provider:** NetBox, EfficientIP SOLIDserver
- **Verhalten:** Bricht die Pipeline (`Exit-Code 1`) ab, wenn IPs nicht im IPAM registriert sind.

### 2. `tf-drift-notifier`
Parst die JSON-Ausgabe eines `terraform plan` und bereitet manuelle Out-of-Band-Änderungen als übersichtlichen Markdown-Bericht auf (inklusive optionalem Webhook-Alarm für Teams/Slack).

### 3. `dns-record-validator`
Prüft definierte DNS-Einträge (`A`, `CNAME`, `PTR`, etc.) aus einer YAML-Konfiguration gegen spezifische Nameserver (z. B. interne Core-DNS-Server oder Azure Private Resolver), um Routing- und Namenskonflikte vorab zu verhindern.

### 4. `tf-state-analyzer`
Untersucht Terraform-State-Dateien, um die Ressourcendichte, den Blast-Radius und die Verteilung von Cloud-Ressourcen zu analysieren.

---

## 🚀 Allgemeine Verwendung

Jedes Tool liegt in einem eigenen Unterverzeichnis unter `tools/` und bringt eine eigene `requirements.txt` sowie Dokumentation mit.

Beispiel für die lokale Ausführung:

```bash
cd tools/<tool-name>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python <script-name>.py --help
```

---

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.