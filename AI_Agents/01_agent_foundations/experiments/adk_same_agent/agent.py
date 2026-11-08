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
from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Finds the nearest .env, starting in this folder and walking up (so AI_Agents/.env also works).
load_dotenv(find_dotenv())

MODEL = os.getenv("MODEL", "gemini-3.5-flash-lite")
APP_NAME = "calc_app"

# --- Loop limits (3 layers against infinite loops) ---------------------------
MAX_LLM_CALLS = 8        # layer 1: total model calls per question (ADK enforces it)
MAX_CALLS_PER_TOOL = 3   # layer 2: same tool over and over = probably stuck (our callback)
TIMEOUT_SECONDS = 30     # layer 3: wall-clock cap, whatever the reason

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


# --- Callbacks: hooks ADK runs around every tool call ------------------------
# This is "where the tool is called": ADK runs before_tool -> YOUR FUNCTION -> after_tool.
# Same spot as `result = TOOLS[call.name](**call.args)` in raw_loop.

def before_tool(tool, args, tool_context):
    # "temp:" state lives only for the current question, so the count resets each time.
    key = f"temp:calls_{tool.name}"
    count = tool_context.state.get(key, 0) + 1
    tool_context.state[key] = count
    print(f"    -> before_tool: about to run {tool.name}({args})  [call #{count}]")
    if count > MAX_CALLS_PER_TOOL:
        # Returning a dict SKIPS the real tool; the model gets this instead.
        return {"status": "error",
                "error_message": f"{tool.name} called too many times. Stop and answer with what you have."}
    return None  # None = go ahead and run the real tool


def after_tool(tool, args, tool_context, tool_response):
    print(f"    <- after_tool:  {tool.name} returned {tool_response}")
    return None  # None = keep the tool's response unchanged


root_agent = Agent(
    name="calc_agent",
    model=MODEL,
    instruction=(
        "You are a helpful assistant. Use the tools for math and time. "
        "If a tool returns status 'error', explain the problem to the user "
        "or fix the input and try again."
    ),
    tools=[calculator, current_time],
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
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
        async with asyncio.timeout(TIMEOUT_SECONDS):  # layer 3
            # run_async IS the loop from raw_loop. Each event = one step of it.
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message,
                run_config=RunConfig(max_llm_calls=MAX_LLM_CALLS),  # layer 1
            ):
                for call in event.get_function_calls():
                    print(f"  [{user_id}] model asked for: {call.name}({call.args})")
                if event.is_final_response() and event.content and event.content.parts:
                    return event.content.parts[0].text
    except TimeoutError:
        return f"Sorry, that took longer than {TIMEOUT_SECONDS}s, so I stopped."
    except Exception as e:  # last line of defence (also catches the max_llm_calls limit)
        print(f"  [{user_id}] run failed: {type(e).__name__}: {e}")
        return "Sorry, something went wrong. Please try again."
    return "(no answer)"


async def main():
    print("Alice:", await ask("alice", "Remember: my favourite number is 7. What is 7 * 6?"))
    print("Bob:  ", await ask("bob", "What is my favourite number?"))
    print("Bob:  ", await ask("bob", "Use the calculator to compute 10 / 0."))
    print("Bob:  ", await ask("bob", "Use the calculator on: __import__('os').getcwd()"))
    # Loop test: invites the model to call the tool many times -> should hit MAX_CALLS_PER_TOOL.
    print("Bob:  ", await ask("bob", "Compute 1+1, then 2+2, then 3+3, then 4+4, then 5+5, each with a separate calculator call."))


if __name__ == "__main__":
    asyncio.run(main())
