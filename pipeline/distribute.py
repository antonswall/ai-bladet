#!/usr/bin/env python3
"""
AI-Bladet — Distribution Orchestrator
=======================================
Körs efter lyckad publicering (från run_weekly.sh).
Kickar igång alla distribueringsmoduler parallellt.

Anrop: python distribute.py --issue content/YYYY-WW.md [--dry-run]

Exit-kod: 0 om minst hälften av stegen lyckades, 1 annars.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


PIPELINE_DIR = Path(__file__).parent
OUTPUT_DIR = PIPELINE_DIR / "output" / "distribution"
DIST_DIR = PIPELINE_DIR


def load_issue(issue_path: str) -> dict:
    """Läs issue-fil och extrahera frontmatter + stories."""
    import yaml

    path = Path(issue_path)
    if not path.exists():
        raise FileNotFoundError(f"Issue-fil saknas: {issue_path}")

    text = path.read_text(encoding="utf-8")

    # Extrahera YAML frontmatter
    if not text.startswith("---"):
        raise ValueError(f"Inget YAML frontmatter i {issue_path}")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Ofullständigt YAML frontmatter i {issue_path}")

    frontmatter = yaml.safe_load(parts[1])
    return frontmatter


def run_module(module_name: str, issue_path: str, dry_run: bool = False) -> tuple[str, bool, str]:
    """Kör ett distribueringssteg som subprocess. Returnerar (namn, success, output)."""
    start = time.time()
    script = DIST_DIR / module_name

    if not script.exists():
        return (module_name, False, f"Script saknas: {script}")

    cmd = [sys.executable, str(script), "--issue", issue_path]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        elapsed = time.time() - start
        success = result.returncode == 0
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        return (module_name, success, f"{output} ({elapsed:.1f}s)")
    except subprocess.TimeoutExpired:
        return (module_name, False, "Timeout (120s)")
    except Exception as e:
        return (module_name, False, str(e))


def main():
    parser = argparse.ArgumentParser(description="AI-Bladet distribution orchestrator")
    parser.add_argument("--issue", required=True, help="Sökväg till issue-fil (content/YYYY-WW.md)")
    parser.add_argument("--dry-run", action="store_true", help="Simulera utan att göra anrop")
    parser.add_argument("--modules", nargs="+",
                        default=["distribute_audio.py", "distribute_x.py",
                                 "distribute_glossary.py", "distribute_meme.py",
                                 "distribute_linkedin.py"],
                        help="Moduler att köra (default: alla)")
    args = parser.parse_args()

    # Ladda issue för metadata
    try:
        issue = load_issue(args.issue)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        sys.exit(1)

    week = issue.get("week", "?")
    year = issue.get("year", datetime.now().year)
    print(f"📦 Distribution vecka {week}/{year}")
    print(f"   Issue: {args.issue}")
    if args.dry_run:
        print("   🏃 Dry-run mode (inga externa anrop)")
    print()

    # Skapa output-kataloger
    for d in ["audio", "x", "linkedin", "glossary", "memes"]:
        (OUTPUT_DIR / d).mkdir(parents=True, exist_ok=True)

    # Kör moduler parallellt
    modules = args.modules
    print(f"🚀 Startar {len(modules)} moduler parallellt...")
    print()

    results = []
    with ThreadPoolExecutor(max_workers=len(modules)) as executor:
        futures = {
            executor.submit(run_module, mod, args.issue, args.dry_run): mod
            for mod in modules
        }
        for future in as_completed(futures):
            name, success, output = future.result()
            results.append((name, success, output))
            icon = "✅" if success else "❌"
            print(f"  {icon} {name}: {output}")

    # Summering
    print()
    successes = sum(1 for _, s, _ in results if s)
    total = len(results)
    print(f"📊 Resultat: {successes}/{total} lyckades")

    # Minst 50% måste lyckas för att distributionen ska räknas som ok
    exit_code = 0 if successes >= total / 2 else 1
    if exit_code == 0:
        print("✅ Distribution godkänd")
    else:
        print("❌ Distribution misslyckades — för många fel")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
