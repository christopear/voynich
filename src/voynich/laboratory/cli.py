"""Explicit registry commands; no experiment runs on import or inspection."""
import argparse
import json
from pathlib import Path
from voynich.laboratory.manifest import ExperimentSpec, scope_changes
from voynich.storage.artifacts import read_json
from voynich.storage.database import make_engine
from voynich.storage.registry import Registry, DuplicateExperiment


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cipher laboratory registry")
    sub = parser.add_subparsers(dest="command", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--family")
    ls.add_argument("--spec-id")
    register = sub.add_parser("register")
    register.add_argument("manifest", type=Path)
    register.add_argument("--artifacts", required=True)
    register.add_argument("--rerun-reason")
    legacy = sub.add_parser("import-pilots")
    legacy.add_argument("directory", type=Path)
    compare = sub.add_parser("compare")
    compare.add_argument("previous", type=Path)
    compare.add_argument("proposed", type=Path)
    scope = sub.add_parser("scope")
    scope.add_argument("manifest", type=Path)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "compare":
        print(json.dumps({"changed": scope_changes(read_json(args.previous), read_json(args.proposed)),
                          "meaning": "Changed scope requires reconsideration; no automatic verdict."}, indent=2))
        return 0
    if args.command == "validate":
        spec = ExperimentSpec(args.manifest.read_text())
        print(json.dumps({"spec_id": spec.id, "status": "valid"}))
        return 0
    engine = make_engine()
    try:
        registry = Registry(engine)
        if args.command == "list":
            print(json.dumps(registry.list(family=args.family, spec_id=args.spec_id), indent=2, default=str))
        elif args.command == "scope":
            spec = ExperimentSpec(args.manifest.read_text())
            entries = registry.list(family=spec.data["family"])
            report = [{"run_id": row["id"], "state": row["state"],
                       "same_specification": row["spec_id"] == spec.id,
                       "changed": scope_changes(row["manifest"], spec.data),
                       "evidence_status": row["evidence_status"]} for row in entries]
            print(json.dumps({"requested_spec": spec.id, "prior_runs": report,
                "unregistered_scope": not any(r["same_specification"] for r in report),
                "caution": "Registration alone is not evidence; changed scopes do not transfer automatically."}, indent=2))
        elif args.command == "register":
            spec = ExperimentSpec(args.manifest.read_text())
            print(registry.register(spec, args.artifacts, rerun_reason=args.rerun_reason))
        elif args.command == "import-pilots":
            for path in sorted(args.directory.glob("*.json")):
                try:
                    print(path.name, registry.import_pilot(path))
                except DuplicateExperiment:
                    print(path.name, "already indexed")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
