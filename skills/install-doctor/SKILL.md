---
name: install-doctor
description: Installs the "doctor" 🩺 and "super-doctor" ⚡ Claude Code subagents. doctor measures a session's real token usage and cache savings and prescribes fixes (applied on request); super-doctor runs before a task, applies safe token-saving setup changes and returns a work plan. Use when the user asks to install, set up, or update the doctor agents.
---

# Install the doctor agents

1. Ask once where to install if the user didn't say: **user-wide** (default, `~/.claude/`, works in every project) or **this project only** (`./.claude/`, can be committed for the team).
2. Run the installer that ships with this skill (it needs only Python 3, no packages):
   - user-wide: `python3 <this skill dir>/scripts/install.py`
   - project: `python3 <this skill dir>/scripts/install.py --project .`
   Add `--no-statusline` if the user doesn't want the status line. If it reports an existing statusLine, tell the user and offer `--force-statusline`; never replace it silently.
3. Verify: run the installed stats script once (path printed by the installer) and confirm it prints JSON.
4. Tell the user, in their language:
   - Restart Claude Code (or start a new session) so the agent loads.
   - **doctor**: "דוקטור, תבדוק אותי" or `@doctor`. Measures and suggests numbered treatments; "דוקטור, בצע טיפול 1,3" applies them. Not `/doctor`: that is a built-in command.
   - **super-doctor**: at the start of a task, "סופר-דוקטור, אני מתחיל עכשיו <task>, תחסוך כמה שיותר בלי לפגוע באיכות". It changes project settings (with backups in `.claude/doctor/backups/`) and returns a work plan for the session.
   - The status line `🩺 חיסכון X% · cache Y% · ctx Nk · out Nk` updates every turn at zero token cost.
   - "Saved %" is the cost reduction versus the same session without prompt caching, including the doctor's own run.

Files installed: `agents/doctor.md`, `agents/super-doctor.md`, `doctor/playbook.md` (shared knowledge base) and `doctor/session_stats.py` (local transcript parser, no network access).
