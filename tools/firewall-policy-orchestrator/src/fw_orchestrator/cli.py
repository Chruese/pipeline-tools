import argparse
import json
import logging
import sys
from pathlib import Path
import yaml

from .models import TicketPolicy
from .topology import verify_cidrs_against_registry
from .compilers.azure import build_azure_rcg
from .interactive import run_wizard

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("fw-orchestrator")

def compile_cmd(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry)
    policies_dir = Path(args.policies)
    build_dir = Path(args.build_dir)
    env = args.environment

    if not registry_path.is_file():
        logger.error(f"Registry nicht gefunden: {registry_path}")
        return 1

    registry_units = yaml.safe_load(registry_path.read_text(encoding="utf-8"))["units"]
    yaml_files = sorted(policies_dir.glob(f"{env}/**/*.yaml"))
    
    if not yaml_files:
        logger.warning(f"Keine Policies für Environment '{env}' gefunden.")
        return 0

    tickets: list[TicketPolicy] = []
    requires_secops = False

    for yfile in yaml_files:
        raw = yaml.safe_load(yfile.read_text(encoding="utf-8"))
        ticket = TicketPolicy.model_validate(raw)
        
        for r in ticket.rules:
            verify_cidrs_against_registry(r.source.unit, r.source.cidrs, registry_units)
            verify_cidrs_against_registry(r.destination.unit, r.destination.cidrs, registry_units)
            if r.security_approval:
                requires_secops = True

        tickets.append(ticket)

    # Compile Azure
    azure_payload = build_azure_rcg(tickets, registry_units, env)
    build_dir.mkdir(parents=True, exist_ok=True)
    out_file = build_dir / f"azure_{env}_rcg.json"
    out_file.write_text(json.dumps(azure_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    
    logger.info(f"Kompilierung abgeschlossen: {out_file}")
    return 2 if requires_secops else 0

def main() -> None:
    parser = argparse.ArgumentParser(prog="fw-tool", description="Firewall Policy Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: compile
    p_compile = subparsers.add_parser("compile", help="Kompiliert YAML-Tickets in Target-Payloads")
    p_compile.add_argument("-e", "--environment", default="prod", help="Target Environment (dev/stage/prod)")
    p_compile.add_argument("-r", "--registry", default="config/topology_registry.yaml", help="Pfad zur Registry")
    p_compile.add_argument("-p", "--policies", default="policies", help="Pfad zum Policies-Verzeichnis")
    p_compile.add_argument("-b", "--build-dir", default="build", help="Ausgabeverzeichnis")

    # Subcommand: wizard
    p_wizard = subparsers.add_parser("wizard", help="Interaktiver Assistent zum Anlegen eines Tickets")
    p_wizard.add_argument("-o", "--output-dir", default="policies", help="Basis-Pfad für Tickets")

    args = parser.parse_args()
    if args.subcommand == "compile":
        sys.exit(compile_cmd(args))
    elif args.subcommand == "wizard":
        run_wizard(Path(args.output_dir))

if __name__ == "__main__":
    main()