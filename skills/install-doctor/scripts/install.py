#!/usr/bin/env python3
"""Install the doctor agent for the current user (or a project with --project DIR).

Copies the agent and its stats script into <target>/.claude, rewrites the script path
inside the agent, and adds the 🩺 status line unless one is already configured.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="install into this project's .claude/ instead of ~/.claude/")
    ap.add_argument("--no-statusline", action="store_true")
    ap.add_argument("--force-statusline", action="store_true", help="replace an existing statusLine")
    args = ap.parse_args()

    claude = (Path(args.project).resolve() if args.project else Path.home()) / ".claude"
    script = claude / "doctor" / "session_stats.py"
    agent = claude / "agents" / "doctor.md"
    script.parent.mkdir(parents=True, exist_ok=True)
    agent.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(ASSETS / "session_stats.py", script)
    text = (ASSETS / "doctor.md").read_text(encoding="utf-8")
    agent.write_text(text.replace("python3 .claude/doctor/session_stats.py", f'"{sys.executable}" "{script}"'), encoding="utf-8")
    print(f"agent:  {agent}\nscript: {script}")

    if args.no_statusline:
        return
    settings_path = claude / "settings.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    except ValueError:
        print(f"statusline: skipped, {settings_path} is not valid JSON")
        return
    if "statusLine" in settings and not args.force_statusline:
        print(f"statusline: skipped, one already exists in {settings_path} (use --force-statusline)")
        return
    settings["statusLine"] = {"type": "command", "command": f'"{sys.executable}" "{script}" --statusline'}
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"statusline: added to {settings_path}")


if __name__ == "__main__":
    main()
