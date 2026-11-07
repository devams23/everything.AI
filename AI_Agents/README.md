# AI Agents — Learning Track

Goal: get from "I know how LLMs and ADK work" to **"give me a vague business problem and I'll ship a reliable agentic solution for it."**

Start here → [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)

## Layout

| Folder | What lives here | Phase |
|---|---|---|
| `roadmap/` | The plan, the honest market take, the progress tracker | — |
| `01_agent_foundations/` | How agents actually work under the hood (loop, tools, state, context) | 1 |
| `02_design_patterns/` | Workflow vs agent patterns, when to use which, multi-agent trade-offs | 2 |
| `03_problem_to_agent/` | **The core skill:** turning business problems into agent designs | 3 |
| `04_production/` | Evals, observability, guardrails, cost, deployment | 4 |
| `05_projects/` | End-to-end builds, one folder per project (copy `_template/`) | 5 |
| `journal/` | Dated learning notes: `YYYY-MM-DD-topic.md` | ongoing |

## Conventions (keep it maintainable)

- **One concept → one folder or one file.** Don't pile notes into one giant doc.
- Every phase folder has a `README.md` with: goal, topics, deliverables, exit criteria.
- Code experiments go in `<phase>/experiments/<short-name>/` with their own `README.md` and `requirements.txt` (or `pyproject.toml`).
- Projects are self-contained: each one can be copied out and run on its own.
- Secrets never get committed. Use `.env` + `.env.example`.
- Commit small and often: `docs(agents): ...`, `feat(agents/p1): ...`, `notes(agents): ...`.
