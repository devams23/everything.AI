# Case study 02 — Sales call research (LedgerLite)

**Verdict: a workflow, NOT an agent.** Parallel fetch (rung 5) → a checked chain (rung 3). Day 1 is code only.

## 1. The ask vs the real problem
- **Stakeholder:** Arjun, Head of Sales, LedgerLite (B2B accounting software). 8 reps × ~4 discovery calls/day.
- **Ask:** "AI to research prospects before calls."
- **Real problem:** research takes 30–45 min → half the reps skip it → they walk in blind. **Research only, no AI outreach** (no bot emailing a CFO).
- Calls are booked 2–5 days ahead, but **~20% are same-day** hot leads ("talk in an hour") → an overnight batch is not enough.

## 2. Failures from the interview
| Failure | Root cause | Data source |
|---|---|---|
| Pitched an **ex-customer** (churned 6 months ago after a billing dispute) → CFO ended the call, lost for good | Sales never checks support | **Zendesk (internal)** |
| Enterprise plan pitched to a 12-person startup | Didn't know their size | Crunchbase |
| ChatGPT invented a **Series B**; the rep congratulated them | Hallucination, no source | Web |

The costliest failure came from **internal** data, not the web. The hallucination is why Arjun is nervous about AI.

## 3. The brief (one screen, read 5 min before the call)
🔴 **Banner: ex-customer / lost deal / open dispute** (if any) → 1) what they do + size → 2) current tool (Tally/Zoho/Excel/competitor, **most important**) → 3) our history → 4) who's on the call → 5) recent trigger (funding, new CFO) → 6) 2–3 opening questions.
Each section: 3–4 bullets / ≤50 words. Every external claim has a **source link**; unsourced or unconfirmed claims are flagged.

## 4. Design
```
calendar event / HubSpot booking → [parallel fetch, code]
   HubSpot (deals, calls, notes) · Zendesk (account, tickets) · Crunchbase (size, funding) · web pages
 → code: ex-customer / dispute check → red banner
 → LLM: extract claims + quotes from messy notes and web pages
 → code: is each quote really in the fetched source? no → drop the claim
 → LLM: write the brief from the CHECKED facts only (word limits)
 → code: length checks → HubSpot record + calendar invite link (+ Slack ping for same-day calls)
```
| Step | Label | Why |
|---|---|---|
| Fetch the 4 sources | Code, parallel | Independent and known in advance |
| Ex-customer / dispute check | **Code** | A database lookup, and the costliest failure → never leave it to a summary |
| Size, funding | Code (Crunchbase = source of truth) | Not an LLM web search |
| Messy notes / web → claims | LLM extract **with quotes** | Messy text |
| Verify the claims | **Code: quote ∈ source** | A critic loop or a second search can hallucinate too; a loop can't fix a missing fact |
| Write the brief + questions | LLM, checked facts only | Writing |
| LinkedIn attendee background | **Human (manual)** until legal OKs automation | ToS / legal question mark |
| Delivery | HubSpot + calendar link + Slack | **No new tool**: adoption |

**Not an agent:** nothing needs the model to choose its next step.

## 5. Metrics (baseline first)
- **Adoption:** % of calls with the brief opened beforehand (calendar link clicks)
- **Ex-customers pitched blind = 0**; wrong-plan pitches ↓
- **Wrong facts reaching reps = 0** ("this is wrong" button on each claim)
- Research time: 30–45 min → ~0; same-day brief ready in < 10 min
- Readable in < 5 min; the banner is seen (usability)
- Business: discovery → next-stage conversion

## 6. Evals (~30 past companies with known truth)
- Ex-customers (incl. the billing dispute) → banner present: **100%**
- 12-person startup → correct size
- No web presence → "not found", nothing invented
- Two companies with the same name → not mixed up
- A page with an injection → treated as data
- Every case: each claim has a source + the quote is in it (code), and section length is within limits
- Evals ≠ unit tests: they check **properties** and give a **pass rate** across runs; the LLM is the thing under test. Code parts (lookups) get normal unit tests.

## 7. Rollout
1. **Day 1 (code only):** banner, HubSpot history, Crunchbase size/funding, attendees → already fixes **2 of the 3 failures**.
2. **Shadow (2–4 weeks):** the LLM sections are generated but hidden; run evals; 1–2 reps compare with their own research.
3. **Assist:** "AI-drafted, check the sources" sections → 2 reps first, then everyone.
4. **Expand** only while wrong facts stay at ~0. **Kill switch** → back to the code-only brief.

## 8. Message for Arjun
"From day one, every brief shows in red if they were ever our customer, with their real size from Crunchbase. That stops 2 of your 3 disasters, and there's no AI in it. AI comes later, only after passing tests on 30 past companies. Every AI fact shows its source, and if there's no source it doesn't appear. If it ever gets something wrong, we switch it off in one click."

## Review notes (my learnings)
- Proposed a **critic loop + web search** to verify → a second LLM can be wrong too. **Code verifies quotes against sources.**
- The worst failure was internal data, so a deterministic check fixed most of the risk.
- Ask **where people already work** (HubSpot, calendar) before building a screen.
- Evals = property checks + pass rates, not exact-match unit tests.
- Metrics need adoption + outcome, not only usability.
- To a stakeholder: speak in what users will experience, not in checks and flags.
