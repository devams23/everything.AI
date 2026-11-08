# Phase 1 Notes — What an agent is (in my own words)

_Written 2026-11-08 after building `experiments/raw_loop` and `experiments/adk_same_agent`._

## 1. What is an agent?
An agent is a series of LLM calls until the goal is reached, and that is decided by the LLM. We can pass tools to perform actions if the goal needs it and send results back and forth. In this way the LLM guides the path, and the agent orchestrates it: calling the model, passing the response/error back, until it completes the task.

> **Review note:** the model *decides* the next step; the code *executes* it and *enforces limits*. "Done" means the model thinks it's done, or a limit stopped it.
> Tighter: *an LLM in a loop — the model picks the next action, the code runs it and feeds the result back, until the model answers or a limit stops it.*
> Workflow vs agent: in a workflow the **code** decides the path; in an agent the **model** does.

## 2. raw_loop vs ADK — where things live
| | raw_loop | ADK |
|---|---|---|
| **The loop** | A simple `for` loop over a range; I have to write and orchestrate it | Inside `run_async()`; each event is one step of the loop (a function call, a tool response, a model reply) |
| **Tool schemas** | A separate dict, passed in the config | Generated automatically from the function's name, type hints and docstring |
| **History** | A separate list I maintain | Managed by `run_async` in the session; the `session_id` keeps it unique, and it can be per user |

> **Review notes:**
> - ADK tool schemas are **not stored in the session**. They're rebuilt and sent to the model on every model call. The session holds only events + state.
> - **The docstring is the tool's prompt.** A vague docstring means the tool gets used wrongly.
> - Session uniqueness comes from the combination **(app_name, user_id, session_id)**. `InMemorySessionService` is lost on restart; production uses a database-backed one.

## 3. Three ways the agent broke in production, and the fixes
<!-- TODO: fill in -->
1.
2.
3.

## 4. What surprised me
- How the per-user part is managed in the session service, even when the `session_id` is the same.
- How much `run_async` abstracts. It feels easy to use, but only after understanding the internal flow.
- Callbacks: we can trace the calls, which is really helpful.
- Overall, the agent loop itself is surprising.

> **Review notes:** same `session_id` + different `user_id` = different session, because the key is the full combination. We used `before_tool`/`after_tool`; `before_model`/`after_model` work the same way around each model call. Together they're DIY tracing (Phase 4 tools do this for you).
