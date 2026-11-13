# Evaluator-optimizer — Ad copy vs brand guide (exercise D)

`brief → writer → code checks → LLM judge (only if code passed) → revise with feedback … max 3 rounds → human`

A plain Python loop (not `LoopAgent`) so the loop and its limit are visible.

## Run 1 results (2026-11-13)
Round 1 → **code** FAIL (76 words, best/guaranteed/ultimate, [placeholder], "!!"). Round 2 → **judge** FAIL (hype tone, invented code). Round 3 → **judge** FAIL (code still there) → **human**.

| # | Finding | Lesson | Fix |
|---|---|---|---|
| 1 | Writer replaced `[discount code]` with an **invented code `SAVE20`** | Feedback "remove the placeholder" → the model filled it with something made up. The judge (claims rule) caught it | Give real data, or tell it to drop missing info |
| 2 | `SAVE20` survived round 3 | The brief is resent every round and says "mention the discount code" → **brief vs feedback conflict, the brief wins** | Check the brief against the guide *before* the loop; send a bad brief back to its author |
| 3 | Escalated after 3 rounds | Correct outcome: a loop can't fix a **missing fact**. The limit worked | — |
| 4 | "Root node judge was cancelled by an external cancellation" | `return` inside `async for` left ADK's event stream open → cancelled at shutdown | Store the final text, let the stream finish (fixed) |
| — | 🚀 and "Crush your goals" passed the code checks | Checks are only as good as the written rules | Extend the guide / banned list |

## Review Q&A
- **Why code checks before the judge?** Cheaper + faster; **certain** (the judge can be wrong); the judge **focuses** on what only it can judge; code is **unit-testable**.
- **What catches "doubles your output" (no banned word)?** The judge's "only supported claims" rule.
