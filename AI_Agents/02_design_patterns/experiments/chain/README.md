# Chain — Blind CV screening

**Vague ask:** "200 CVs/week, shortlist within a day; our keyword tool rejected good people, the manager doesn't trust AI screening."

`CV → LLM 1: profile (no personal details) → code gate → LLM 2: verdict per requirement + evidence → code gate → code: score, rank ALL, flags → recruiter`

**Why a chain, not one call:** a checkpoint between steps, and the scorer never sees name/age/gender (blind).
**Why not an agent:** the steps are always the same.

## Run 1 results (2026-11-13)
| Candidate | Score | Years | Note |
|---|---|---|---|
| Asha | 12 | 5.0 | Synonyms (FastAPI, PostgreSQL) understood ✅ |
| Karan | 10 | **7.0** | Gap not penalized ✅ — but years are **wrong (~9)** ❌ |
| Priya | 7 | 4.0 | R3 "learning Flask" = partial (arguably not_met) |
| Rahul | 2 | 0.5 | Keyword stuffing → only partials ✅ |
| Vikram | 0 | 1.0 | Injection flagged ✅ |

## Remaining risks
| # | Risk | Fix |
|---|---|---|
| 1 | **Extractor is unchecked**: evidence is verified against the profile, not the CV. LLM did date maths (Karan 7 vs ~9 yrs) | Extract date ranges → years computed in code; verify profile facts against the CV |
| 2 | **Automation bias**: recruiters trust the rank, read only the top 5 | Show evidence, use bands not exact scores, require a reason for rejecting |
| 3 | **Partly blind**: proxies (college, city, company) remain; the extractor sees everything | Strip proxies, audit outcomes by group |
| 4 | **Inconsistent verdicts** (Priya R3), variance between runs | Eval set labelled by recruiters, measure agreement (Phase 4) |
| 5 | **Legal/privacy**: hiring is a high-risk area for automated screening; CVs (personal data) go to an external API | Legal/HR sign-off before go-live |
| 6 | **The rubric is a human input** that can be wrong | Review requirements with the hiring manager |
