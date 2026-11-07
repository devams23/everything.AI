# Phase 1 — Agent Foundations

**Goal:** demystify agents. After this, no framework (ADK, LangGraph, OpenAI Agents SDK, Claude Agent SDK…) should feel like magic. You should see each one as the same loop with different conveniences.

## Topics
1. **The agent loop**: model call → tool-call request → run the tool → feed the result back → repeat until a stop condition. That's it.
2. **Tool-calling mechanics**: JSON schemas, how the model "chooses" a tool, parallel tool calls, tool errors returned as observations.
3. **State & context engineering**: what goes into the context window each turn, why it bloats, summarisation/compaction, scratchpads. *This is the skill most people underrate.*
4. **Memory**: short-term (conversation), long-term (vector store/DB), and why most "memory" is just retrieval.
5. **Planning & stopping**: ReAct, plan-then-execute, max iterations, "done" criteria, why agents loop forever.
6. **Structured output**: forcing typed results (Pydantic) so downstream code can trust them.

## Deliverables
- `experiments/raw_loop/`: an agent loop of about 100 lines on a raw model SDK, with no framework and 2–3 tools. Build it **once**, to understand it. You won't use it in production.
- `experiments/adk_same_agent/`: the same agent in ADK. Write down what ADK gave you for free.
- `notes.md`: a one-page "an agent is…" explanation in your own words.

## Exit criteria
- [ ] I can draw the agent loop from memory and point to where retries, timeouts and stop conditions live.
- [ ] I can explain why an agent picked the wrong tool by reading the context it was given.
- [ ] I can map every ADK primitive I've used onto "loop / tool / state / control flow".
