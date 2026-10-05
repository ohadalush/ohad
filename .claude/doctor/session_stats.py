#!/usr/bin/env python3
"""Token-usage stats for a Claude Code session, read from its local transcript.

Costs nothing in model tokens: it only parses ~/.claude/projects/<project>/<session>.jsonl
(plus <session>/subagents/*.jsonl) and prices usage relative to uncached input.

Usage:
  session_stats.py                 # newest session of the current project, JSON report
  session_stats.py --transcript F  # a specific transcript
  session_stats.py --statusline    # one-line summary; reads Claude Code statusline JSON on stdin
"""
import argparse
import glob
import json
import os
import sys
import time

# Price multipliers relative to one uncached input token (same ratios across current Claude models).
W_INPUT, W_WRITE_5M, W_WRITE_1H, W_READ, W_OUTPUT = 1.0, 1.25, 2.0, 0.1, 5.0


def projects_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(base, "projects")


def newest_transcript(cwd):
    root = projects_dir()
    slug = "".join(c if c.isalnum() else "-" for c in os.path.abspath(cwd))
    files = glob.glob(os.path.join(root, slug, "*.jsonl")) or glob.glob(os.path.join(root, "*", "*.jsonl"))
    return max(files, key=os.path.getmtime) if files else None


def empty():
    return {"requests": 0, "input": 0, "write_5m": 0, "write_1h": 0, "read": 0, "output": 0, "thinking": 0}


def add_usage(acc, u):
    acc["requests"] += 1
    acc["input"] += u.get("input_tokens") or 0
    acc["read"] += u.get("cache_read_input_tokens") or 0
    cc = u.get("cache_creation") or {}
    w5, w1 = cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens")
    if w5 is None and w1 is None:
        w5, w1 = u.get("cache_creation_input_tokens") or 0, 0
    acc["write_5m"] += w5 or 0
    acc["write_1h"] += w1 or 0
    acc["output"] += u.get("output_tokens") or 0
    acc["thinking"] += (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0


def scan(path, acc, seen, extra):
    """Accumulate usage from one transcript, de-duplicating streamed copies of the same message."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
                extra["compactions"] += 1
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            if d.get("type") == "user" and isinstance(msg.get("content"), list):
                for b in msg["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        size = len(json.dumps(b.get("content"), ensure_ascii=False))
                        extra["tool_results"].append(size)
            u, mid = msg.get("usage"), msg.get("id")
            if not u or mid in seen:
                continue
            seen.add(mid)
            add_usage(acc, u)
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            extra["max_context"] = max(extra["max_context"], ctx)
            if msg.get("model"):
                extra["models"][msg["model"]] = extra["models"].get(msg["model"], 0) + 1


def is_doctor(path, recent_cutoff):
    meta = path[: -len(".jsonl")] + ".meta.json"
    try:
        with open(meta, encoding="utf-8") as fh:
            if json.load(fh).get("agentType") == "doctor":
                return True
    except (OSError, ValueError):
        pass
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = fh.read(20000)
        if "כאן דוקטור" in head or '"agentType":"doctor"' in head:
            return True
    except OSError:
        pass
    return os.path.getmtime(path) >= recent_cutoff  # still being written: the doctor running this script


def cost(a):
    total_in = a["input"] + a["write_5m"] + a["write_1h"] + a["read"]
    actual = a["input"] * W_INPUT + a["write_5m"] * W_WRITE_5M + a["write_1h"] * W_WRITE_1H + a["read"] * W_READ + a["output"] * W_OUTPUT
    baseline = total_in * W_INPUT + a["output"] * W_OUTPUT
    return total_in, actual, baseline


def pct(x, y):
    return round(100.0 * x / y, 1) if y else 0.0


def report(transcript, doctor_mode):
    main, doctor, other = empty(), empty(), empty()
    extra = {"compactions": 0, "tool_results": [], "max_context": 0, "models": {}}
    seen = set()
    scan(transcript, main, seen, extra)
    sub_files = sorted(glob.glob(os.path.join(transcript[: -len(".jsonl")], "subagents", "*.jsonl")))
    cutoff = time.time() - 120 if doctor_mode else float("inf")
    doctor_files = [f for f in sub_files if is_doctor(f, cutoff)]
    for f in sub_files:
        scan(f, doctor if f in doctor_files else other, seen, {"compactions": 0, "tool_results": [], "max_context": 0, "models": {}})

    total = empty()
    for part in (main, doctor, other):
        for k in total:
            total[k] += part[k]
    total_in, actual, baseline = cost(total)
    _, doc_actual, _ = cost(doctor)
    big = sorted(extra["tool_results"], reverse=True)
    return {
        "transcript": transcript,
        "saved_pct": pct(baseline - actual, baseline),
        "cache_hit_pct": pct(total["read"], total_in),
        "cost_units": round(actual),
        "cost_units_without_cache": round(baseline),
        "doctor_cost_units": round(doc_actual),
        "doctor_share_pct": pct(doc_actual, actual),
        "doctor_tokens": doctor,
        "main_tokens": main,
        "other_subagents_tokens": other,
        "subagent_runs": len(sub_files),
        "total_tokens": total,
        "thinking_share_of_output_pct": pct(total["thinking"], total["output"]),
        "cache_writes_1h_pct": pct(total["write_1h"], total["write_1h"] + total["write_5m"]),
        "max_context_tokens": extra["max_context"],
        "compactions": extra["compactions"],
        "tool_results_count": len(big),
        "largest_tool_results_chars": big[:5],
        "models": extra["models"],
        "note": "cost_units = uncached-input-token equivalents (input 1, cache write 1.25/2, cache read 0.1, output 5).",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript")
    ap.add_argument("--statusline", action="store_true")
    ap.add_argument("--doctor", action="store_true", help="count the subagent transcript being written now as the doctor's")
    args = ap.parse_args()

    transcript = args.transcript
    if args.statusline:
        try:
            transcript = transcript or json.load(sys.stdin).get("transcript_path")
        except ValueError:
            pass
    transcript = transcript or newest_transcript(os.getcwd())
    if not transcript or not os.path.exists(transcript):
        print("🩺 אין עדיין נתונים" if args.statusline else json.dumps({"error": "no transcript found"}))
        return

    r = report(transcript, args.doctor)
    if args.statusline:
        t = r["total_tokens"]
        print(f"🩺 חיסכון {r['saved_pct']}% · cache {r['cache_hit_pct']}% · ctx {r['max_context_tokens'] // 1000}k · out {t['output'] // 1000}k")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
