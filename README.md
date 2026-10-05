# Doctor 🩺 — Claude Code efficiency agent

| File | Purpose |
|---|---|
| `.claude/agents/doctor.md` | The `doctor` subagent: measures the session, diagnoses waste, prescribes fixes. |
| `.claude/doctor/session_stats.py` | Parses the local session transcript (zero model tokens) and computes cache savings, including the doctor's own cost. |
| `.claude/settings.json` | Always-on status line: `🩺 חיסכון 87% · cache 91% · ctx 64k · out 12k`. |

## Usage
- In Claude Code: "doctor, check my session" / "דוקטור, תבדוק אותי" (or `@doctor`).
  Note: `/doctor` is a built-in Claude Code command (installation check), so invoke the agent by name.
- Manually: `python3 .claude/doctor/session_stats.py` (JSON report).
- Global install: copy `.claude/agents/doctor.md` to `~/.claude/agents/` and the script to `~/.claude/doctor/`, then point the agent's command at `~/.claude/doctor/session_stats.py`.

"Saved %" = cost reduction vs. the same session with no prompt caching
(input 1×, cache write 1.25× / 2×, cache read 0.1×, output 5×).
