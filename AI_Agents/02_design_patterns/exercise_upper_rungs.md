# Exercise — The upper rungs (7, 8, 9)

Reminder:
- **7 Orchestrator-workers:** an LLM *plans* subtasks at runtime → workers do them → combine. The subtasks aren't known in advance.
- **8 Autonomous agent:** one agent + tools in a loop; the model chooses each next step.
- **9 Multi-agent:** several agents with their **own** role, tools, permissions or context that hand work to each other.

For each problem: **rung**, **why not the rung below**, **one guardrail**. (One of them is a trap.)

| | Problem | Rung | Why not lower | Guardrail |
|---|---|---|---|---|
| G | "Resolve refund requests end to end: look up the order, check the policy, refund up to ₹2,000, reply to the customer." | | | |
| H | "Before each board meeting the CFO wants a brief on whichever 3–8 competitors matter this quarter: news, pricing changes, hiring, launches." | | | |
| I | "When a test fails in CI, an AI should read the failure, explore the code, edit, rerun the tests, and repeat until green." | | | |
| J | "Insurance claims pass through fraud check, medical review and payout. Each has a different team owner and different data-access rules." | | | |
| K | "Every Monday, a sales summary from the CRM for each of our 12 regions." | | | |

## My answers + review (2026-11-15)

| | My answer | Review | Key point |
|---|---|---|---|
| G | 8 | **Start at 3**, move to 8 only if cases are messy | Steps are mostly fixed → chain; LLM reads, **code** checks policy + amount. Guardrails: amount from the order record (not the customer), limit enforced **in the tool code**, never refund the same order twice, human above the limit, no PII in the prompt |
| H | 7 | ✅ | Why not 5: *which* competitors and *what* to research are decided at runtime. Guardrail: every claim has a source URL, code checks it |
| I | 8 | ✅ | Each step depends on the last. Biggest risk: **"make tests green" by editing/deleting tests** → agent can't touch tests, sandbox, round/cost limit, human reviews the PR |
| J | 9 | ✅ | Reason = separate permissions/owners/context. The order is fixed, so code passes the claim along → multi-agent for **isolation, not autonomy**. Human before denial/payout |
| K | none (trap) | ✅ → **rung 1** | Totals by region = SQL + cron. Add a parallel LLM summary (5) only if they want written commentary |

**Lesson:** upper rungs are for steps that can't be known in advance (7, 8) or work that must be isolated (9). Fixed steps go lower, even if they *sound* complex.
