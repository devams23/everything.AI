# Exercise — Place 6 problems on the ladder (2026-11-09)

**Main lesson:** justify every step *up* ("why can't the simpler step below do it?"), not "why don't I need anything higher".

| | Problem | My answer | Correct | Key point |
|---|---|---|---|---|
| A | Invoice PDFs → vendor/date/total in a sheet | 3 | **2** | Count the LLM calls: one. The rest is code. A chain = several LLM calls in sequence. Guardrail = **output validation** + human review queue; PII redaction must not hide the vendor. |
| B | Nightly disk > 90% → email ops | 1 | **1** ✅ | No unstructured input, so no LLM. |
| C | Emails → billing / technical / sales | 4 | **4** ✅ | Paths are fixed, but *choosing* one is an LLM decision that can be wrong → add an "unclear → human" route. |
| D | Draft, check vs brand guide, revise until pass | 6 | **6** ✅ | Unknown number of revisions → loop + **max iterations**. Do code-checkable rules first. |
| E | "Why did signups drop?" | 7 | **7 → start at 8** ✅ | The path depends on findings. One agent with read-only tools; move to orchestrator-workers if parallel hypotheses help. Not multi-agent. |
| F | Reviews from 3 marketplaces → 1 report | 5 | **5** ✅ | Fetching is code, then 3 parallel summaries + 1 merge. Why not 2: only if there are too many reviews for one call. |
