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

## Share with someone else
Give them `install-doctor.skill` (source: `skills/install-doctor/`). They upload it in Claude
(Settings → Capabilities → Skills) or unzip it into `~/.claude/skills/`, then ask
"install the doctor agent". Or run the installer directly:
`python3 install-doctor/scripts/install.py` (user-wide) / `--project .` (one project).

# nta-billing — נת"ע billing tool

`nta-billing/`: command-line tool that builds the נת"ע bills of quantities (see `nta-billing/SETUP.md` and `nta-billing/CLAUDE.md`).
Formulas are recalculated by a built-in Python engine (`nta-billing/engine/xlcalc.py`), so LibreOffice is only needed for the PDF export.
Tests: `cd nta-billing && python -m unittest discover tests`.
