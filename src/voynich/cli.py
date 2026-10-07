"""Discover and explicitly run historical experiments without importing them eagerly."""
import argparse
import runpy
import sys
from pathlib import Path


def experiments() -> dict[str, str]:
    return {p.name[1:3]: p.stem for p in sorted((Path(__file__).parent / "experiments").glob("e[0-9][0-9]_*.py"))}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Voynich research commands")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List experiment IDs without executing analyses")
    run = sub.add_parser("experiment", help="Run a numbered experiment; later arguments go to its parser")
    run.add_argument("id", choices=list(experiments()))
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command == "list":
        for number, module in experiments().items():
            print(f"{number}  {module[4:]}")
        return
    module = "voynich.experiments." + experiments()[args.id]
    original = sys.argv
    try:
        sys.argv = [module, *args.arguments]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original
