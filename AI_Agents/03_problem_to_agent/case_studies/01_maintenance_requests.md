# Case study 01 — Maintenance requests (UrbanNest Property Management)

**Verdict: an AI-assisted system, NOT an agent.** Rung 1 (shared tracker + automated messages) + small LLM jobs (rungs 2/4).

## 1. The ask vs the real problem
- **Ask:** "Build us an AI agent, live next month." (The CEO saw a demo.)
- **Real problem:** not volume (~60 requests/week, 400 flats, 3 coordinators). It's **lost requests + no visibility**:
  - WhatsApp (~70%) goes to coordinators' **personal phones**, email (~20%) to a shared inbox, calls + walk-ins aren't logged.
  - Google Sheet updated "when people remember". Photos live in phone galleries.
  - About half of incoming messages are **"any update??"** → a vicious circle.

## 2. Failures from the interview (what the design must fix)
| Failure | Cost |
|---|---|
| Burst pipe WhatsApped on a Saturday night, seen Monday | ₹3.5 lakh, a tenant moved out, insurance dispute (photos lost) |
| Tenant messaged two coordinators → **2 plumbers** sent | Double call-out fee |
| A coordinator left → her chats + ~15 open requests lost | Found weeks later via complaints |
| Cover staff ask the tenant to re-explain | 1-star review: "explained to 4 people" |
| **Constraint:** a ticketing tool failed 2 years ago (too many fields) | Coordinators went back to WhatsApp → **adoption is a requirement** |

## 3. Design
```
WhatsApp Business no. + shared inbox → system: phone no. → tenant/flat (code)
  → open request for this flat? → LLM: same issue? → attach / new request
  → LLM: classify (category, urgency) → emergency (or unsure) → call on-call → no ack in 10 min → backup → Meera
                                       → routine → queue + auto-acknowledgement
  → coordinator assigns vendor (human) → every status change → auto WhatsApp update (code)
  → "fixed?" → tenant confirms → close | "still broken" → reopen same request | no reply 3 days → auto-close
```
| Step | Label | Why |
|---|---|---|
| One shared number/inbox | **Process change** | Nothing can be automated while messages sit on personal phones |
| Identify tenant, find open requests | Code | Phone no. → flat lookup; don't rely on tenants remembering IDs |
| Same-issue check | LLM (only after code finds an open request for the flat) | "Ceiling dripping" = "leak from above" is fuzzy |
| Classify urgency | LLM + code routing | Unsure → emergency (asymmetric cost) |
| Emergency escalation | Code + on-call rota | Never depends on "whoever is online" |
| Vendor assignment | Human | Duplicates are solved by visibility, not automation |
| Status updates | Code | Removes "any update??" at the source |
| Handover context | LLM summary | Cover staff don't re-ask the tenant |
| Calls / walk-ins | Human logs, LLM turns the note into a request | Voice agent = rung creep (~6 calls/week, emergencies come by phone) |
| Photos / evidence | Code: stored by request ID, **server-side receipt time**, not deletable, access-restricted | Insurance + staff leaving |

**LLM jobs (4):** classify + extract · same-issue check · history summary · call note → request. Each needs its own eval.
**Later (phase 2):** bills/fees for audits, analytics.

## 4. Metrics (measure a baseline BEFORE launch)
- **Missed emergencies = 0**; message → on-call acknowledgement < 15 min
- "Any update?" messages ↓; duplicate vendor dispatches → 0; "re-explain" complaints ↓
- **Adoption:** % of requests that go through the system (the last tool died here)

## 5. Evals
- ~200 **real** past messages, labelled by Meera (incl. the burst-pipe message) + tricky cases: Hindi/English mix, understated ("small leak, no hurry 🙂"), overstated ("URGENT!!!" hinge), photo-only.
- Classifier: **emergency recall ≈ 100%** matters more than precision.
- Same-issue check: pairs of messages, same vs different issue.

## 6. Risks & guardrails
- Missed emergency → unsure = emergency, escalation chain, "for emergencies call X" in every acknowledgement.
- Low adoption → a few fields only, WhatsApp-like UI, coordinators involved in the design.
- Privacy → photos of homes restricted; tenant data stays in the system.

## 7. Rollout
1. **Day 1 (no AI risk):** shared number/inbox, one request list, auto-acknowledgement, lookup by phone, status updates, **on-call rota + escalation**.
2. **Shadow (~4 weeks):** LLM classifier labels everything, humans still decide → compare with the eval set + real outcomes.
3. **Assist:** LLM urgency + summaries go live, humans can override.
4. Automate more only where the metrics prove it.

## 8. Message for the CEO
"We're adding AI where it pays off: it reads every message 24/7 and flags emergencies within a minute. Nothing gets lost when someone is off or leaves, and tenants get automatic updates. We're deliberately not letting AI act on its own, because one mistake costs ₹3.5 lakh. We measure, then automate more where the numbers prove it's safe."

## Review notes (my learnings)
- Proposed a solution during the interview → ran into the hidden "adoption" constraint. **Interview first.**
- Asking about the **worst case** changed the design (uneven risk).
- "Notify whoever is active" = the original failure again. After-hours needs an **on-call rota**, a process.
- A voice agent was rung creep: justify every step up.
- Design so the question never gets asked (proactive updates) instead of answering it faster.
- Speak outcomes to a CEO, not architecture.
