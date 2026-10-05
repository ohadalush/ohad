# Doctor playbook

Shared knowledge base for the `doctor` and `super-doctor` agents.

**Context hygiene**
- Peak context >100k, or many turns on mixed topics → `/clear` between unrelated tasks; `/compact <what to keep>` (e.g. `/compact keep API decisions and failing test names`) before switching phases. Use `/context` to see what fills the window.
- Large tool results (>20k chars) → read files with line ranges, use Grep/Glob instead of `cat`/`find` dumps, pipe noisy commands through `| tail -50` / `| head`, run tests with quiet/fail-only flags.
- Repeated compactions → work was too long in one thread; split tasks, delegate exploration to subagents.

**Prompt cache**
- Cache hit <70% → something mid-session busts the prefix: editing CLAUDE.md, toggling MCP servers/tools, switching model or effort mid-thread, or long idle gaps. Hierarchy: tools → system → messages; a change invalidates its level and everything after.
- `cache_writes_1h_pct` high with fast back-to-back turns is fine in Claude Code (it manages TTL); in your own API apps prefer 5m TTL unless pauses of 5–60 min are common.
- Keep static content first and stable; put volatile content last.

**Base context (paid on every request)**
- CLAUDE.md >~8 KB → trim to essentials (build/test commands, conventions, gotchas). Move niche procedures into Skills (`.claude/skills/<name>/SKILL.md`, loaded on demand) or `@path` imports used only where relevant.
- Many MCP servers → every tool definition costs tokens; disable servers not used in this project (`/mcp`), prefer narrowly-scoped ones.
- Too many custom agents/skills with long descriptions → shorten descriptions; descriptions are always loaded, bodies are not.

**Model and thinking**
- Opus for routine edits/searches → `/model` to Sonnet for implementation, Haiku-class for trivial tasks; reserve Opus for architecture and hard debugging. Subagents can pin a cheaper `model:` in their frontmatter.
- Thinking share >60% on simple tasks → lower effort for routine work; state the task precisely so the model does not deliberate.

**Delegation (4D: Delegation, Description, Discernment, Diligence)**
- Broad searches in the main thread → delegate to an `Explore`/custom subagent; only its summary returns. But each subagent starts cold and rebuilds context: many subagent runs for small tasks cost more than doing them inline.
- Vague prompts causing correction rounds → give file paths, expected behavior, constraints and a done-criterion up front; use plan mode (Shift+Tab) for multi-file changes so mistakes are caught before tokens are spent implementing them.
- Demand evidence (test output, diffs) rather than accepting "done"; failed attempts bloat context, so `Esc Esc` to rewind instead of arguing the model out of a wrong path.

**Diligence**
- Permission prompts slowing work → allowlist safe read-only commands in `.claude/settings.json` (or `/fewer-permission-prompts`); keep destructive commands gated.
- Images/screenshots: downscale (<2000 px), and avoid pasting many; each one is re-sent every turn until compacted.
- Batch/offline API workloads → Message Batches (≈50% cheaper) + caching with a shared prefix.

## Safe treatments (what an agent may change, with approval or in super-doctor mode)

All are project-level, reversible and quality-neutral. Never touch `~/.claude/` unless the user asks.

| Treatment | How | Takes effect |
|---|---|---|
| Block reads of bulky generated paths | `.claude/settings.json` → `permissions.deny`: `Read(./node_modules/**)`, `Read(./dist/**)`, `Read(./build/**)`, `Read(./.venv/**)`, `Read(./**/*.min.js)`, lockfiles — only paths that exist | next session |
| Allowlist safe read-only commands | `permissions.allow`: e.g. `Bash(git status)`, `Bash(git diff:*)`, `Bash(git log:*)`, `Bash(ls:*)`, the project's test/lint commands | next session |
| Disable unused project MCP servers | `disabledMcpjsonServers: ["name"]` for servers in `.mcp.json` the task won't use | next session |
| Slim CLAUDE.md (>8 KB) | Move niche sections verbatim into `.claude/skills/<topic>/SKILL.md` (with a `description:` saying when to load it); leave build/test commands, conventions, gotchas. Lossless: nothing is deleted. | next session |
| Default model | `model` in `.claude/settings.json`: `sonnet` for routine work, `opusplan` (Opus plans, Sonnet executes) for complex work. Never downgrade below what the task needs. | next session |

Before changing any file: copy it to `.claude/doctor/backups/<YYYYmmdd-HHMMSS>/<same relative path>` (note "new file" if it did not exist) and append one line per change to `.claude/doctor/changes.log`. Undo = copy the backup back, or delete files marked new.
