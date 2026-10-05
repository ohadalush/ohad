#!/usr/bin/env python3
"""Install the doctor and super-doctor agents for the current user (or a project with --project DIR).

Copies the agents, playbook and stats script into <target>/.claude, rewrites their paths
inside the agents, and adds the 🩺 status line unless one is already configured.
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
    doctor_dir = claude / "doctor"
    script = doctor_dir / "session_stats.py"
    doctor_dir.mkdir(parents=True, exist_ok=True)
    (claude / "agents").mkdir(parents=True, exist_ok=True)

    shutil.copyfile(ASSETS / "session_stats.py", script)
    shutil.copyfile(ASSETS / "playbook.md", doctor_dir / "playbook.md")
    for name in ("doctor.md", "super-doctor.md"):
        text = (ASSETS / name).read_text(encoding="utf-8")
        # Project installs keep the relative paths so the repo can be committed and cloned anywhere.
        # User-wide installs point at ~/.claude/doctor; backups, changes.log and session-plan.md stay project-relative.
        if not args.project:
            text = text.replace("python3 .claude/doctor/session_stats.py", f'"{sys.executable}" "{script}"')
            text = text.replace("`.claude/doctor/playbook.md`", f"`{doctor_dir / 'playbook.md'}`")
        (claude / "agents" / name).write_text(text, encoding="utf-8")
    print(f"agents: {claude / 'agents'}/doctor.md, super-doctor.md\nfiles:  {doctor_dir}")

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
