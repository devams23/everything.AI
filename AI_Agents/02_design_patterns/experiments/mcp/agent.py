"""Phase 2 - MCP: connect an agent to an EXISTING MCP server (no tool code written by us).

    our agent  --(MCP protocol over stdio)-->  filesystem MCP server (Node, started via npx)
                                                  -> tools: list_directory, read_text_file, ...

Before: we wrote every tool as a Python function. With MCP, someone else's server provides the
tools; ADK asks it "what tools do you have?" and hands their schemas to the model, the same as ours.

Guardrails:
  1. The server may only see ONE folder (the path we pass when starting it).
  2. tool_filter: we expose only READ tools, so no write/edit/move, even though the server has them.
  3. Loop limits from Phase 1: max LLM calls + an overall timeout.

Needs: Node.js (npx).  Run:  python agent.py
"""
import asyncio
import os
import shutil
import uuid
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

load_dotenv(find_dotenv())

MODEL = os.getenv("MODEL", "gemini-3.5-flash-lite")
APP_NAME = "notes_reader"
NOTES_DIR = Path(__file__).resolve().parents[2]  # AI_Agents/02_design_patterns
READ_ONLY_TOOLS = ["list_directory", "directory_tree", "read_text_file", "search_files"]

# --- The MCP connection: start the server as a subprocess, talk to it over stdin/stdout ---
notes_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=shutil.which("npx") or "npx",  # on Windows this resolves to npx.cmd
            args=["-y", "@modelcontextprotocol/server-filesystem", str(NOTES_DIR)],
        ),
        timeout=60,  # first run downloads the server package, so give it time
    ),
    tool_filter=READ_ONLY_TOOLS,  # guardrail 2: capability, not trust
)

agent = Agent(
    name="notes_reader",
    model=MODEL,
    instruction=(
        f"You answer questions about the learning notes in {NOTES_DIR}. "
        "Use the file tools to find and read the files; never guess their contents. "
        "Mention which file each point comes from."
    ),
    tools=[notes_tools],  # a whole server's tools, plugged in like one tool list
)

QUESTION = (
    "Read the README.md inside each folder under experiments/. For each pattern give one line: "
    "the pattern, when to use it, and its most important finding."
)


async def main():
    try:
        # MCP discovery: ask the server which tools it offers (after our filter)
        tools = await notes_tools.get_tools()
        print("Tools from the MCP server:", [t.name for t in tools])

        session_service = InMemorySessionService()
        session_id = str(uuid.uuid4())
        await session_service.create_session(app_name=APP_NAME, user_id="devam", session_id=session_id)
        runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
        message = types.Content(role="user", parts=[types.Part(text=QUESTION)])

        answer = ""
        async with asyncio.timeout(120):  # guardrail 3: the whole question
            async for event in runner.run_async(
                user_id="devam", session_id=session_id, new_message=message,
                run_config=RunConfig(max_llm_calls=15),  # guardrail 3: max loop steps
            ):
                for call in event.get_function_calls():
                    print(f"  MCP call: {call.name}({call.args})")
                if event.is_final_response() and event.content and event.content.parts:
                    answer = event.content.parts[0].text or ""
        print("\n" + answer)
    except TimeoutError:
        print("Stopped: took longer than 120s.")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    finally:
        await notes_tools.close()  # stop the server subprocess


if __name__ == "__main__":
    asyncio.run(main())
