# Phase 4 — Production

**Goal:** close the gap between a demo and a product. Most agent projects die here, and most of the real engineering value is here.

## Topics
1. **Evals (the most important topic)**: golden datasets, assertion checks, LLM-as-judge (and how to calibrate it against human labels), trajectory/tool-use evals, regression suites in CI.
2. **Observability**: tracing every model and tool call (OpenTelemetry; Langfuse / Phoenix / Cloud Trace), tokens and cost per request, replaying failures.
3. **Reliability**: retries with backoff, timeouts, idempotent tools, fallback models, graceful degradation.
4. **Safety & guardrails**: prompt injection, least-privilege tools, separating read from write, approval gates for irreversible actions, PII handling.
5. **Cost & latency budgets**: model tiering (small model for easy steps), prompt caching, streaming, caching results.
6. **Deployment**: serving an agent as an API, async jobs and queues for long tasks, config and prompt versioning, secrets.
7. **Rollout**: shadow mode → assistive → partial automation → full automation, with metrics deciding each step.

## SWE fundamentals that show up here
API design · async/concurrency · idempotency · queues · persisting agent state · the testing pyramid · containers · auth & secrets.

## Deliverables
- `eval_playbook.md`: how *I* build an eval set from zero for a new problem.
- `production_checklist.md`: the checklist I run before calling any agent "done".
- Evals and tracing added after the fact to Project 1.

## Exit criteria
- [ ] Every project has an eval suite I can run with one command, and I know its baseline score.
- [ ] I can show the trace of a failed run and explain the root cause.
- [ ] I can state my agent's cost per task and p95 latency.
