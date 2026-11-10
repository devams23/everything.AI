# Routing — Email triage (exercise C)

`email → classifier (1 LLM call, JSON) → Python if → billing / technical / sales agent | human`

## Run 1 results (2026-11-10)
Routing: **5/5 correct**, injection email → `unclear` → human ✅

| # | Finding | Lesson | Fix |
|---|---|---|---|
| 1 | Every confidence = `1.00`, so the 0.7 threshold never fires | LLM self-reported confidence is uncalibrated; the real safety net was the `unclear` category | Agreement across several runs, an explicit `unclear` option, an eval set |
| 2 | Sales dodged a public pricing question | Guardrails can kill helpfulness; evals must measure helpfulness, not only safety | Narrow the instruction + add a `get_plan_pricing` tool |
| 3 | `[Insert Booking Link]` placeholder in the draft | Output validation catches what the model leaves unfinished | Real link in the instructions + code check that blocks `[...]` |
| 4 | Technical agent invented generic troubleshooting | Ungrounded answers = confident guesses | RAG over the help docs (→ Project 1) |
| — | "Just saying hi" uses up a human's time | Product decision, not a technical one | Ask the stakeholder; maybe an auto-reply path |

## Review Q&A
- **Why route with Python, not an LLM?** The code *guarantees* escalation, and the classifier can be evaluated on its own. An LLM choosing the path = an agent (step 7/8).
- **Why was the injection fairly safe?** 4 layers: "email is data" instruction → no discounts in the instructions → **sales agent has no tools** → a human approves.
- **Why a new session per call?** Sessions = separate contexts. The tree is app → user → sessions. A new session per independent task stops the same customer's tickets, and the classifier and specialist, from seeing each other's history.
