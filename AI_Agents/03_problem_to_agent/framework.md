# The Problem → Agent Framework

A repeatable method for turning a vague business problem into an agentic solution design.
Run it **in order**. Most bad agent projects skip steps 1–3 and jump straight to "let's build a multi-agent system".

---

## Step 1 — Restate the problem as an outcome
Vague: *"Support is drowning."*
Restated: *"Cut median first-response time on tier-1 tickets from 9h to under 1h without lowering CSAT."*

Answer these:
- **Who** is in pain, and who pays for the fix?
- **What job** are they trying to get done?
- **What metric** moves if we succeed? What is it today?
- **What does "good enough" look like?** (Agents are rarely 100%. Is 80% automated plus 20% routed to a human a win?)

> If you can't name a metric, stop. You don't have a problem yet, just a wish.

## Step 2 — Map the current process (as-is)
Write the workflow as it runs today, step by step. For each step record:
- the **actor** (person/system), its **inputs**, **outputs**, and **decisions made**
- the **systems** touched (CRM, email, DB, spreadsheets…)
- **volume** (how many per day) and **time per item**
- where it **breaks** (errors, waiting, rework)

The bottleneck usually sits in 1–2 steps. Automating everything else adds little value.

## Step 3 — Classify every step
For each step, choose the *least* powerful tool that can do it:

| Step type | Signal | Solution |
|---|---|---|
| Deterministic | Clear rules, structured data | **Plain code** |
| Understanding / generation | Unstructured text in, a fixed output shape out | **Single LLM call** |
| Known multi-step path | The same steps every time | **Workflow** (chain / route / parallel) |
| Unknown path | The steps depend on what you find along the way | **Agent** |
| High stakes / ambiguous / needs accountability | Money, legal, reputation, irreversibility | **Human** (agent prepares, human decides) |

## Step 4 — Choose the simplest architecture that works
Use the autonomy ladder from `02_design_patterns/`. Write down:
- the chosen pattern, plus **why the rung below isn't enough**
- a diagram: inputs → steps → tools → outputs → where the human sits
- the model tier per step (a small, fast model for classifying; a strong model for reasoning)

## Step 5 — Define tools, data and permissions
For each tool:
- **Read or write?** Is a write reversible?
- **Blast radius** if the model calls it wrongly or gets prompt-injected
- **Idempotency**: is it safe to retry?
- **Auth**: whose credentials does the agent act with? Use least privilege.
- **Data**: where does the context come from (RAG, DB, APIs)? How fresh is it? Who may see it?

## Step 6 — Define evals *before* building
- **Success criteria** per step and end to end (accuracy, groundedness, the right tool chosen, task completed)
- **Eval set**: 30–100 real (or realistic) cases, including the nasty edge cases
- **How it's scored**: exact match / assertions / LLM-as-judge (calibrated against human labels) / human review
- **Baseline**: how good is today's process, or the dumbest possible solution?

## Step 7 — Risks & guardrails
- Failure modes: hallucination, wrong action, loops, stale data, injection, PII leaks
- Guardrails: input/output validation, approval gates, rate limits, spend caps, kill switch
- Compliance: logging, audit trail, data retention

## Step 8 — Cost, latency and ROI
- Estimated tokens per task × price × volume = monthly cost
- Latency budget (is it interactive or a batch job?)
- ROI: hours saved × cost per hour vs. build + run cost. **If the ROI is unclear, say so.**

## Step 9 — Rollout plan
1. **Shadow**: the agent runs, a human does the real work, you compare the two
2. **Assist**: the agent drafts, a human approves
3. **Partial automation**: high-confidence cases run automatically, the rest go to a human
4. **Full automation** (only if the metrics justify it)

Define the metric threshold that unlocks each stage.

---

## Smell tests
- "We need multi-agent" before steps 1–3 are written → 🚩
- No eval set → 🚩 you can't tell whether it works
- The agent has write access to production with no approval step → 🚩
- The whole process is deterministic → you don't need an LLM, just a script
- The volume is tiny (10/month) → automation may not pay back the build cost

## Questions to ask a stakeholder (discovery interview)
1. Walk me through the last time you did this, step by step.
2. Which part do you hate / takes longest / goes wrong most?
3. What happens when it goes wrong? Who notices, and what does it cost?
4. How do you know a result is "good"? Can you show me 5 good and 5 bad examples?
5. Which systems hold the data? Can we get access?
6. What must never happen? (This defines your guardrails.)
7. If this worked perfectly, what would you do with the time saved?
