# Pattern Catalog — the AI ladder

**Rule:** start at the bottom. Climb a rung only when you can say why the one below fails.
**Always:** code does maths, checks and decisions; the LLM reads and writes messy text; a human approves anything risky.

| # | Pattern | Use when | Why not the rung below | Watch out for |
|---|---|---|---|---|
| 1 | **Plain code** | Input is structured, rules are known | — | Using an LLM for SQL-shaped work (weekly sales report = SQL + cron) |
| 2 | **One LLM call** | Unstructured input, one step (extract, classify, summarize) | Code can't read messy text | Validate the output in code; route failures to a human |
| 3 | **Chain** | Fixed steps, each needs an LLM, with a checkpoint between them | One call can't be checked mid-way, or one step must not see the other's input (blind CV scoring) | Each step trusts the one before it → check every step, not just the last (extractor got years wrong) |
| 4 | **Routing** | Inputs of different kinds need different handlers | One prompt for every case gets weak and bloated | Self-reported confidence is uncalibrated (always 1.00) → explicit `unclear` → human; route in **code** |
| 5 | **Parallel** | Independent subtasks known in advance | Sequential is slower (time = slowest, not the sum) | Merging loses details with no slot in the output; never depend on finish order |
| 6 | **Evaluator-optimizer** | Output must meet checkable criteria; revisions needed | One pass doesn't reliably meet the bar | Max rounds; code checks before the LLM judge; the judge must quote evidence; a loop can't fix a missing fact or a bad brief |
| 7 | **Orchestrator-workers** | Subtasks are decided at runtime (which competitors, what to research) | Parallel needs the subtasks known up front | Workers invent facts → every claim needs a source |
| 8 | **Autonomous agent** | The next step depends on the last result (debug a failing test) | Steps can't be planned in advance | Loop limits (calls, time, cost), sandbox, minimal tools, guard against "cheating" (editing tests) |
| 9 | **Multi-agent** | Work must be **isolated**: different owners, permissions, data (insurance claims) | One agent would hold every permission and all the data | Use it for isolation, not because "more agents = smarter"; a human before high-stakes decisions |

## Cross-cutting lessons
- **Instructions can plant facts:** "mention the injection" → the model invents one. Write conditions ("*if* …").
- **Feedback can backfire:** "remove the placeholder" → it filled one with a made-up code.
- **Untrusted input is DATA:** emails, reviews, CVs, MCP tool descriptions → limit what the model can do, don't rely on the prompt.
- **Tools:** own Python function = full control; MCP = reuse/share across clients, but it's third-party code with your permissions → pin versions, filter tools, limit access.
- **Sessions:** a fresh session per independent task; state isn't sent to the model, only `{keys}` named in an instruction plus the event history.
