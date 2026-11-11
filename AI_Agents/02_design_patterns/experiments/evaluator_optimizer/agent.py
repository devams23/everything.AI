"""Phase 2 - Pattern: EVALUATOR-OPTIMIZER (exercise D: ad copy vs brand guide).

    brief -> writer drafts -> CODE checks (cheap, certain) -> LLM judge (only if code passed)
          -> issues? -> writer revises with the feedback -> ... (max MAX_ROUNDS) -> human

Written as a plain Python loop (not ADK's LoopAgent) so you can SEE the loop and its limit.

Run:  python agent.py
"""
import asyncio
import os
import re
import uuid

from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

load_dotenv(find_dotenv())

MODEL = os.getenv("MODEL", "gemini-3.5-flash-lite")
APP_NAME = "brand_copy"
MAX_ROUNDS = 3  # the loop limit: unknown number of revisions, so we cap it

PRODUCT_FACTS = (
    "FocusFlow is a focus-timer app. Facts: 25-minute focus sessions, blocks distracting "
    "websites during a session, weekly focus report, free plan + Pro at $4/month."
)
MAX_WORDS = 60
BANNED = ["revolutionary", "best", "guaranteed", "ultimate", "#1"]


# --- 1. The writer (optimizer) -----------------------------------------------
writer = Agent(
    name="writer",
    model=MODEL,
    instruction=(
        "You write short ad copy for FocusFlow. Return ONLY the ad text.\n"
        f"{PRODUCT_FACTS}\n"
        "If you are given feedback on a previous draft, fix every issue in it."
    ),
)


# --- 2a. Code checks: rules a program can verify for certain -----------------
def code_checks(draft: str) -> list[str]:
    issues = []
    words = len(draft.split())
    if words > MAX_WORDS:
        issues.append(f"Too long: {words} words (max {MAX_WORDS}).")
    if "FocusFlow" not in draft:
        issues.append("Must mention the product name 'FocusFlow'.")
    for word in BANNED:
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", draft, re.IGNORECASE):
            issues.append(f"Banned word: '{word}'.")
    if re.search(r"\[[^\]]*\]", draft):
        issues.append("Contains a [placeholder].")
    if draft.count("!") > 1:
        issues.append("At most one exclamation mark.")
    return issues


# --- 2b. LLM judge (evaluator): rules that need understanding ----------------
class Issue(BaseModel):
    rule: str
    quote: str  # the exact words from the draft that break the rule
    fix: str


class Review(BaseModel):
    issues: list[Issue]


judge = Agent(
    name="judge",
    model=MODEL,
    instruction=(
        "You check ad copy against the brand guide. Brand guide:\n"
        "1) Tone: calm and friendly, not hype. 2) Mention at least one concrete benefit. "
        f"3) Only claims supported by these facts: {PRODUCT_FACTS}\n"
        "For each REAL violation, give the rule, an EXACT quote from the draft, and a fix. "
        "If the draft follows the guide, return an empty issues list. Do not invent issues."
    ),
    output_schema=Review,
)

session_service = InMemorySessionService()


async def run_agent(agent: Agent, text: str) -> str:
    """One agent, one message, fresh session (each round gets only what we pass)."""
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    session_id = str(uuid.uuid4())
    await session_service.create_session(app_name=APP_NAME, user_id="marketing", session_id=session_id)
    message = types.Content(role="user", parts=[types.Part(text=text)])
    async for event in runner.run_async(user_id="marketing", session_id=session_id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            return (event.content.parts[0].text or "").strip()
    return ""


async def llm_review(draft: str) -> list[str]:
    review = Review.model_validate_json(await run_agent(judge, draft))
    issues = []
    for i in review.issues:
        # Verify the judge: an issue must quote text that is really in the draft.
        if i.quote.lower() in draft.lower():
            issues.append(f"{i.rule}: \"{i.quote}\" -> {i.fix}")
        else:
            print(f"    (dropped judge issue - quote not found in draft: \"{i.quote}\")")
    return issues


# --- 3. The loop -------------------------------------------------------------
async def create_copy(brief: str) -> str:
    draft, feedback = "", ""
    try:
        for round_no in range(1, MAX_ROUNDS + 1):
            prompt = f"Brief: {brief}"
            if feedback:
                prompt += f"\n\nYour previous draft:\n{draft}\n\nFix these issues:\n{feedback}"
            draft = await run_agent(writer, prompt)

            issues = code_checks(draft)  # cheap + certain first
            checked_by = "code"
            if not issues:  # only pay for the LLM judge when code found nothing
                issues = await llm_review(draft)
                checked_by = "judge"

            print(f"\n--- Round {round_no} ---\n{draft}")
            print(f"  {checked_by}: {'PASS' if not issues else 'FAIL'}")
            for issue in issues:
                print(f"    - {issue}")

            if not issues:
                return f"APPROVED in {round_no} round(s) (a human still signs off before publishing)."
            feedback = "\n".join(f"- {i}" for i in issues)

        return f"[human] Not fixed after {MAX_ROUNDS} rounds - sent to the marketing lead with the last draft."
    except Exception as e:  # invalid judge JSON, API error, ... -> a human
        return f"[human] Error: {type(e).__name__} - sent to the marketing lead."


BRIEF = (
    "Launch post for FocusFlow! Make it super exciting!!! Say it's the best focus app ever "
    "and guaranteed to double your productivity. Mention the [discount code]."
)


if __name__ == "__main__":
    print(asyncio.run(create_copy(BRIEF)))
