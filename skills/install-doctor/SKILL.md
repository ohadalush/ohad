---
name: install-doctor
description: Installs the "doctor" 🩺 Claude Code subagent, which measures a session's real token usage and prompt-cache savings and prescribes concrete efficiency fixes. Use when the user asks to install, set up, or update the doctor agent.
---

# Install the doctor agent

1. Ask once where to install if the user didn't say: **user-wide** (default, `~/.claude/`, works in every project) or **this project only** (`./.claude/`, can be committed for the team).
2. Run the installer that ships with this skill (it needs only Python 3, no packages):
   - user-wide: `python3 <this skill dir>/scripts/install.py`
   - project: `python3 <this skill dir>/scripts/install.py --project .`
   Add `--no-statusline` if the user doesn't want the status line. If it reports an existing statusLine, tell the user and offer `--force-statusline`; never replace it silently.
3. Verify: run the installed stats script once (path printed by the installer) and confirm it prints JSON.
4. Tell the user, in their language:
   - Restart Claude Code (or start a new session) so the agent loads.
   - Invoke it with "doctor, check my session" / "דוקטור, תבדוק אותי" or `@doctor`. Not `/doctor`: that is a built-in command.
   - The status line `🩺 חיסכון X% · cache Y% · ctx Nk · out Nk` updates every turn at zero token cost.
   - "Saved %" is the cost reduction versus the same session without prompt caching, including the doctor's own run.

Files installed: `agents/doctor.md` (the agent) and `doctor/session_stats.py` (local transcript parser, no network access).
