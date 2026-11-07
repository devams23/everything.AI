# Phase 2 — Design Patterns

**Goal:** a mental catalogue of architectures and, more importantly, a reason to pick the *simplest* one that works.

## The autonomy ladder (simplest first)
1. **Plain code**: no LLM at all. Always check whether this is enough.
2. **Single LLM call**: classify / extract / summarise / draft.
3. **Prompt chain**: a fixed sequence of LLM calls (ADK `SequentialAgent`).
4. **Routing**: classify, then send to a specialised path.
5. **Parallelisation**: fan-out / fan-in, or voting (ADK `ParallelAgent`).
6. **Evaluator–optimizer**: generate, critique, revise (ADK `LoopAgent`).
7. **Orchestrator–workers**: a planner decides the sub-tasks at runtime.
8. **Autonomous agent**: the model controls the loop and tool choice end to end.
9. **Multi-agent system**: several agents with separate contexts and roles. Powerful, expensive and hard to debug.

Rule of thumb: **use a workflow when the path is known and an agent when it isn't.** Each step up the ladder has to buy you something you can measure.

## Topics
- The patterns above, with the cost/latency/reliability trade-offs of each.
- Interop protocols: **MCP** (agent ↔ tools/data) and **A2A** (agent ↔ agent).
- Where to put the human: approve, edit, or escalate.
- Failure modes per pattern (errors compounding in chains, runaway loops, context lost between agents).

## Deliverables
- `pattern_catalog.md`: one section per pattern covering when to use it, when NOT to, its ADK mapping, and one real-world example.
- `experiments/<pattern>/`: a small runnable example for at least 4 patterns.

## Exit criteria
- [ ] Given a problem, I can name 2 candidate patterns and argue why the simpler one wins (or doesn't).
- [ ] I can explain when multi-agent is worth it compared with one agent that has more tools.
