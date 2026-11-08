"""Phase 1, step 2: the same agent as raw_loop, built with Google ADK.

REVIEW EXERCISE: an AI wrote this. It runs, but it contains 3 deliberate problems.
Find them yourself before asking for the answers.

Run:  python agent.py
"""
import asyncio
import os
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Finds the nearest .env, starting in this folder and walking up (so AI_Agents/.env also works).
load_dotenv(find_dotenv())

MODEL = os.getenv("MODEL", "gemini-3.5-flash-lite")
APP_NAME = "calc_app"
USER_ID = "user_1"
SESSION_ID = "session_1"


# Tools: ADK reads the type hints + docstring to build the schema you wrote by hand before.
def calculator(expression: str) -> dict:
    """Evaluate a math expression like '2*(3+4)' and return the result."""
    return {"result": eval(expression)}


def current_time() -> dict:
    """Get the current local time as HH:MM."""
    return {"result": datetime.now().strftime("%H:%M")}


root_agent = Agent(
    name="calc_agent",
    model=MODEL,
    instruction="You are a helpful assistant. Use the tools for math and time.",
    tools=[calculator, current_time],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


async def ask(user: str, question: str) -> str:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    if session is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )

    message = types.Content(role="user", parts=[types.Part(text=question)])
    async for event in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=message
    ):
        for call in event.get_function_calls():
            print(f"  [{user}] tool call: {call.name}({call.args})")
        if event.is_final_response() and event.content and event.content.parts:
            return event.content.parts[0].text
    return "(no answer)"


async def main():
    print("Alice:", await ask("alice", "Remember: my favourite number is 7. What is 7 * 6?"))
    print("Bob:  ", await ask("bob", "What is my favourite number?"))
    print("Bob:  ", await ask("bob", "Use the calculator to compute 10 / 0."))


if __name__ == "__main__":
    asyncio.run(main())
