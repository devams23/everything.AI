# Roadmap — From "I know ADK" to "I turn business problems into shipped agents"

## The target (one sentence)
> Be the person who can take a vague business problem, decide **whether** and **how** AI agents should solve it, build it on any framework, **prove** it works with evals, and run it safely in production.

That's an **Applied AI / Agent Engineer** with a solution-architect mindset. Coding the agent is maybe 20% of the job. The other 80% is problem framing, system design, evaluation and reliability, and those are the parts that last.

## Where you are now
| Already have | Gap to close |
|---|---|
| How LLMs work, sampling params (temperature, top-p/k, max tokens) | What happens *inside* the agent loop, and context engineering |
| ADK: LLM agents, workflow agents (sequential/parallel/loop), nesting, retries, timeouts | Choosing a pattern on purpose; knowing when **not** to use an agent |
| Built RAG + API projects in this repo | Evals, observability and safety for agents that *act* |
| — | **Business problem → agent design** (the core skill) |

## Principles for this roadmap
1. **Framework-agnostic on purpose.** ADK is your workbench, but every concept is learned as "loop / tools / state / control flow" so it carries over to LangGraph, the OpenAI/Claude Agent SDKs, or whatever comes next.
2. **Don't write everything from scratch.** Write the agent loop by hand exactly once (Phase 1) so you understand it. After that, use frameworks and AI coding assistants freely. Your value is judgment, not typing.
3. **Design before code.** Every project starts with a filled-in design doc (`03_problem_to_agent/templates/solution_design.md`).
4. **No eval, no done.** If you can't measure it, you can't claim it works.
5. **Learn SWE fundamentals in context.** Each phase lists the engineering fundamentals it exercises, so you learn them where they matter instead of in a vacuum.

---

## Phases
Time estimates assume about 8–10 hours/week. Phases 3 and 5 overlap: you practise design while you build.

### Phase 1 — Agent foundations (weeks 1–2) → `01_agent_foundations/`
- The agent loop, tool calling, context engineering, memory, planning/stopping, structured output.
- **Build:** a raw agent loop of ~100 lines with no framework → the same agent in ADK → write up the difference.
- **SWE fundamentals:** typed data models (Pydantic), error handling, writing clean, small functions with tests.

### Phase 2 — Design patterns (weeks 3–4) → `02_design_patterns/`
- The autonomy ladder: code → single call → chain → routing → parallel → evaluator-optimizer → orchestrator-workers → autonomous → multi-agent.
- MCP and A2A, human-in-the-loop placement, failure modes per pattern.
- **Build:** `pattern_catalog.md` + 4 small runnable pattern examples in ADK.
- **SWE fundamentals:** async/concurrency (parallel agents), timeouts & retries done properly, interface design.

### Phase 3 — Problem → Agent (weeks 4–8, then ongoing) → `03_problem_to_agent/`
**The main skill. Spend the most time here.**
- Learn the framework in `framework.md`: outcome → current process → step classification → simplest architecture → tools & permissions → evals → risks → rollout.
- **Practice:** 6+ case studies on vague briefs from different domains (support, sales, finance ops, HR, internal knowledge, engineering). At least 2 should end with "not an agent".
- **SWE fundamentals:** requirements gathering, writing design docs, estimating cost, thinking in trade-offs.

### Phase 4 — Production (weeks 6–10, alongside projects) → `04_production/`
- Evals (golden sets, LLM-as-judge, trajectory evals), tracing, reliability, guardrails & prompt injection, cost/latency budgets, deployment, staged rollout.
- **Build:** `eval_playbook.md`, `production_checklist.md`, and evals + tracing added to Project 1.
- **SWE fundamentals:** testing in CI, observability, idempotency, queues, containers, secrets, API design.

### Phase 5 — Projects (ongoing from week 3) → `05_projects/`
Each project starts from a **vague brief** and goes through the full method. The difficulty rises along one axis at a time.

| # | Project | Vague brief | Key skills it forces |
|---|---|---|---|
| P1 | **Support triage & draft replies** | "Our support team is drowning in tickets." | Routing, structured output, RAG over a knowledge base, human approves before sending, first eval set |
| P2 | **Research / analyst agent** | "Leadership wants a weekly competitor briefing, and it takes an analyst 2 days." | Orchestrator-workers, parallel research, citations & grounding, LLM-as-judge evals, cost control |
| P3 | **Ops agent with real side effects** | "Finance spends too long processing invoices and chasing mismatches." | Write-tools (creating records, sending emails), idempotency, approval gates, audit log, your own MCP server, prompt-injection defence |
| P4 | **Capstone: end-to-end, deployed** | Pick a real problem (your job, a friend's business, an open dataset). | Discovery interview → design doc → build → evals → deploy as a service → shadow-mode rollout → postmortem |

Optional stretch work once P1–P3 are done: a multi-agent version of P2 measured against the single-agent baseline (did it actually help?), or a voice/real-time agent.

---

## Milestones (how you know you're on track)
- **End of week 2:** you can explain any agent framework as loop/tools/state/control flow.
- **End of week 4:** you can look at a problem and say "this is a routing workflow, not an agent", with reasons.
- **End of week 8:** 6 case studies plus P1 shipped with an eval suite.
- **End of week 12:** P2 and P3 done; you can show traces, eval scores, cost per task and p95 latency for each.
- **Week 16+:** the capstone is deployed, and you have a portfolio of design docs and working systems to talk through in interviews.

## Reading list (primary sources, not blog spam)
- Anthropic, *Building Effective Agents*: the workflow-vs-agent taxonomy this roadmap uses.
- Anthropic, *Effective context engineering for AI agents* and *Writing tools for agents*.
- Google ADK docs: agents, workflow agents, callbacks, evaluation, deployment.
- OpenAI, *A practical guide to building agents*.
- The MCP specification (modelcontextprotocol.io) and the A2A protocol docs.
- Hamel Husain / Shreya Shankar on LLM evals: error analysis first, metrics second.
- Chip Huyen, *AI Engineering* (book): the production and evaluation chapters.

## How to use this folder
1. Tick items off in [`progress.md`](progress.md) as you go.
2. Write a journal entry (`journal/YYYY-MM-DD-topic.md`) after each session.
3. Commit after each meaningful step.
4. Re-read [`market_reality.md`](market_reality.md) every couple of months and adjust. The field moves fast, and so should this plan.
