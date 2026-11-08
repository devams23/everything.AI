"""Phase 1, step 2: the same agent as raw_loop, built with Google ADK.

Started as a review exercise with 3 deliberate problems (see git history for the original).
Fixed:
  1. Session leak   -> sessions keyed by the real user, not hardcoded IDs.
  2. Crash on tool error -> tools return {"status": "error", ...} so the model can recover,
                            and ask() catches anything unexpected at the request boundary.
  3. eval()         -> allow-list AST calculator: numbers and + - * / only.

Run:  python agent.py
"""
import ast
import asyncio
import operator
import os
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Finds the nearest .env, starting in this folder and walking up (so AI_Agents/.env also works).
load_dotenv(find_dotenv())

MODEL = os.getenv("MODEL", "gemini-2.5-flash")
APP_NAME = "calc_app"

# --- Tools -------------------------------------------------------------------
# ADK reads the type hints + docstring to build the schema you wrote by hand before.
# Convention: return a dict with "status", and NEVER raise. An error the model can
# read is a chance to recover; an exception kills the whole run.

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Only numbers and + - * / are allowed")


def calculator(expression: str) -> dict:
    """Evaluate an arithmetic expression like '2*(3+4)'. Supports + - * / and parentheses."""
    try:
        result = _safe_eval(ast.parse(expression, mode="eval").body)
        return {"status": "success", "result": result}
    except ZeroDivisionError:
        return {"status": "error", "error_message": "Division by zero is undefined."}
    except (ValueError, SyntaxError) as e:
        return {"status": "error", "error_message": f"Invalid expression: {e}"}


def current_time() -> dict:
    """Get the current local time as HH:MM."""
    return {"status": "success", "result": datetime.now().strftime("%H:%M")}


root_agent = Agent(
    name="calc_agent",
    model=MODEL,
    instruction=(
        "You are a helpful assistant. Use the tools for math and time. "
        "If a tool returns status 'error', explain the problem to the user "
        "or fix the input and try again."
    ),
    tools=[calculator, current_time],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


async def ask(user_id: str, question: str, session_id: str = "default") -> str:
    # In a real app user_id comes from authentication (a login token),
    # never from something the client can type, or anyone can claim to be anyone.
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    message = types.Content(role="user", parts=[types.Part(text=question)])
    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=message
        ):
            for call in event.get_function_calls():
                print(f"  [{user_id}] tool call: {call.name}({call.args})")
            for resp in event.get_function_responses():
                print(f"  [{user_id}] tool result: {resp.response}")
            if event.is_final_response() and event.content and event.content.parts:
                return event.content.parts[0].text
    except Exception as e:  # last line of defence: one bad request must not take down the app
        print(f"  [{user_id}] run failed: {type(e).__name__}: {e}")
        return "Sorry, something went wrong. Please try again."
    return "(no answer)"


async def main():
    print("Alice:", await ask("alice", "Remember: my favourite number is 7. What is 7 * 6?"))
    print("Bob:  ", await ask("bob", "What is my favourite number?"))
    print("Bob:  ", await ask("bob", "Use the calculator to compute 10 / 0."))
    print("Bob:  ", await ask("bob", "Use the calculator on: __import__('os').getcwd()"))


if __name__ == "__main__":
    asyncio.run(main())
