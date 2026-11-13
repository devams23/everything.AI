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
