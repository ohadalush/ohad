# Doctor 🩺 — Claude Code efficiency agent

| File | Purpose |
|---|---|
| `.claude/agents/doctor.md` | The `doctor` subagent: measures the session, diagnoses waste, prescribes numbered treatments, applies them on request ("דוקטור, בצע טיפול 1,3"). |
| `.claude/agents/super-doctor.md` | The `super-doctor` subagent: run before a task; applies safe setup treatments (with backups) and returns a token-saving work plan for the session. |
| `.claude/doctor/playbook.md` | Shared knowledge base and the list of safe, reversible treatments. |
| `.claude/doctor/session_stats.py` | Parses the local session transcript (zero model tokens) and computes cache savings, including the doctor's own cost. |
| `.claude/settings.json` | Always-on status line: `🩺 חיסכון 87% · cache 91% · ctx 64k · out 12k`. |

## Usage
- Before a task: "סופר-דוקטור, אני מתחיל עכשיו <task>, תחסוך כמה שיותר בלי לפגוע באיכות" (or `@super-doctor`).
  Changes to Claude Code config may ask for your approval; undo from `.claude/doctor/backups/`.
- After / during a task: "דוקטור, תבדוק אותי" (or `@doctor`).
  Note: `/doctor` is a built-in Claude Code command (installation check), so invoke the agent by name.
- Manually: `python3 .claude/doctor/session_stats.py` (JSON report).
- Global install: copy `.claude/agents/doctor.md` to `~/.claude/agents/` and the script to `~/.claude/doctor/`, then point the agent's command at `~/.claude/doctor/session_stats.py`.

"Saved %" = cost reduction vs. the same session with no prompt caching
(input 1×, cache write 1.25× / 2×, cache read 0.1×, output 5×).

## Share with someone else
Give them `install-doctor.skill` (source: `skills/install-doctor/`). They upload it in Claude
(Settings → Capabilities → Skills) or unzip it into `~/.claude/skills/`, then ask
"install the doctor agent". Or run the installer directly:
`python3 install-doctor/scripts/install.py` (user-wide) / `--project .` (one project).
